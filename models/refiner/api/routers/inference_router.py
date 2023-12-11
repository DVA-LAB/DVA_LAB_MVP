import cv2
import numpy as np
from fastapi import APIRouter, Depends, status

from api.services import Refiner
from interface.request import DataRequest, ShipRequest
import csv
import os
import glob
import cv2
import numpy as np

router = APIRouter(tags=["data"])


@router.post(
    "/refinement",
    status_code=status.HTTP_200_OK,
    summary="bbox refinement with SAM",
)
async def inference(request_body: DataRequest):
    refiner = Refiner("cuda")

    imgs_path = request_body.img_path
    json_path = request_body.json_file

    updated_data = refiner.do_refine(json_path, imgs_path)
    # refiner.save_update(updated_data, "refined_train.json")
    return updated_data


@router.post(
    "/check_size",
    status_code=status.HTTP_200_OK,
    summary="check ship size with SAM",)
async def inference(request_body: ShipRequest):
    refiner = Refiner("cuda")

    user_frame_no, mean_x, mean_y = check_user_input(request_body.user_input)
    frames = glob.glob(os.path.join(request_body.frame_path, '*.jpg'))

    tracking_result = request_body.tracking_result
    objs = read_file(tracking_result)
    ship_id = [x for x in objs if (int(x[0]) == int(user_frame_no)) and (int(x[2])==1) and (is_point_in_bbox(mean_x, mean_y, x[3:7]))]

    if len(ship_id):
        target_results = [x for x in objs if int(x[1]) == int(ship_id[0])]
        for idx, result in enumerate(target_results):
            frame_no = result[0]
            # TODO@jh: 매번 찾지 않고, 네이밍 규칙으로 읽도록 수정
            frame = [x for x in frames if int(1) == int(x.split('_')[-1].split('.')[0])][0]
            class_id = result[2]
            bbox_xyxy = refiner.convert_to_xyxy(result[3:7])
            mask = refiner._do_seg(frame, bbox_xyxy)
            ship_size = refiner.calculate_length_along_major_axis(mask)
            # TODO@jh: ship size 로 BEV_1 endpoint 활용하여 GSD 계산

def read_csv_file(file_path):
    detections = []
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            detections.append([float(x) for x in row])
    return detections

def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    detections = [[float(x) for x in line.strip().split(',')] for line in lines]
    return detections

def is_point_in_bbox(x, y, bbox):
    xmin, ymin, w, h = bbox
    xmax = xmin + w
    ymax = ymin + h
    return xmin <= x <= xmax and ymin <= y <= ymax

def check_user_input(input_path):
    user_input = [x for x in os.listdir(input_path) if x.endswith('.txt')][0]
    user_frame_no = os.path.splitext(user_input)[0]
    with open(os.path.join(input_path, user_input), 'r') as f:
        ship_coord = f.read()
    x1, y1, x2, y2 = map(float, ship_coord.split(' ')[0:4])
    mean_x = (x1 + x2) / 2
    mean_y = (y1 + y2) / 2
    return user_frame_no, mean_x, mean_y


