from fastapi import APIRouter, Depends, status, Request

import argparse
import os
import os.path as osp
import time
import cv2
import torch

from loguru import logger

from api.services import preproc
from api.services import get_exp
from api.services import fuse_model, get_model_info, postprocess
from api.services import plot_tracking
from api.services import Timer

from api.services import YoloxDetectionModel
from api.services import get_sliced_prediction
from api.services import AutoDetectionModel

from api.services import config as cfg

from interface.request import SahiRequest

import numpy as np
import csv

from typing import List


IMAGE_EXT = [".jpg", ".jpeg", ".webp", ".bmp", ".png"]


def make_parser():
    parser = argparse.ArgumentParser("ByteTrack")
    parser.add_argument(
        "--demo", default="image", help="demo type, eg. image, video and webcam"
    )
    parser.add_argument(
        "--model", default="yolov5", help="Model name | yolov5, yolox, yolov8"
    )
    parser.add_argument("-expn", "--experiment-name", type=str, default=None)
    parser.add_argument("-n", "--name", type=str, default=None, help="model name")

    parser.add_argument(
        "--path", default="/home/dva3/workspace/output/test/test01", help="path to images or video"
    )
    parser.add_argument("--camid", type=int, default=0, help="webcam demo camera id")
    parser.add_argument(
        "--save_result",
        action="store_true",
        help="whether to save the inference result of image/video",
    )

    # exp file
    parser.add_argument(
        "-f",
        "--exp_file",
        default=None,
        type=str,
        help="If you want to use yolox, pls input your expriment description file",
    )
    parser.add_argument("-c", "--ckpt", default="/mnt/models/best_1203.pt", type=str, help="ckpt for eval")
    parser.add_argument(
        "--device",
        default="gpu",
        type=str,
        help="device to run our model, can either be cpu or gpu",
    )
    parser.add_argument("--conf", default=None, type=float, help="test conf")
    parser.add_argument("--nms", default=None, type=float, help="test nms threshold")
    parser.add_argument("--tsize", default=None, type=int, help="test img size")
    # parser.add_argument("--fps", default=30, type=int, help="frame rate (fps)")
    parser.add_argument(
        "--fp16",
        dest="fp16",
        default=False,
        action="store_true",
        help="Adopting mix precision evaluating.",
    )
    parser.add_argument(
        "--fuse",
        dest="fuse",
        default=False,
        action="store_true",
        help="Fuse conv and bn for testing.",
    )

    return parser


def get_image_list(path):
    image_names = []
    for maindir, subdir, file_name_list in os.walk(path):
        for filename in file_name_list:
            apath = osp.join(maindir, filename)
            ext = osp.splitext(apath)[1]
            if ext in IMAGE_EXT:
                image_names.append(apath)
    return image_names

class Predictor(object):
    def __init__(
        self,
        det_model,
        cls_map,
        device=torch.device("cuda:0"),
        fp16=False,
        args = None
    ):
        self.det_model = det_model
        self.cls_map = cls_map
        self.device = device
        self.fp16 = fp16
        self.args = args
        
        self.rgb_means = (0.485, 0.456, 0.406)
        self.std = (0.229, 0.224, 0.225)

    def inference(self, img, frame_id):
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
        
        file_name_without_extension, _ = os.path.splitext(os.path.basename(img_path))
        result = get_sliced_prediction(img_path, self.det_model, slice_height=1024, slice_width=1024, output_file_name=file_name_without_extension)
    
        det_outputs = []
        for ann in result.to_coco_annotations():
            bbox = ann['bbox']
            if self.args.model == "yolox":
                conf = ann['score'].item()
            else:    
                conf = ann['score']
            label = ann['category_id']
            # output : [x1, y1, x2, y2, conf, label]
            if label in self.cls_map.keys():
                det_outputs.append([frame_id, self.cls_map[label], bbox[0], bbox[1], bbox[2], bbox[3], conf])
        return det_outputs

def image_demo(predictor, current_time, args):
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
    # CSV 파일 경로
    # csv_file_path = "./example.csv"
    
    # CSV 파일에 데이터 쓰기
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in det_results:
            writer.writerow(row)

    print(f"데이터가 {csv_file_path}에 저장되었습니다.")


def main(img_path=None, csv_path=None):
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
    elif args.model == 'yolox':
        # yolox 는 class에 백그라운드를 포함하지 않음
        classes = ('dolphin','boat')
        # detection_model = YoloxDetectionModel(
        #     config_path = args.exp_file,
        #     device="cpu",
        #     confidence_threshold=0.3,
        #     nms_threshold=0.4,
        #     image_size = (640,640),
        #     model_path=args.ckpt,
        #     classes=classes
        # )

    cls_map = {}
    # det 모델과 anomaly 모델 머지 input class를 맞춰주기 위함
    for idx, cls in enumerate(cfg.OUT_CLASSES):
        m_cls_idx = cfg.CLASSES.index(cls)
        cls_map[m_cls_idx] = idx

    predictor = Predictor(detection_model, cls_map, args.device, args.fp16, args)

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
async def inference(request: Request):
    data = await request.json()
    img_path = data.get("img_path")
    csv_path = data.get("csv_path")
    print(img_path,csv_path)
    main(img_path, csv_path)
    return