from fastapi import APIRouter, Depends, status, Request

import argparse
import time
import os

from loguru import logger

from api.services import BYTETracker
from api.services import Timer
from interface.request import TrackingRequest

import numpy as np

def make_parser():
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

def track(det_results, img_w, img_h, result_path, args):
    tracker = BYTETracker(args, frame_rate=args.fps)
    timer = Timer()
    results = []
    timer.tic()
    for frame_id, det_result in enumerate(det_results, 1):
        if det_result is not None and np.array(det_result).size > 0:
            online_targets = tracker.update(np.array(det_result), [img_h, img_w], [img_h, img_w])
            online_tlwhs = []
            online_ids = []
            online_scores = []
            online_labels = []
            for t in online_targets:
                tlwh = t.tlwh
                tid = t.track_id
                label = int(t.label)
                
                if tlwh[2] * tlwh[3] > args.min_box_area:
                    online_tlwhs.append(tlwh)
                    online_ids.append(tid)
                    online_scores.append(t.score)
                    online_labels.append(label)
                    # save results
                    results.append(f"{frame_id},{tid},{label},{tlwh[0]:.2f},{tlwh[1]:.2f},{tlwh[2]:.2f},{tlwh[3]:.2f},{t.score:.2f},-1,-1,-1\n")
        timer.toc()
        if frame_id % 20 == 0:
            logger.info('Processing frame {}: avg {:.4f} seconds per frame'.format(frame_id, timer.average_time))

    with open(result_path, 'w') as f:
        f.writelines(results)
    logger.info(f"save results to {result_path}")


def main(det_result_path, result_path):
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

    # 추후 인풋 형식 맞출 때 반영 필요: img w, h 절보 추가
    img_w, img_h = 3840, 1260
    
    track(det_results, img_w, img_h, result_path, args)


router = APIRouter(tags=["bytetrack"])

@router.post(
    "/bytetrack/track",
    status_code=status.HTTP_200_OK,
    summary="bytetrack",
)
async def inference(body: TrackingRequest):
    det_result_path = body.det_result_path
    result_path = body.result_path
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    main(det_result_path, result_path)
    return result_path