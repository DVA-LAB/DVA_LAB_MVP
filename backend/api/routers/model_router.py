import glob
import json
import os

import requests
from autologging import logged
from fastapi import APIRouter, Depends, HTTPException, status
from interface.request import ModelRequest
from utils.merge_bboxes import (match_and_ensemble, plot_detections,
                                read_csv_file, read_file)

router = APIRouter(tags=["model"])


@router.post(
    "/inference",
    status_code=status.HTTP_200_OK,
    summary="AI model run",
)
async def model_inference(body: ModelRequest):
    try:
        # # Detection
        # img_path, csv_path, sliced_path = inference_detection(
        #     body.frame_path, body.detection_save_path, body.sliced_path
        # )
        #
        # # if use_segment=True:
        # #     # TODO@jh: check segment service
        # #     for frame in glob.glob(os.path.join(body.frame_path, "*.jpg")):
        # #         frame_path, slices_path, output_path = inference_segmentation(
        # #             frame, body.sliced_path, output_path
        # #         )
        #
        # # Bbox merge
        # os.makedirs(body.output_merge_path, exist_ok=True)
        # # delete_files_in_folder(body.output_merge_path)
        # anomaly_detection_output = read_csv_file(csv_path)
        # detection_output = read_csv_file(csv_path)
        # detection_save_path = os.path.join(body.output_merge_path, "result.txt")
        # output = match_and_ensemble(
        #     anomaly_detection_output,
        #     detection_output,
        #     use_anomaly=True,
        #     output_file=detection_save_path,
        # )
        # # TODO@jh: change to plt save function
        # # plot_detections(anomaly_detection_output, detection_output, output)
        #
        # # Tracking
        # tracking_save_path = os.path.join("test", "model", "tracking", "result.txt")
        # os.makedirs(os.path.dirname(tracking_save_path), exist_ok=True)
        # # delete_files_in_folder(os.path.dirname(tracking_save_path))
        # result_path = inference_tracking(detection_save_path, tracking_save_path)
        # return result_path
        return "for test"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/inference/detection",
    status_code=status.HTTP_200_OK,
    summary="sahi + yolo inference",
    description="""\
이 엔드포인트는 Sahi와 YOLO 모델을 사용하여 객체 탐지를 수행합니다. \
사용자가 제공한 원본 프레임 경로(`img_path`), 결과를 저장할 경로(`csv_path`), \
그리고 inference과정에서 생성한 이미지 패치를 저장할 경로(`sliced_path`)를 입력 받습니다.

### 예시
- `img_path`: /home/dva4/DVA_LAB/backend/test/frame_origin
- `csv_path`: /home/dva4/DVA_LAB/backend/test/model/detection/result.csv
- `sliced_path`: /home/dva4/DVA_LAB/backend/test/model/sliced
""",
)
async def inference_detection(img_path, csv_path, sliced_path):
    url = "http://localhost:8002/sahi/inference"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {"img_path": img_path, "csv_path": csv_path, "sliced_path": sliced_path}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error in external API: {response.text}",
        )

    return response.json()


@router.post(
    "/inference/segmentation",
    status_code=status.HTTP_200_OK,
    summary="anomaly segmentation",
    description="""\
이 엔드포인트는 anomaly 탐지 모델을 사용하여 segmentation mask를 생성합니다. \
사용자가 제공한 원본 프레임 경로(`img_path`), 프레임을 나누어 저장한 이미지 패치 경로(`sliced_path`), \
그리고 결과를 저장할 경로(`output_path`)를 입력 받습니다.

### 예시
- `frame_path`: /home/dva4/DVA_LAB/backend/test/frame_origin/DJI_0119_30_00000.jpg
- `slices_path`: /home/dva4/DVA_LAB/backend/test/model/sliced
- `output_path`: /home/dva4/DVA_LAB/backend/test/model/segment/DJI_0119_30_00000.jpg
""",
)
async def inference_segmentation(frame_path, slices_path, output_path):
    url = "http://localhost:8003/anomaly/inference"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {
        "frame_path": frame_path,
        "slices_path": slices_path,
        "output_path": output_path,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error in external API: {response.text}",
        )

    return response.json()


@router.post(
    "/inference/merge",
    status_code=status.HTTP_200_OK,
    summary="detection - segmentation bbox merge",
    description="""\
이 엔드포인트는 detection과 segmentation 모델에서 나온 bbox 결과를 병합 합니다. \
객체 탐지 결과 csv_path (`csv_path`)와 segmentation bbox 결과 (`anomaly_detection_output`) \
그리고 병합한 결과를 저장할 (`output_merge_path`)를 입력 받습니다..

### 예시
- `output_merge_path`: /home/dva4/DVA_LAB/backend/test/model/merged
- `csv_path`: /home/dva4/DVA_LAB/backend/test/model/detection/result.csv
- `anomaly_detection_output`: /home/dva4/DVA_LAB/backend/test/model/detection/result.csv -> 임시로 detection csv를 받게 함
""",
)
async def inference_merge(
    output_merge_path, csv_path, anomaly_detection_output, use_anomaly: bool = True
):
    try:
        os.makedirs(output_merge_path, exist_ok=True)
        # delete_files_in_folder(output_merge_path)
        anomaly_detection_output = read_csv_file(csv_path)
        detection_output = read_csv_file(csv_path)
        detection_save_path = os.path.join(output_merge_path, "result.txt")
        match_and_ensemble(
            anomaly_detection_output,
            detection_output,
            use_anomaly=use_anomaly,
            output_file=detection_save_path,
        )
        return f"file saved: {detection_save_path}"
    except Exception as e:
        return f"Error: {str(e)}"


@router.post(
    "/inference/tracking",
    status_code=status.HTTP_200_OK,
    summary="object tracking",
    description="""\
이 엔드포인트는 tracking 모델을 사용하여 detection한 객체를 추적합니다. \
사용자가 제공한 detection 결과(`det_result_path`)를 입력받아서 결과를 `result_path`에 저장합니다.

### 예시
- `det_result_path`: /home/dva4/DVA_LAB/backend/test/model/merged/result.txt
- `result_path`: /home/dva4/DVA_LAB/backend/test/model/tracking/result.txt
""",
)
async def inference_tracking(detection_path, save_path):
    url = "http://localhost:8004/bytetrack/track"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {"det_result_path": detection_path, "result_path": save_path}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error in external API: {response.text}",
        )

    return f"file saved: {response.json()}"


def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*"))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
