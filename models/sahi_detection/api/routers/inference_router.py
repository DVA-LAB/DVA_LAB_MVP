from fastapi import APIRouter, Depends, status, Request
import argparse
import os
import os.path as osp
import cv2
import csv
import time
import torch
import numpy as np

from loguru import logger
from interface.request import SahiRequest
from typing import List

from api.services import preproc
from api.services import get_exp
from api.services import fuse_model, get_model_info, postprocess
from api.services import plot_tracking
from api.services import Timer
from api.services import YoloxDetectionModel
from api.services import get_sliced_prediction
from api.services import AutoDetectionModel
from api.services import config as cfg

IMAGE_EXT = [".jpg", ".jpeg", ".webp", ".bmp", ".png"]


def make_parser():
    """
        객체추적에 사용할 사용자 옵션을 반환합니다.

        Return:
            - parser (argparse.ArgumentParser)
    """

    parser = argparse.ArgumentParser("ByteTrack")
    parser.add_argument("--demo", default="image", help="demo type, eg. image, video and webcam")
    parser.add_argument("--model", default="yolov8", help="Model name | yolov5, yolox, yolov8")
    parser.add_argument("-expn", "--experiment-name", type=str, default=None)
    parser.add_argument("-n", "--name", type=str, default=None, help="model name")
    parser.add_argument("--path", default="/home/dva3/workspace/output/test/test01", help="path to images or video")
    parser.add_argument("--camid", type=int, default=0, help="webcam demo camera id")
    parser.add_argument("--save_result", action="store_true", help="whether to save the inference result of image/video")

    # exp file
    parser.add_argument("-f", "--exp_file", default=None, type=str, help="If you want to use yolox, pls input your expriment description file")
    parser.add_argument("-c", "--ckpt", default="/mnt/models/v8_m_best.pt", type=str, help="ckpt for inf")
    parser.add_argument("--device", default="gpu", type=str, help="device to run our model, can either be cpu or gpu")
    parser.add_argument("--conf", default=None, type=float, help="test conf")
    parser.add_argument("--nms", default=None, type=float, help="test nms threshold")
    parser.add_argument("--tsize", default=None, type=int, help="test img size")
    parser.add_argument("--fps", default=5, type=int, help="frame rate (fps)")
    parser.add_argument("--fp16", dest="fp16", default=False, action="store_true", help="Adopting mix precision evaluating.")
    parser.add_argument("--fuse", dest="fuse", default=False, action="store_true", help="Fuse conv and bn for testing.")

    return parser


def get_image_list(path):
    """
        특정 확장자를 가진 이미지 파일의 경로 목록을 반환합니다.

        Args:
            - path (str): 하위 디렉터리를 탐색할 디렉터리 경로
    
        Return:
            - image_names (list): 파일 경로 리스트를 반환합니다.
    """

    image_names = []
    for maindir, subdir, file_name_list in os.walk(path):
        for filename in file_name_list:
            apath = osp.join(maindir, filename)
            ext = osp.splitext(apath)[1]
            if ext in IMAGE_EXT:
                image_names.append(apath)

    return image_names

class Predictor(object):
    """
        SAHI와 Pretraiend YOLO 모델 기반 객체탐지를 수행합니다.

    """
    def __init__(self, det_model, cls_map, sliced_path, device=torch.device("cuda:0"), fp16=False, args = None):
        self.det_model = det_model
        self.cls_map = cls_map
        self.sliced_path = sliced_path
        self.device = device
        self.fp16 = fp16
        self.args = args
        
        self.rgb_means = (0.485, 0.456, 0.406)
        self.std = (0.229, 0.224, 0.225)

    def inference(self, img, frame_id):
        """
            실질적으로 SAHI를 적용하고 객체탐지를 수행합니다.

            Args:
                - img (str) or (np.array): 이미지 경로 또는 이미지를 읽은 넘파이 배열입니다.
                - frame_id (int): 프레임 번호입니다.

            Return:
                det_outputs (list): 객체 탐지 결과 bbox입니다.
        """

        img_info = {"id": frame_id}
        img_path = img
        if isinstance(img, str):
            img_info["file_name"] = osp.basename(img)
            img = cv2.imread(img)
        else:
            img_info["file_name"] = None

        height, width = img.shape[:2]
        img_info["height"] = height
        img_info["width"] = width
        img_info["raw_img"] = img
        
        if self.sliced_path != None:
            logger.info("in here")
            file_name_without_extension, _ = os.path.splitext(os.path.basename(img_path))
            result = get_sliced_prediction(img_path, self.det_model, slice_height=1024, slice_width=1024, output_file_name=file_name_without_extension, interim_dir = self.sliced_path)
        else:
            result = get_sliced_prediction(img_path, self.det_model, slice_height=1024, slice_width=1024)
        
        det_outputs = []
        for ann in result.to_coco_annotations():
            bbox = ann['bbox']
            if self.args.model == "yolox":
                conf = ann['score'].item()
            else:    
                conf = ann['score']
            label = ann['category_id']

            if bbox[0] < 0:
                bbox[0] = 0.0
            if bbox[1] < 0:
                bbox[1] = 0.0
            if bbox[2] > width:
                bbox[2] = float(width)
            if bbox[3] > height:
                bbox[3] = float(height)

            # output : [x1, y1, x2, y2, conf, label]
            if label in self.cls_map.keys():
                det_outputs.append([frame_id, self.cls_map[label], bbox[0], bbox[1], bbox[2], bbox[3], conf])
        return det_outputs

