from fastapi import APIRouter, Depends, status, Request

import argparse
import time
import csv
import os

from loguru import logger

from api.services import BYTETracker
from api.services import Timer
from interface.request import TrackingRequest

import numpy as np

def make_parser():
    """
        객체추적에 사용할 사용자 옵션을 반환합니다.

        Args
            - fps (int): 초당 프레임 수
            - track_thresh (float): tracking confidence treshold
            - track_buffer (int): 트래킹이 끊긴 프레임을 보존할 버퍼 크기
            - match_thresh (float): matching threshold for tracking
            - min_box_area (float): 최소 bbox 넓이
            - mot20 (bool): 데이터셋이 mot20 여부

        Return
            - parser (argparse.ArgumentParser()): 사용자 옵션 값
    """

    parser = argparse.ArgumentParser("ByteTrack")

    parser.add_argument("--fps", default=30, type=int, help="frame rate (fps)")
    # tracking args
    parser.add_argument("--track_thresh", type=float, default=0.2, help="tracking confidence threshold")
    parser.add_argument("--track_buffer", type=int, default=30, help="the frames for keep lost tracks")
    parser.add_argument("--match_thresh", type=float, default=0.8, help="matching threshold for tracking")
    parser.add_argument(
        "--aspect_ratio_thresh", type=float, default=1.6,
        help="threshold for filtering out boxes of which aspect ratio are above the given value."
    )
    parser.add_argument('--min_box_area', type=float, default=1, help='filter out tiny boxes')
    parser.add_argument("--mot20", dest="mot20", default=False, action="store_true", help="test mot20.")
    return parser

def merge_bboxes(track_results):
    """
    여러 경계 상자들을 포함하는 하나의 큰 경계 상자를 계산합니다.
    """
    global merged_dolphin_center
    if not track_results:
        merged_dolphin_center = None
        return None

    # 각 경계 상자의 최소 x, y 및 최대 x, y 좌표를 계산합니다.
    min_x = min(track_result.tlwh[0] for track_result in track_results)
    min_y = min(track_result.tlwh[1] for track_result in track_results)
    max_x = max(track_result.tlwh[0] + track_result.tlwh[2] for track_result in track_results)
    max_y = max(track_result.tlwh[1] + track_result.tlwh[3] for track_result in track_results)

    merged_dolphin_center = (min_x + (max_x - min_x) / 2, min_y + (max_y - min_y) / 2)
    return (min_x, min_y, max_x, max_y)


