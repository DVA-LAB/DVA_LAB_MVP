import glob
import json
import os
import requests
import json
import pandas as pd
import time

import requests
from autologging import logged
from fastapi import (APIRouter, Depends, FastAPI, File, Form, HTTPException,
                     UploadFile, status)
from fastapi.responses import FileResponse, JSONResponse
from interface.request import VisRequest, VisRequestBev
from utils.visualizing.visualize import (set_gsd, set_merged_dolphin_center,
                                         show_result)

router = APIRouter(tags=["result"])


@router.post(
    "/visualize",
    status_code=status.HTTP_200_OK,
    summary="visualizing result",
)
async def model_inference(body: VisRequest):
    log_file_path = glob.glob(os.path.join(body.log_path, '*.csv'))[0]
    logs = pd.read_csv(log_file_path)

    # Read GSD.txt and parse the frame number
    with open(os.path.abspath(os.path.join("test", "GSD.txt")), "r") as f:
        gsd_txt = f.read().split()
    frame_num = int(gsd_txt[0])  # Assuming the first value is the frame number

    # Call set_gsd with the DataFrame and frame number
    set_gsd(logs, frame_num)

    set_merged_dolphin_center(body.set_merged_dolphin_center)

    os.makedirs(os.path.dirname(body.output_video), exist_ok=True)
    delete_files_in_folder(os.path.dirname(body.output_video))
    show_result(log_file_path, body.input_dir, body.output_video, body.bbox_path)
    return body.output_video


@router.post(
    "/total_gsd",
    status_code=status.HTTP_200_OK,
    summary="구할 수 있는 모든 gsd를 구합니다.",
)
async def get_all_gsd(body: VisRequestBev):
    s_time = time.time()
    gsds = dict()
    with open(body.GSD_path, 'r') as f:
        initial_frame, initial_gsd = f.read().split(' ')

    # TODO@jh: user_input이 올바르게 저장되어 있지 않아서 임의로 가장 가까운 5의 배수로 수정함
    gsds[round(int(initial_frame) / 5) * 5] = initial_gsd

    with open(body.user_input, 'r') as f:
        distance = float(f.read().split(' ')[-1])

    r_s_time = time.time()
    ships_size = get_ship_size(body.user_input, body.frame_path, body.tracking_result)
    r_f_time = time.time()
    frame_nos = [int(x.split('_')[-1].split('.')[0]) for x in glob.glob(os.path.join(body.frame_path, '*.jpg'))]

    g_s_time = time.time()
    for ship_size in ships_size:  # [frame_no, point[0][0], point[0][1], point[1][0], point[1][0]]
        try:
            frame = ship_size[0]
            x1, y1, x2, y2 = ship_size[1:]
            frame_file = [x for x in glob.glob(os.path.join(body.frame_path, '*.jpg')) if int(x.split('_')[-1].split('.')[0])==int(frame)][0]
            gsd = get_gsd(frame, frame_file, x1, y1, x2, y2, distance)
            gsds[frame] = gsd
        except Exception as e:
            print(e)
    g_f_time = time.time()

    with open(body.GSD_save_path, 'w') as file:
        result = []
        for frame_no in sorted(frame_nos):
            try:
                result.append(f'{frame_no} {gsds[frame_no]}')
            except:
                result.append(f'{frame_no} {0}')
        file.write('\n'.join(result))

    return (f'새로 계산한 GSD: {body.GSD_save_path}',
            f'소요시간: {round(time.time() - s_time, 0)} sec',
            f'refiner 모듈이 계산한 선박 개수: {len(ships_size)}',
            f'refiner 계산에 소요된 시간: {round(r_f_time - r_s_time, 0)} sec',
            f'추가 gsd 계산에 소요된 시간: {round(g_f_time - g_s_time, 0)} sec')


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

def get_ship_size(user_input, frame_path, tracking_result):
    url = 'http://112.216.237.124:8005/ship_size'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "user_input": user_input,
        "frame_path": frame_path,
        "tracking_result": tracking_result
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_data = response.json()
    return response_data

def get_gsd(frame_number, frame_file, x1, y1, x2, y2, m_distance):
    url = "http://112.216.237.124:8001/bev1"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    data = {
        "frame_num": frame_number,
        "frame_path": frame_file,
        "csv_path": "/home/dva4/dva/backend/test/sync_csv/sync_log.csv",
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
        "dst_dir": "/home/dva4/dva/backend/test/frame_bev",
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    result = response.json()
    if result[0] == 0:
        return result[-1]
    else:
        return 0