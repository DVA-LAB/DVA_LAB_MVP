import sys
sys.path.insert(0, '/home/dva4/DVA_LAB')

import os
import cv2
import csv
import math
import time
from tqdm import tqdm
import argparse
from models.BEV.api.services.Orthophoto_Maps.main_dg import *
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

def read_log_file(log_path):
    """
        로그 파일을 pandas 데이터 프레임으로 읽어 반환합니다.

        Args:
            log_path (str): 로그 파일 경로입니다.

        Return:
            df (pd.DataFrame): pandas DataFrame 형식의 로그 파일입니다.
    """

    # Reading the CSV file into a DataFrame
    df = pd.read_csv(log_path)

    return df

def calculate_nearest_distance(centers, classes, track_ids, GSD):
    """
        선박과 돌고래 간의 최단거리를 계산합니다.
    
        Args:
            - centers (list): 선박의 중심점이 담긴 배열입니다.
            - classes (list): 클래스 정보가 담긴 배열입니다.
            - track_ids (list): track_id가 담긴 배열입니다.
            - GSD (float): gsd 값입니다.

        Return:
            - dolphin_present (bool): 돌고래 존재 여부를 의미합니다.
            - distances (list): 병합된 돌고래 바운딩 박스 중심과 선박간의 실제 거리가 담긴 배열입니다.
    
    """

    global merged_dolphin_center
    distances = {}
    dolphin_present = merged_dolphin_center is not None
    if not dolphin_present:
        return dolphin_present, distances

    for i in range(len(centers)):
        if classes[i] == 1:  # 선박인 경우
            # 병합된 돌고래 바운딩 박스 중심과의 거리 계산
            distance = math.sqrt((merged_dolphin_center[0] - centers[i][0]) ** 2 + (merged_dolphin_center[1] - centers[i][1]) ** 2)
            real_distance = distance * GSD
            distances[(track_ids[i],classes[i])] = real_distance
    
    return dolphin_present, distances


def calculate_speed(center1, center2, frame_rate, GSD):
    """
        두 중심점과 프레임 속도를 기반으로 선박의 속도를 계산합니다.

        Args:
            - center1 (list): 첫 번째 중심점이며 [x, y]로 구성됩니다.
            - center2 (list): 두 번째 중심점이며 [x, y]로 구성됩니다.
            - frame_rate (float): 프레임 레이트입니다.
            - gsd (float): GSD 값입니다.

        Return:
            - speed_kmh (float): 선박의 km/h 속도입니다.
    """
    # 픽셀 단위의 거리
    pixel_distance = math.sqrt((center2[0] - center1[0]) ** 2 + (center2[1] - center1[1]) ** 2)
    # 실제 거리 (미터 단위)
    real_distance = pixel_distance * GSD
    # 시간 간격 (초 단위)
    time_interval = 1 / frame_rate
    # 속도 (미터/초)
    speed = real_distance / time_interval
    # 속도를 km/h 단위로 변환
    speed_kmh = round(speed * 3.6, 2)
    return speed_kmh


def read_bbox_data(file_path):
    """
        bbox.txt 파일을 읽고 프레임별 bounding box 데이터를 저장합니다.
    
        Args:
            - file_path (str): bbox.txt 파일이 위치하는 경로입니다.

        Return:
            - data (dict): 프레임 번호 당 track_id, bbox, class, conf가 담긴 데이터입니다.
            
            ex) data[frame_id].append({'track_id': int(track_id), 'bbox': (a, b, c, d), 'class': class_id, 'conf': conf})
    """

    data = {}
    with open(file_path, 'r') as file:
        for line in file:
            frame_id, track_id, label, x, y, w, h, conf, _, _, _ = map(float, line.split(','))
            if frame_id not in data:
                data[frame_id] = []
            data[frame_id].append({'track_id': int(track_id), 'bbox': (x, y, w, h), 'class': label, 'conf': conf})
    return data