def track(det_results, img_w, img_h, result_path, args):
    """
        객체추적을 수행하고 그 결과를 파일로 생성합니다.

        Args
            - det_results (list): 객체탐지 & 이상탐지 결과가 병합된 파일이 ByteTrack의 입력이 될 수 있도록 변환된 결과
            - img_w (int): 이미지의 가로 크기
            - img_h (int): 이미지의 세로 크기
            - result_path (str): 객체추적 결과가 저장될 파일 경로
            - args (argparse.ArgumentParser()): 객체추적에 사용할 사용자 옵션
    """

    tracker = BYTETracker(args, frame_rate=args.fps)
    timer = Timer()
    results = []
    ############### for bev viz ###############
    data = []
    ###############            ###############
    timer.tic()
    for frame_id, det_result in enumerate(det_results, 1):
        if det_result is not None and np.array(det_result).size > 0:
            online_targets = tracker.update(np.array(det_result), [img_h, img_w], [img_h, img_w])
            online_tlwhs = []
            online_ids = []
            online_scores = []
            online_labels = []
            ############### for bev viz ###############
            points = []
            dolphin_bboxes = []
            ###############            ###############
            for t in online_targets:
                tlwh = t.tlwh
                tid = t.track_id
                label = int(t.label)
                
                if tlwh[2] * tlwh[3] > args.min_box_area:
                    online_tlwhs.append(tlwh)
                    online_ids.append(tid)
                    online_scores.append(t.score)
                    online_labels.append(label)
                    
                    if label == 1 and t.score < 0.8:
                        continue
                    
                    # save results
                    results.append(f"{frame_id},{tid},{label},{tlwh[0]:.2f},{tlwh[1]:.2f},{tlwh[2]:.2f},{tlwh[3]:.2f},{t.score:.2f},-1,-1,-1\n")
                    
                    ############### for bev viz ###############
                    # bbox의 중심점을 계산합니다.
                    center_x, center_y = (tlwh[0] + tlwh[2]) / 2, (tlwh[1] + tlwh[3]) / 2

                    if label == 1: # 선박인 경우
                        points = [frame_id, tid, label, center_x+1, center_y+1, center_x, center_y, t.score, -1,-1,-1]
                    else : # 돌고래인 경우
                        dolphin_bboxes.append(t)
                    
                    # csv data add
                    if len(points)>0:
                        data.append(points)
                        points = []
            
            # 모든 돌고래 bbox를 하나로 합칩니다.
            merged_dolphin_bbox = merge_bboxes(dolphin_bboxes)
            if merged_dolphin_bbox is not None:
                center_x, center_y = (merged_dolphin_bbox[0]+merged_dolphin_bbox[2])/2,  (merged_dolphin_bbox[1]+merged_dolphin_bbox[3])/2 
                if label == 0 :
                    points = [frame_id, 999999, label, merged_dolphin_bbox[0],merged_dolphin_bbox[1],merged_dolphin_bbox[2], merged_dolphin_bbox[3],t.score,-1,-1,-1]
                
            # csv data add
            if len(points)>0:
                data.append(points)

        timer.toc()
        if frame_id % 20 == 0:
            logger.info('Processing frame {}: avg {:.4f} seconds per frame'.format(frame_id, timer.average_time))


    with open(result_path, 'w') as f:
        f.writelines(results)
    g = open("/home/dva4/DVA_LAB/backend/test/bev_points.csv", "w")
    writer = csv.writer(g)
    writer.writerows(data)
    g.close()
    logger.info(f"save results to {result_path}")


def main(det_result_path, result_path):
    """
        객체추적 모델에 인퍼런스를 수행하는 메인 함수 역할을 수행합니다.

        Args
            - det_result_path (str): 객체탐지와 이상탐지의 결과가 병합된 bbox 정보가 담긴 파일 경로
            - reult_path (str): 객체추적 결과가 저장될 파일 경로
    """

    args = make_parser().parse_args()

    # 시작 시간 로그
    current_time = time.localtime(time.time())
    time_format = '%Y-%m-%d %H:%M:%S'
    time_str = time.strftime(time_format,current_time)
    logger.info('Start time: {}'.format(time_str))

    # 검출 결과 파일 읽어서 bytetrack 인풋 형태로 변환
    f = open(det_result_path, 'r')
    lines = f.readlines()
    f.close()
    
    grouped_data = {}
    for line in lines:
        line = line.replace("\n", "")
        line = line.split(",")
        
        key = int(float(line[0]))
        values = [float(value) for value in line[1:]]
        if key not in grouped_data.keys():
            
            grouped_data[key] = []        
        grouped_data[key].append(values)
    det_results = [grouped_data[key] for key in sorted(grouped_data.keys())]

    # 추후 인풋 형식 맞출 때 반영 필요: img w, h 정보 추가
    img_w, img_h = 3840, 1260
    track(det_results, img_w, img_h, result_path, args)


router = APIRouter(tags=["bytetrack"])

@router.post(
    "/bytetrack/track",
    status_code=status.HTTP_200_OK,
    summary="bytetrack",
)
async def inference(body: TrackingRequest):
    """
        객체추적 모델에 인퍼런스를 수행한 뒤 결과 bbox가 담긴 파일 경로를 반환합니다.

        Args
            - body
                - det_result_path (str): 객체탐지와 이상탐지의 결과가 병합된 bbox 정보가 담긴 파일 경로
                - result_path (str): 객체추적 결과가 저장될 파일 경로

        Return
            - result_path (str): 객체추적 결과가 저장된 파일 경로
    """

    det_result_path = body.det_result_path
    result_path = body.result_path
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    main(det_result_path, result_path)
    return result_path
