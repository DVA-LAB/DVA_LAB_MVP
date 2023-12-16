import csv
import glob
import json
import os

import cv2
import numpy as np
import requests
from fastapi import APIRouter, Depends, status

from api.services import Refiner
from interface.request import DataRequest, ShipRequest

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
    "/ship_size",
    status_code=status.HTTP_200_OK,
    summary="check ship size with SAM",
)
async def inference(request_body: ShipRequest):
    refiner = Refiner("cuda")

    # TODO@jh: user가 여러대의 선박에 대한 입력을 저장할 경우 처리 필요
    user_frame_no, mean_x, mean_y = check_user_input(request_body.user_input)

    # TODO@jh: user_input이 올바르게 저장되어 있지 않아서 임의로 가장 가까운 5의 배수로 수정함
    user_frame_no = round(user_frame_no / 5) * 5

    frames = glob.glob(os.path.join(request_body.frame_path, "*.jpg"))
    tracking_result = request_body.tracking_result
    objs = read_file(tracking_result)  # frame_number, track_id, class_id, x, y, w, h, -1,-1,-1
    ship_id = [
        x[1]
        for x in objs
        if (int(x[0]) == int(user_frame_no))
        and (int(x[2]) == 1)
        and (is_point_in_bbox(mean_x, mean_y, x[3:7]))
    ]

    ships_info = []
    if len(ship_id):
        target_results = [x for x in objs if int(x[1]) == int(ship_id[0])]
        for idx, result in enumerate(target_results):
            frame_no = result[0]

            # TODO@jh: 서버에 저장된 tracking 결과가 5의 배수로 inference한 결과가 아니라서 별도 처리함 (추후 수정 필요)
            if frame_no % 5 != 0:
                continue
            # TODO@jh: 매번 찾지 않고, 네이밍 규칙으로 읽도록 수정 필요
            frame = [
                x for x in frames if frame_no == int(x.split("_")[-1].split(".")[0])
            ][0]
            bbox_xyxy = refiner.convert_to_xyxy(result[3:7])
            mask = refiner._do_seg(cv2.imread(frame), [bbox_xyxy])
            _, _, point = refiner.find_rotated_bounding_box_and_max_length(mask)
            ships_info.append([frame_no, point[0][0], point[0][1], point[1][0], point[1][0]])
    ships_info = [list(map(int, sublist)) for sublist in ships_info]
    return ships_info


def read_csv_file(file_path):
    detections = []
    with open(file_path, "r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            detections.append([float(x) for x in row])
    return detections


def read_file(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    detections = [[float(x) for x in line.strip().split(",")] for line in lines]
    return detections


def is_point_in_bbox(x, y, bbox):
    xmin, ymin, w, h = bbox
    xmax = xmin + w
    ymax = ymin + h
    return xmin <= x <= xmax and ymin <= y <= ymax


def check_user_input(input_path):
    # TODO@jh: user input이 복수개일때 확인 필요
    with open(input_path, "r") as f:
        ship_coord = f.read()
    frame_number, x1, y1, x2, y2, distance = ship_coord.split(" ")
    x1, y1, x2, y2 = map(float, [x1, y1, x2, y2])
    mean_x = (x1 + x2) / 2
    mean_y = (y1 + y2) / 2
    return int(frame_number), mean_x, mean_y


def visualize_points(image_path, points, output_path):
    image = cv2.imread(image_path)
    for point in points:
        cv2.circle(image, point, radius=5, color=(0, 0, 255), thickness=-1)
    cv2.imwrite(output_path, image)