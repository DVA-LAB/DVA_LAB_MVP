import glob
import json
import os
import shutil
import time
from typing import List

import requests
import torch
from api.services.data_service import parse_videos_multithreaded
from fastapi import (APIRouter, Depends, FastAPI, File, Form, HTTPException,
                     UploadFile, status)
from fastapi.responses import FileResponse, JSONResponse
from interface.request.user_input_request import UserInput
from utils.log_sync.adjust_log import do_sync
from utils.remove_glare import remove_glare

router = APIRouter(tags=["data"])

video_path = os.path.abspath(os.path.join("test", "video_origin"))
processed_video_path = os.path.abspath(os.path.join("test", "video_origin_remove"))
frame_path = os.path.abspath(os.path.join("test", "frame_origin"))
csv_path = os.path.abspath(os.path.join("test", "csv"))
srt_path = os.path.abspath(os.path.join("test", "srt"))
sync_path = os.path.abspath(os.path.join("test", "sync_csv"))
input_path = os.path.abspath(os.path.join("test", "input"))


@router.post("/video/")
async def upload_video(file: UploadFile = File(...), preprocess: bool = Form(...)):
    """
        사용자가 업로드한 비디오를 저장합니다.
    
        Args
            - file (fastapi.UploadFile): 사용자로부터 업로드되는 파일
            - preprocess (bool): 빛반사 제거와 같은 전처리 기능 사용 여부
        Raise
            - 비디오 전처리 또는 저장과정에서 에러가 발생할 경우 서버 에러 발생
        Return
            - json 형식의 파일 업로드 성공 메시지
    """

    s_time = time.time()
    os.makedirs(video_path, exist_ok=True)
    os.makedirs(frame_path, exist_ok=True)
    # delete_files_in_folder(video_path)
    # delete_files_in_folder(frame_path)
    try:
        file_location = os.path.join(video_path, lowercase_extensions(file.filename))
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        save_time = time.time()
        # print(f"video saving time: {round(save_time - s_time, 0)} sec")

        # TODO@jh: frame parsing을 background task로 처리하는 경우, 다 parsing되기전에 사용자 요청이 오는 경우 처리가 힘들지만 먼가 방법 고안이 필요함
        if preprocess:
            is_cuda_available = torch.cuda.is_available()
            print(f"GPU for removing glare: {is_cuda_available}")
            process_s_time = time.time()
            os.makedirs(processed_video_path, exist_ok=True)
            # delete_files_in_folder(processed_video_path)
            save_path = os.path.join(
                processed_video_path, lowercase_extensions(file.filename)
            )
            remover = remove_glare.RGLARE(file_location, save_path, 4, True, True)
            remover.video_gpu()
            # TODO@jh: GPU cache clear 확인 필요
            process_f_time = time.time()
            print(
                f"removing glare time: {round(process_f_time - process_s_time, 0)} sec"
            )
            parse_videos_multithreaded(processed_video_path, frame_path)
            print(f"frame parsing time: {round(time.time() - process_f_time)} sec")
        else:
            frame_s_time = time.time()
            parse_videos_multithreaded(video_path, frame_path)
            print(f"frame parsing time: {round(time.time() - frame_s_time)} sec")

        print(f"total video upload time: {round(time.time() - s_time)} sec")
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.get("/video/")
async def get_video():
    """
        서버에 저장된 비디오 파일을 가져와 클라이언트에게 반환합니다.
    
        Raise
            - fastapi.HTTPException: 비디오 파일이 저장된 경로에서 비디오 목록 읽기에 실패한 경우 서버 에러(500)를 발생
        Return
            - fastapi.responses.FileResponse: 비디오 파일을 읽어 사용자에게 반환
            - fastapi.responses.JSONResponse: 비디오 파일이 없거나 여러 개의 파일이 있을 경우 사용자에게 json 형태의 에러 메시지와 404 에러 반환
    """

    video_storage_path = video_path
    try:
        videos = [
            f
            for f in os.listdir(video_storage_path)
            if os.path.isfile(os.path.join(video_storage_path, f))
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error accessing video storage: {e}"
        )
    if not videos or len(videos) > 1:
        return JSONResponse(
            status_code=404,
            content={"message": "Video not found or multiple videos present"},
        )
    file_location = os.path.join(video_storage_path, lowercase_extensions(videos[0]))
    return FileResponse(file_location)


