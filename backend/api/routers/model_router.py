import glob
import json
import os

import requests
from autologging import logged
from fastapi import APIRouter, Depends, HTTPException, status
from interface.request import ModelRequest
from utils.merge_bboxes import (match_and_ensemble, plot_detections, read_csv_file, read_file)

router = APIRouter(tags=["model"])


@router.post(
    "/inference",
    status_code=status.HTTP_200_OK,
    summary="AI model run",
)
async def model_inference(body: ModelRequest):
    """
        AI 모델(객체탐지, 이상탐지, 객체추적)을 구동 후 생성된 bbox 파일 경로를 반환합니다.

        Args
            - body
                - body.frame_path (str): 원본 프레임이 저장된 경로
                - body.detection_save_path (str): 객체탐지 결과가 저장된 경로
                - body.sliced_path (str): 원본 프레임이 슬라이싱 된 경로

        Raise
            - fastapi.HTTPException: 모델 구동 중 에러가 발생할 경우 서버 에러(500)를 발생
        
        Return
            - result_path (str): 모델 구동 결과로 생성된 bbox의 파일 경로
    """

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
    """
        Pretrained YOLO 모델과 SAHI를 이용해 객체탐지를 수행합니다. 
        
        이후 관련 폴더 경로들을 json 형태로 반환합니다.

        요청 URL: http://localhost:8002/sahi/inference

        Args
            - img_path (str): 원본 프레임 경로
            - csv_path (str): 객체인식 결과파일 저장경로
            - sliced_path (str): 원본 프레임이 슬라이싱된 경로

        Raise
            - fastapi.HTTPException: 서버의 객체 탐지 결과가 200 OK가 아닌 경우 HTTP 예외 발생

        Return
            - JSON(
                - img_path (str): 원본 프레임 경로
                - csv_path (str): 객체인식 결과파일 저장경로
                - sliced_path (str): 원본 프레임이 슬라이싱된 경로
            )
    """

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
- `patch_size` : 1024
- `overlap_ratio` : 0.2
""",
)

async def inference_segmentation(frame_path, slices_path, output_path, patch_size:int, overlap_ratio:float):
    """
        Pretrained Anomaly Detection 모델을 사용해 이상탐지 인퍼런스 결과를 요청합니다.

        요청 URL: http://localhost:8003/anomaly/inference

        Args
            - frame_path (str): 이상탐지를 수행할 프레임 파일경로
            - slices_path (str): 이상탐지를 수행할 프레임 파일이 슬라이싱된 패치 디렉터리 경로
            - output_path (str): 이상탐지 결과가 저장될 파일경로

        Raise
            - fastapi.HTTPException: 서버의 이상 탐지 결과가 200 OK가 아닌 경우 HTTP 예외를 발생
            
        Return
            - JSON(
                - output_img (np.ndarray): 이상탐지 결과 마스크가 시각화된 이미지
                - output_mask (np.ndarray): 이상탐지 결과 마스크
                - output_list (list): N x [frame_number, class_id, x1, y1, w1, h1, anomaly_score]
            )
    """

    url = "http://localhost:8003/anomaly/inference"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {
        "frame_path": frame_path,
        "slices_path": slices_path,
        "output_path": output_path,
        "patch_size": patch_size,
        "overlap_ratio":overlap_ratio
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
async def inference_merge(output_merge_path, csv_path, anomaly_detection_output, use_anomaly: bool = True):
    """
        객체 탐지 결과와 이상 탐지 결과를 병합한 파일을 생성합니다. 

        병합된 파일은 os.path.join(output_merge_path, "result.txt")의 경로에 생성됩니다.
    
        Args
            - output_merge_path (str): 객체 탐지 bbox와 이상 탐지 bbox를 병합한 결과 bbox를 저장할 경로
            - csv_path (str): 객체 탐지 결과 bbox 파일 경로
            - anomaly_detection_output (str): 이상 탐지 결과 bbox 파일 경로
            - use_anomaly (bool): 이상 탐지의 결과 bbox와의 병합 여부

        Raise
            - Exception: 예외가 발생할 경우 예외 에러 메시지 출력

        Return
            - 파일이 특정 경로에 저장되었다는 메세지 스트링 (str)
    """

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
    """
        ByteTrack을 활용하여 객체추적 인퍼런스 결과를 요청후 파일 저장 성공 메시지를 반환합니다.

        요청 URL: http://localhost:8004/bytetrack/track

        Args
            - detection_path (str): 객체탐지 결과경로
            - save_path (str): 객체추적 결과파일 저장경로

        Raise
            - fastapi.HTTPException: 서버의 이상 탐지 결과가 200 OK가 아닌 경우 HTTP 예외를 발생

        Return
            - 객체추적 인퍼런스 결과 파일이 저장되었다는 메시지 스트링 (str)
    """

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
    """
        특정 폴더에 담긴 파일을 전부 삭제합니다.

        Args
            - folder_path (str): 폴더 경로
    """

    files = glob.glob(os.path.join(folder_path, "*"))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
