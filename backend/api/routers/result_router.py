from autologging import logged
from fastapi import APIRouter, Depends, status
from interface.request import VisRequest
from utils.visualizing.visualize import show_result, set_gsd, set_merged_dolphin_center
import requests
import json
import glob
import os
from fastapi import (APIRouter, Depends, FastAPI, File, Form, HTTPException,
                     UploadFile, status)
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(tags=["result"])


@router.post(
    "/visualize",
    status_code=status.HTTP_200_OK,
    summary="visualizing result",
)
async def model_inference(body: VisRequest):
    log_file = glob.glob(os.path.join(body.log_path, '*.csv'))[0]
    # TODO@jh: mp4 외 영상 옵션 추가
    video_file = glob.glob(os.path.join(body.video_path, '*.mp4'))[0]

    with open(os.path.join('test', 'GSD.txt'), 'r') as f:
        gsd = f.read()
    set_gsd(float(gsd))

    set_merged_dolphin_center(body.set_merged_dolphin_center)

    os.makedirs(os.path.dirname(body.output_video), exist_ok=True)
    delete_files_in_folder(os.path.dirname(body.output_video))
    show_result(log_file, video_file, body.output_video, body.bbox_path)
    return body.output_video


@router.get(
    "/export/origin",
    status_code=status.HTTP_200_OK,
    summary="export origin video",
)
async def export_origin():
    video_storage_path = "/home/dva4/dva/backend/test/result/result.mp4"
    return FileResponse(video_storage_path)


# TODO@jh: 공통 유틸로 빼기
def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*"))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)