@router.get("/frame/{frame_number}")
async def get_frame(frame_number: int):
    """
        사용자로부터 입력받은 프레임 번호에 해당하는 이미지를 반환합니다.

        Args
            - frame_number (int): 프레임 번호
        Raise
            - fastapi.HTTPException: 프레임 번호에 해당하는 이미지를 찾지 못하는 경우 서버 에러(500)을 발생
        Return
            - fastapi.responses.FileResponse: 프레임 번호에 해당하는 이미지
    """

    try:
        frames = glob.glob(os.path.join(frame_path, "*.jpg"))
        image_path = [
            x for x in frames if int(x.split("_")[-1].split(".")[0]) == frame_number
        ]
        if not len(image_path):
            return JSONResponse(status_code=404, content={"message": "Frame not found"})
        return FileResponse(image_path[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing frame: {e}")


@router.post("/csv/")
async def upload_csv(file: UploadFile = File(...)):
    """
        사용자가 업로드한 csv 로그 파일을 저장하고 그 결과 메시지를 json 형식으로 반환합니다.

        Args
            - file (fastapi.UploadFile): 사용자로부터 입력받는 csv 로그 파일
        Raise
            - fastapi.HTTPException: 파일 저장과정에서 에러가 발생한 경우 서버 에러(500)를 발생
        Return
            - 파일 저장 성공 메시지를 담은 "message" 필드와 파일명이 담긴 "filename" 필드를 포함하는 json
    """

    csv_storage_path = csv_path
    os.makedirs(csv_storage_path, exist_ok=True)
    # delete_files_in_folder(csv_storage_path)
    try:
        file_location = os.path.join(
            csv_storage_path, lowercase_extensions(file.filename)
        )
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/srt/")
async def upload_srt(file: UploadFile = File(...)):
    """
        사용자가 업로드한 srt 파일을 저장합니다.

        Args
            - file (fastapi.UploadFile): 사용자로부터 입력받는 srt 파일
        Raise
            - fastapi.HTTPException: 파일을 저장하는 과정에서 에러가 발생할 경우 서버 에러(500)를 발생
        Return
            - 파일 저장 성공 메시지를 담은 "message" 필드와 파일명이 담긴 "filename" 필드를 포함하는 json
    """

    srt_storage_path = srt_path
    os.makedirs(srt_storage_path, exist_ok=True)
    # delete_files_in_folder(srt_storage_path)
    try:
        file_location = os.path.join(
            srt_storage_path, lowercase_extensions(file.filename)
        )
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/sync/")
async def sync_log():
    """
        사용자가 업로드한 csv 파일과 srt 파일을 간의 동기화를 수행합니다.

        Raise
            - csv, srt 파일 간 동기화에 실패할 경우 서버 에러(500)를 발생
        Return
            - 동기화 성공 메시지를 담은 "message" 필드를 포함하는 json
    """

    os.makedirs(sync_path, exist_ok=True)
    # delete_files_in_folder(sync_path)
    try:
        do_sync(video_path, csv_path, srt_path, sync_path)
        return {"message": "synchronized csv saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during file synchronization: {e}"
        )


@router.post("/user_input/")
async def save_input(request: UserInput):
    """
        사용자로부터 받은 프레임과 점 간 거리 정보를 통해 픽셀 사이즈와 GSD 값을 계산한 다음 파일 두 파일로 저장합니다.

            - user_input.txt: frame_number point1.x point1.y point2.x point2.y distance
            - GSD.txt:        frame_number gsd_mean pixelsize_mean
        Args
            - request
                - request.frame_number (int): 사용자가 선택한 프레임의 번호
                - request.points_distances (float): 사용자가 선택한 프레임에서 찍은 두 점의 (x, y) 좌표 리스트와 두 점간 거리
        Raise
            - fastapi.HTTPException: 픽셀 사이즈, GSD를 계산하는 과정에서 에러가 발생할 경우 서버 에러(500)를 발생
        Return
            - GSD 값이 저장된 파일의 절대경로를 포함한 단순 메시지 스트링
    """

    os.makedirs(input_path, exist_ok=True)
    # delete_files_in_folder(input_path)
    frame_number = request.frame_number
    point_distances = request.point_distances
    frame_file = [
        x
        for x in glob.glob(os.path.join(frame_path, "*.jpg"))
        if int(x.split("_")[-1].split(".")[0]) == frame_number
    ][0]
    try:
        gsds = []
        pixelsizes = []
        inputs = []
        for pd in point_distances:
            inputs.append(f'{frame_number} {pd.point1.x} {pd.point1.y} {pd.point2.x} {pd.point2.y} {pd.distance}')
            gsd, pixelsize = get_gsd(frame_number, frame_file, pd.point1.x, pd.point1.y, pd.point2.x, pd.point2.y, pd.distance)
            if gsd != 0:
                gsds.append(gsd)
                pixelsizes.append(pixelsize)
        gsd_mean = sum(gsds) / len(gsds)
        pixelsize_mean = sum(pixelsizes) / len(pixelsizes)
        with open(os.path.join("test", "GSD.txt"), "w") as f:
            f.write(f'{frame_number} {gsd_mean} {pixelsize_mean}')
        with open(os.path.join(input_path, 'user_input.txt'), 'w') as f:
            f.write('\n'.join(inputs))
        return f'초기 gsd값이 {os.path.abspath(os.path.join("test", "GSD.txt"))}에 저장되었습니다.'
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_gsd(frame_number, frame_file, x1, y1, x2, y2, m_distance):
    """
        사용자 입력 값을 기반으로 http://[IP].[PORT]/bev1로 POST를 요청한 뒤 GSD 값과 픽셀거리 값을 가져옵니다.

        Args
            - frame_number (int): 프레임 파일 번호
            - frame_file (str): 프레임 파일 경로
            - x1 (float): point1의 x좌표
            - y1 (float): point1의 y좌표
            - x2 (float): point2의 x좌표
            - y2 (float): point2의 y좌표
            - m_distance (float): point1과 point2 간 거리
        Return
            - Tuple (
                - gsd (float): GSD 값
                - pixel_size (float): 픽셀 크기 값
            )
    """

    url = "http://112.216.237.124:8001/bev1"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    data = {
        "frame_num": frame_number,
        "frame_path": frame_file,
        "csv_path": "/home/dva4/DVA_LAB/backend/test/sync_csv/sync_log.csv",
        "objects": [
            None,
            None,
            None,
            x1,
            y1,
            x2,
            y2,
            None,
            -1,
            -1,
            -1,
        ],
        "realdistance": m_distance,
        "dst_dir": "/home/dva4/DVA_LAB/backend/test/frame_bev",
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    result = response.json()
    if result[0] == 0:
        return result[-1], result[-2]
    else:
        return 0, 0

def calculate_pixel_distance(point1, point2):
    """
        두 픽셀 좌표 간의 유클리드 거리를 계산한 값을 반환합니다.

        두 점의 (x, y) 좌표는 다음과 같이 가져옵니다.

            - point1.x, point1.y
            - point2.x, point2.y

        Args
            - point1: 이미지의 픽셀 상의 한 점
            - point2: 이미지의 픽셀 상의 한 점
            
        Return
            - 두 픽셀 좌표 간 유클리드 거리
    """

    return ((point2.x - point1.x) ** 2 + (point2.y - point1.y) ** 2) ** 0.5


def calculate_average_distance(distances):
    """
        거리들의 평균 값을 반환합니다.

        Args
            - distances (list): 거리 배열

        Return
            - sum(distances) / len(distances)
    """
    
    return sum(distances) / len(distances)


def delete_files_in_folder(folder_path):
    """
        인자에 해당하는 경로의 모든 파일을 제거합니다.

        Args
            - folder_path (str): 폴더 경로
    """

    files = glob.glob(os.path.join(folder_path, "*"))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)


def lowercase_extensions(file_name):
    """
        파일명의 확장자를 소문자로 변환한 파일명을 반환합니다.

        Args
            - file_name (str): 확장자를 소문자로 변환할 파일명

        Return
            - new_file_name (str): 확장자를 소문자로 변환한 파일명
    """

    name, extension = os.path.splitext(file_name)
    new_file_name = name + extension.lower()

    return new_file_name


# @router.delete("/reset/")
# async def reset_data():
#     try:
#         delete_files_in_folder(video_path)
#         delete_files_in_folder(frame_path)
#         delete_files_in_folder(csv_path)
#         delete_files_in_folder(srt_path)
#         delete_files_in_folder(sync_path)
#         delete_files_in_folder(input_path)
#         return {"message": "All data reset successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during data reset: {e}")