def draw_lines_and_distances(draw, centers, classes, font, gsd, line_color=(0, 0, 255)):
    """
        이미지에 선박과 돌고래 사이의 선을 그리고 거리 정보를 시각화합니다.    
    
        Args:
            - draw (PIL.ImageDraw.Draw()): 드로잉 객체
            - centers (list): 중심점 리스트
            - classes (list): 객체 클래스 리스트
            - font (PIL.ImageFont.truetype): 폰트 정보
            - gsd (float): GSD 값
            - line_color (tuple): 선 색
    """
        
    global merged_dolphin_center
    if merged_dolphin_center is None:
        return  # 돌고래가 없으면 거리를 그릴 필요가 없습니다.

    for i in range(len(centers)):
        if classes[i] == 1:  # 선박인 경우
            # 병합된 돌고래 바운딩 박스 중심과 선박 중심점 사이에 선을 그립니다.
            start, end = centers[i], merged_dolphin_center
            draw.line([start, end], fill=line_color, width=2)

            # 두 점 사이의 거리를 계산합니다.
            distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
            mid_point = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            
            draw.text(mid_point, f"{round(distance*gsd, 2)}m", font=font, fill=line_color)


def draw_radius_circles(draw, center, radii_info, font, gsd):
    """
        주어진 중심점에서 지정된 반지름으로 원을 그리고 반지름 값을 표시합니다.

        Args:
            draw (PIL.ImageDraw.Draw()): 드로잉 객체
            center (list): 중심점 리스트 [x, y]
            radii_info (list(tuple)): (반지름, 색상) 튜플로 구성된 리스트
            font (PIL.ImageFont.truetype): 폰트 정보
            gsd (float): GSD 값
    """
    for radius, color in radii_info:
        # 원을 그립니다.
        draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], outline=color, width=15)
        # 원의 선 위에 텍스트를 표시합니다.
        draw.text((center[0] + radius + 10, center[1] - 10), f"{round(radius*gsd,2)}m", font=font, fill=color)


def merge_bboxes(bboxes):
    """
        여러 경계 상자들을 포함하는 하나의 큰 경계 상자를 계산합니다.
        
        Args:
            - bboxes (list): bbox 리스트입니다.

        Return:
            - bbox (tuple)
                - min_x (float): bbox를 구성하는 최소 x값
                - min_y (float): bbox를 구성하는 최소 y값
                - max_x (float): bbox를 구성하는 최대 x값
                - max_y (float): bbox를 구성하는 최대 y값
    """
    global merged_dolphin_center
    if not bboxes:
        merged_dolphin_center = None
        return None

    # 각 경계 상자의 최소 x, y 및 최대 x, y 좌표를 계산합니다.
    min_x = min(bbox['bbox'][0] for bbox in bboxes)
    min_y = min(bbox['bbox'][1] for bbox in bboxes)
    max_x = max(bbox['bbox'][0] + bbox['bbox'][2] for bbox in bboxes)
    max_y = max(bbox['bbox'][1] + bbox['bbox'][3] for bbox in bboxes)

    merged_dolphin_center = (min_x + (max_x - min_x) / 2, min_y + (max_y - min_y) / 2)
    return (min_x, min_y, max_x, max_y)

def get_image_paths(directory: str) -> list:
    """
        디렉터리 내의 모든 이미지 파일 경로를 가져옵니다.

        Args:
            directory (str): 디렉터리 경로

        Return:
            image_paths (list): 이미지 파일 경로 리스트
    """
    image_paths = []
    for root, _, files in os.walk(directory):
        for file in sorted(files):  # Sort files before appending
            image_path = os.path.join(root, file)
            image_paths.append(image_path)

    return image_paths