def image_demo(predictor, current_time, args):
    """
        이미지 파일에 대한 모델 인퍼런스 수행결과를 반환합니다.

        Args:
            - predictor (Predictor): 인퍼런스를 수행할 모델 객체
            - current_time (time.localtime): 현재 시간
            - args (argparse.ArgumentParser)

        Return:
            - det_results (list): 객체 탐지 결과 bbox입니다.   
    """

    if osp.isdir(args.path):
        files = get_image_list(args.path)
    else:
        files = [args.path]
    files.sort()
    timer = Timer()
    det_results = []
    for frame_id, img_path in enumerate(files, 1):
        det_outputs = predictor.inference(img_path, frame_id)
        det_results+=det_outputs

        if frame_id % 20 == 0:
            logger.info('Processing frame {} ({:.2f} fps)'.format(frame_id, 1. / max(1e-5, timer.average_time)))
    
    return det_results

def write_csv(csv_file_path, det_results):
    """
        객체탐지 결과를 csv 파일로 저장합니다.

        Args:
            - csv_file_path (str): 객체탐지 결과를 저장할 파일명입니다.
            - det_results (list): 객체탐지 결과가 담긴 bbox 정보입니다.
    """

    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in det_results:
            writer.writerow(row)

    print(f"데이터가 {csv_file_path}에 저장되었습니다.")


def main(img_path=None, csv_path=None, sliced_path = None):
    """
        SAHI + 객체탐지를 수행하고 그 결과를 csv 파일로 생성합니다.

        Args:
            - img_path (str): SAHI가 적용된 객체탐지를 수행할 원본 프레임이 위치하는 디렉터리 경로입니다.
            - csv_path (str): SAHI가 적용된 객체탐지 결과를 저장할 csv 파일 이름입니다.
            - sliced_path (str): SAHI에 의해 슬라이싱 된 패치가 저장된 디렉터리 경로입니다.
    """

    args = make_parser().parse_args()

    args.device = torch.device("cuda" if args.device == "gpu" else "cpu")
    # 임시로 args 유지할 때까지만 사용
    if img_path != None:
        args.path = img_path

    if csv_path == None:
        csv_path = "./example.csv"

    logger.info("Args: {}".format(args))
    logger.info("Selected Model: ", args.model)

    if args.model == "yolox":
        exp = get_exp(args.exp_file, args.name)

        if not args.experiment_name:
            args.experiment_name = exp.exp_name

        if args.conf is not None:
            exp.test_conf = args.conf
        if args.nms is not None:
            exp.nmsthre = args.nms
        if args.tsize is not None:
            exp.test_size = (args.tsize, args.tsize)

    # Model define
    if args.model == 'yolov5':
        detection_model = AutoDetectionModel.from_pretrained(
        model_type='yolov5',
        confidence_threshold=0.3,
        image_size = 1024,
        model_path = args.ckpt ,
        device='cuda:0', # or 'cpu'
        )
    elif args.model == 'yolov8':
        detection_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        confidence_threshold=0.3,
        image_size = 1024,
        model_path= args.ckpt,
        device='cuda:0', # or 'cpu'
        )

    cls_map = {}
    # det 모델과 anomaly 모델 머지 input class를 맞춰주기 위함
    for idx, cls in enumerate(cfg.OUT_CLASSES):
        m_cls_idx = cfg.CLASSES.index(cls)
        cls_map[m_cls_idx] = idx
    
    logger.info("sliced_path//////////////////", sliced_path)
    predictor = Predictor(detection_model, cls_map, sliced_path, args.device, args.fp16, args)

    current_time = time.localtime()
    if args.demo == "image":
        det_results = image_demo(predictor, current_time, args)
        write_csv(csv_path, det_results)
    else:
        logger.exception("Please check input format")


router = APIRouter(tags=["sahi"])

@router.post(
    "/sahi/inference",
    status_code=status.HTTP_200_OK,
    summary="detection inference",
)
async def inference(request: SahiRequest.SahiRequest):
    """
        SAHI가 적용된 객체탐지를 수행하고 그 결과를 반환합니다.

        Args:
            - request
                - request.img_path (str): SAHI가 적용된 객체탐지를 수행할 원본 프레임이 위치하는 디렉터리 경로입니다.
                - request.csv_path (str): SAHI가 적용된 객체탐지 결과를 저장할 csv 파일 이름입니다.
                - request.sliced_path (str): SAHI에 의해 슬라이싱 된 패치가 저장된 디렉터리 경로입니다.

        Return:
            - img_path (str): SAHI가 적용된 객체탐지를 수행할 원본 프레임이 위치하는 디렉터리 경로입니다.
            - csv_path (str): SAHI가 적용된 객체탐지 결과를 저장할 csv 파일 이름입니다.
            - sliced_path (str): SAHI에 의해 슬라이싱 된 패치가 저장된 디렉터리 경로입니다.
    """

    img_path = request.img_path
    csv_path = request.csv_path
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    sliced_path = request.sliced_path

    main(img_path, csv_path, sliced_path)
    return img_path, csv_path, sliced_path