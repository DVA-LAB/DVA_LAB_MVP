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
    """
        SAM을 이용하여 COCO 형식의 BBox 레이블을 객체에 더 fit하게 세그먼트 마스크로 세밀화하는 함수입니다.

        이 API는 주어진 이미지 경로와 JSON 파일을 사용하여 BBox 레이블을 개선합니다. 개선된 데이터는 세그먼트 마스크로서 더 정확하게 객체를 표현합니다.

        Args:
            - request_body (DataRequest): 요청 본문, 아래의 필드를 포함합니다.
                - img_path (str): 세그먼트 마스크를 적용할 이미지의 경로입니다.
                - json_file (str): COCO 형식의 BBox 레이블이 포함된 JSON 파일의 경로입니다.

        Returns:
            - updated_data (json): 세그먼트 마스크로 세밀화된 레이블이 포함된 JSON 데이터입니다.
    """

    refiner = Refiner("cuda")

    imgs_path = request_body.img_path
    json_path = request_body.json_file

    updated_data = refiner.do_refine(json_path, imgs_path)
    return updated_data


@router.post(
    "/ship_size",
    status_code=status.HTTP_200_OK,
    summary="check ship size with SAM",
)
async def inference(request_body: ShipRequest):
    """
        SAM 모델 추론 결과를 기반으로 선박의 크기를 계산할 수 있는 정보를 반환합니다.

        Args
            - request_body
                - request_body.user_input (str): 사용자 입력이 담긴 파일 경로
                - request_body.frame_path (str): 원본 프레임 경로
                - request_body.tracking_result (str): 객체 추적 결과 bbox 파일 경로

        Return
            - ships_info (list): N x [frame_no, point[0][0], point[0][1], point[1][0], point[1][0]]
    """

    refiner = Refiner("cuda", fastsam=True)
    # refiner = Refiner("cuda")

    # TODO@jh: user가 여러대의 선박에 대한 입력을 저장할 경우 처리 필요
    user_frame_no, mean_x, mean_y = check_user_input(request_body.user_input)

    # TODO@jh: user_input이 올바르게 저장되어 있지 않아서 임의로 가장 가까운 5의 배수로 수정함 -> 주석처리함
    # user_frame_no = round(user_frame_no / 5) * 5

    frames = glob.glob(os.path.join(request_body.frame_path, "*.jpg"))
    tracking_result = request_body.tracking_result
    objs = read_file(
        tracking_result
    )  # frame_number, track_id, class_id, x, y, w, h, -1,-1,-1
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
            try:
                frame_no = result[0]
                # TODO@jh: 서버에 저장된 tracking 결과가 5의 배수로 inference한 결과가 아니라서 별도 처리함 (추후 수정 필요)
                # TODO@jh: 매번 찾지 않고, 네이밍 규칙으로 읽도록 수정 필요
                frame = [
                    x for x in frames if frame_no == int(x.split("_")[-1].split(".")[0])
                ][0]
                bbox_xyxy = refiner.convert_to_xyxy(result[3:7])
                mask = refiner._do_seg(cv2.imread(frame), [bbox_xyxy])
                _, _, point = refiner.find_rotated_bounding_box_and_max_length(mask)
                ships_info.append(
                    [frame_no, point[0][0], point[0][1], point[1][0], point[1][1]] # 마지막은 point[1][1]이 되어야 하는 것이 아닌지 재검증 필요 (By HE)
                )
            except Exception as e:
                # TODO@jh: 이미지가 읽히지 않는 프레임이 있는 것 같음. 추후 확인 필요
                print(e)
    ships_info = [list(map(int, sublist)) for sublist in ships_info]

    return ships_info


def read_csv_file(file_path):
    """
        탐지 결과 bbox csv 파일을 읽고 그 bbox를 리스트로 변환하여 반환합니다.

        Args
            - file_path (str): 탐지 결과 csv 파일 경로

        Return
            - detections (list): bbox 리스트
    """

    detections = []
    with open(file_path, "r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            detections.append([float(x) for x in row])

    return detections


def read_file(file_path):
    """
        탐지 결과 bbox 파일을 읽고 그 bbox를 리스트로 변환하여 반환합니다.

        Args
            - file_path (str): 탐지 결과 파일 경로

        Return
            - detections (list): bbox 리스트
    """

    with open(file_path, "r") as file:
        lines = file.readlines()
    detections = [[float(x) for x in line.strip().split(",")] for line in lines]

    return detections


def is_point_in_bbox(x, y, bbox):
    """
        한 점이 bbox안에 있는지 여부를 반환합니다.

        Args
            - x (float): 점의 x 좌표
            - y (float): 점의 y 좌표
            - bbox (list): bbox 정보

        Return
            - True or False (bool)
    """

    xmin, ymin, w, h = bbox
    xmax = xmin + w
    ymax = ymin + h

    return xmin <= x <= xmax and ymin <= y <= ymax


def check_user_input(input_path):
    """
        유저 입력에 포함된 두 점의 x좌표의 평균과 y좌표의 평균을 계산합니다.

        Args
            - input_path (str): 유저 입력 파일 경로
        
        Return
            - frame_number (int): 프레임 번호
            - mean_x (float): 두 점의 x좌표의 평균
            - mean_y (float): 두 점의 y좌표의 평균
    """

    # TODO@jh: user input이 복수개일때 확인 필요
    with open(input_path, "r") as f:
        ship_coord = f.read()
    frame_number, x1, y1, x2, y2, distance = ship_coord.split(" ")
    x1, y1, x2, y2 = map(float, [x1, y1, x2, y2])
    mean_x = (x1 + x2) / 2
    mean_y = (y1 + y2) / 2

    return int(frame_number), mean_x, mean_y


def visualize_points(image_path, points, output_path):
    """
        점 정보가 주어졌을 때 원본 프레임에 해당 점을 중심으로하는 동심원을 그립니다.

        Args
            - image_path (str): 원본 프레임 경로
            - points (list): 점 정보 [x, y, w, h]
            - output_path (str): 시각화를 적용한 프레임의 저장 경로
    """

    image = cv2.imread(image_path)
    for point in points:
        cv2.circle(image, point, radius=5, color=(0, 0, 255), thickness=-1)
    cv2.imwrite(output_path, image)