def show_result(args): #log_path, input_dir, output_video, bbox_path, frame_rate=30):
    """
        시각화를 수행하고 수행 결과를 비디오 파일로 저장합니다.
        
        또한 이후 BEV 시각화를 위한 bev_points.csv 파일을 생성합니다.
        
        Args:
            - args (argparse.ArgumentParser): 옵션 값입니다.
                - args.input_dir (str): 원본 프레임이 위치한 폴더 경로입니다.
                - args.log_path (str): log 파일이 위치한 파일 경로입니다.
                - args.bbox_path (str): bbox 정보가 담긴 파일이 위치한 경로입니다.
                - args.output_video (str): 출력 비디오로 생성할 파일 경로입니다.
                - args.GSD_path (str): GSD 파일이 위치한 경로입니다.
    """
    start_time = time.time()
    frame_rate=30

    image_paths = get_image_paths(args.input_dir)
    
    # 첫 번째 이미지를 기준으로 비디오 크기 설정
    first_image = cv2.imread(image_paths[0])
    frame_height, frame_width, _ = first_image.shape

    logs = read_log_file(args.log_path)
    bbox_data = read_bbox_data(args.bbox_path)
    
    # font = ImageFont.truetype('AppleGothic.ttf', 40)
    font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 40)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    temp = args.output_video.split('.')[0]+"_temp.mp4"
    out = cv2.VideoWriter(temp, fourcc, frame_rate, (frame_width, frame_height))
    
    with open(args.GSD_path, 'r') as file:
        gsd_list = [tuple(map(float, line.strip().split())) for line in file]

    frame_count = 0
    previous_centers = {}
    max_ship_speed = 0
    data = []
    try:
        for image_path in tqdm(image_paths):
            frame = cv2.imread(image_path)
            date = logs['datetime'][frame_count]
            frame_bboxes = bbox_data.get(frame_count, [])
            image = Image.fromarray(frame)
            draw = ImageDraw.Draw(image)
            gsd = gsd_list[frame_count][1]
            # pixel_size = gsd_list[frame_count][2]

            dolphin_bboxes = []
            track_ids=[]
            centers = []  # bbox 중심점들을 저장합니다.
            classes = []  # bbox의 클래스 정보를 저장합니다.
            points = []
            ships_within_50m = set()
            ships_within_300m = set()
            ship_speeds = {}

            try:
                # BEV_FullFrame 함수 호출
                rst, _, _, _, _, gsd_bev, _, _, _, _ = BEV_FullFrame(frame_count, image_path, args.log_path, gsd, DEV = False)
                if rst:
                    print(f"Frame {frame_count} is skipped by BEV_FullFrame")
                    continue
                else:
                    gsd = gsd_bev / 3
                # if (gsd == 0 and pixel_size == 0):
                #     # BEV_FullFrame 함수 호출
                #     rst, _, _, _, _, gsd, _, _, _, pixel_size = BEV_FullFrame(frame_count, image_path, args.log_path, gsd, DEV = False)
                #     if rst:
                #         print(f"Frame {frame_count} is skipped by BEV_FullFrame")
                #         continue
                #     else:
                #         gsd = pixel_size
                # else:
                #     gsd = pixel_size
            except Exception as e:
                print(f"Error in BEV_FullFrame at frame {frame_count}: {e}")


            for bbox_info in frame_bboxes:
                track_id = bbox_info['track_id']
                x, y, w, h = bbox_info['bbox']
                class_id = int(bbox_info['class'])
                conf_score = round(bbox_info['conf'], 2)
                
                if class_id == 0 and conf_score < 0.5:
                    continue
                if class_id == 1 and conf_score < 0.8:
                    continue
                
                # bbox의 중심점을 계산합니다.
                center_x, center_y = x + w / 2, y + h / 2

                centers.append((center_x, center_y))
                classes.append(class_id)
                track_ids.append(track_id)
                
                if class_id == 1:  # 선박인 경우
                    # 중심 좌표에 작은 초록색 점을 그림
                    outer_radius = 10  # 외부 원의 반지름
                    draw.ellipse((center_x - outer_radius, center_y - outer_radius, center_x + outer_radius, center_y + outer_radius), outline=(0, 0, 255), width=10)

                    # 중심점 저장
                    if track_id not in previous_centers:
                        previous_centers[track_id] = (center_x, center_y)
                    else:
                        # 속도 계산
                        speed_kmh = calculate_speed(previous_centers[track_id], (center_x, center_y), frame_rate, gsd)
                        ship_speeds[track_id] = speed_kmh
                        max_ship_speed = max(max_ship_speed, speed_kmh)
                        # 중심점 업데이트
                        previous_centers[track_id] = (center_x, center_y)
                    
                    points = [frame_count, track_id, class_id, center_x+1, center_y+1, center_x, center_y, conf_score,-1,-1,-1 ]
                else : # 돌고래인 경우
                    dolphin_bboxes.append(bbox_info)
                
                # csv data add
                if len(points)>0:
                    data.append(points)
                    points = []

            # 모든 돌고래 bbox를 하나로 합칩니다.
            merged_dolphin_bbox = merge_bboxes(dolphin_bboxes)
            if merged_dolphin_bbox is not None:
                center_x, center_y = (merged_dolphin_bbox[0]+merged_dolphin_bbox[2])/2,  (merged_dolphin_bbox[1]+merged_dolphin_bbox[3])/2
                draw_radius_circles(draw, (center_x, center_y), [(50/gsd, "black"), (300/gsd, "yellow")], font, gsd)
                # 그리고 해당 bbox를 그립니다.
                draw.rectangle(xy=merged_dolphin_bbox, width=5, outline=(0, 0, 255))
                
                if class_id == 0:
                    points = [frame_count, 999999, class_id, merged_dolphin_bbox[0],merged_dolphin_bbox[1],merged_dolphin_bbox[2], merged_dolphin_bbox[3],conf_score,-1,-1,-1]
                
            # 모든 bbox 중심점들 사이에 선을 그리고 거리를 표시합니다.
            draw_lines_and_distances(draw, centers, classes, font, gsd)

            dolphin_present, nearest_distances = calculate_nearest_distance(centers, classes, track_ids, gsd)
            for (track_id, cls), distance in nearest_distances.items():
                if cls == 1:
                    if distance <= 300:
                        ships_within_300m.add(track_id)
                    if distance <= 50:
                        ships_within_50m.add(track_id)
            violation = False

            if dolphin_present:
                # Apply the rules based on the distance and speed
                for ship_id, speed in ship_speeds.items():
                    if ship_id in ships_within_300m:
                        distance = nearest_distances.get((ship_id, 1), float('inf'))  # Assuming class 1 is for ships
                        if distance <= 50:
                            violation = True  # Rule 1
                        elif 50 < distance <= 300 and speed > 0:
                            violation = True  # Rule 2
                        elif 300 < distance <= 750 and speed >= 9.26:
                            violation = True  # Rule 3
                        elif 750 < distance <= 1500 and speed >= 18.52:
                            violation = True  # Rule 4
                        elif distance <= 300 and len(ships_within_300m) >= 3:
                            violation = True  # Rule 5
            else:
                # Rule 6: No dolphins, no violation
                violation = False

            if nearest_distances:
                min_distance = min(nearest_distances.values())
                min_distance = round(min_distance, 2)  # Round after finding the minimum
                min_distance = str(min_distance)
            else:
                min_distance = "-"  # Or any other placeholder you prefer
            font_color = (0, 0, 0) # if violation else (0, 255, 0)

            # csv data add
            if len(points)>0:
                data.append(points)

            # 텍스트를 흰색 배경 사각형 위에 그립니다.
            text_positions = [(30, 30), (30, 80), (30, 130), (30, 180), (30, 230), (30, 280)]
            texts = [
                f"일시: {date}",
                f"프레임 숫자: {frame_count}",
                f"픽셀 사이즈: {round(gsd,5)}m/px",
                f"선박과 가장 가까운 거리: {min_distance}m",
                f"50m 이내의 선박 수: {len(ships_within_50m)}",
                f"300m 이내의 선박 수: {len(ships_within_300m)}"
            ]

            # 좌상단에 흰색 배경 사각형을 그립니다.
            dashboard_background = (0, 0, 700, 350)  # 좌표 (x0, y0, x1, y1)
            draw.rectangle(dashboard_background, fill=(255, 255, 255))

            for text, pos in zip(texts, text_positions):
                draw.text(pos, text, font=font, fill=font_color)
            
            # 나머지 코드
            img = np.array(image)
            out.write(img)
            # cv2.imwrite(f'test_{frame_count}.jpg', img)
            # cv2.imshow(args.video_path, img)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            #     break

            frame_count += 1
    except Exception as e:
        print(f"Error during processing frame {frame_count}: {e}")

    f = open("backend/utils/visualizing/bev_points.csv", "w")
    writer = csv.writer(f)
    writer.writerows(data)
    f.close()
    out.release()
    os.system(f"ffmpeg -y -i {args.output_video.split('.')[0]}_temp.mp4 -vcodec h264 -movflags +faststart {args.output_video}")
    os.system(f"rm {args.output_video.split('.')[0]}_temp.mp4")
    end_time = time.time()
    # 걸린 시간 계산
    elapsed_time = end_time - start_time
    print(f"Video writing completed. Total frames processed: {frame_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_path', type=str, default='backend/test/sync_csv/sync_log.csv')
    parser.add_argument('--input_dir', type=str, default='backend/test/frame_origin')
    parser.add_argument('--output_video', type=str, default='backend/test/visualize.mp4')
    parser.add_argument('--bbox_path', type=str, default='backend/test/model/tracking/result.txt')
    parser.add_argument('--GSD_path', type=str, default='backend/test/GSD_total.txt')
    args = parser.parse_args()
    show_result(args)