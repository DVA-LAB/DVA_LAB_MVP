import sys
sys.path.insert(0, '/home/dva4/DVA_LAB')

import os
import cv2
import math
import argparse
from models.BEV.api.services.Orthophoto_Maps.main_dg import *
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


def read_log_file(log_path):
    # Reading the CSV file into a DataFrame
    df = pd.read_csv(log_path)

    # Displaying the first few rows of the DataFrame
    return df


def calculate_nearest_distance(dolphin_present, merged_dolphin_center, centers, classes, track_ids, gsd):
    distances = {}
    if not dolphin_present:
        return distances

    for i in range(len(centers)):
        if classes[i] == 1:  # 선박인 경우
            # 병합된 돌고래 바운딩 박스 중심과의 거리 계산
            distance = math.sqrt((merged_dolphin_center[0] - centers[i][0]) ** 2 + (merged_dolphin_center[1] - centers[i][1]) ** 2)
            real_distance = distance * gsd
            distances[(track_ids[i],classes[i])] = real_distance
    
    return distances


def calculate_speed(center1, center2, frame_rate, gsd):
    """
    두 중심점과 프레임 속도를 기반으로 선박의 속도를 계산합니다.
    """
    # 픽셀 단위의 거리
    pixel_distance = math.sqrt((center2[0] - center1[0]) ** 2 + (center2[1] - center1[1]) ** 2)
    # 실제 거리 (미터 단위)
    real_distance = pixel_distance * gsd
    # 시간 간격 (초 단위)
    time_interval = 1 / frame_rate
    # 속도 (미터/초)
    speed = real_distance / time_interval
    # 속도를 km/h 단위로 변환
    speed_kmh = round(speed * 3.6, 2)
    return speed_kmh


def read_bbox_data(file_path, img_shape):
    # bbox.txt 파일을 읽고 프레임별 bounding box 데이터를 저장합니다.
    max_row = img_shape[0]
    max_col = img_shape[1]
    data = {}
    with open(file_path, 'r') as file:
        for line in file:
            frame_id, track_id, class_id, a, b, c, d, conf, _, _, _ = map(float, line.split(','))
            a = np.clip(a, 0, max_col - 1)
            b = np.clip(b, 0, max_row - 1)
            c = np.clip(c, 0, max_col - 1)
            d = np.clip(d, 0, max_row - 1)
            if frame_id not in data:
                data[frame_id] = []
            data[frame_id].append({'track_id': int(track_id), 'bbox': (a, b, c, d), 'class': class_id, 'conf': conf})
    return data


def draw_lines_and_distances(draw, centers, merged_dolphin_center, classes, font, gsd, line_color=(0, 0, 255)):
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
    radii_info는 (반지름, 색상) 튜플의 리스트입니다.
    """
    for radius, color in radii_info:
        # 원을 그립니다.
        draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], outline=color, width=15)
        # 원의 선 위에 텍스트를 표시합니다.
        draw.text((center[0] + radius + 10, center[1] - 10), f"{round(radius*gsd,2)}m", font=font, fill=color)

def get_image_paths(directory: str) -> list:
    image_paths = []
    for root, _, files in os.walk(directory):
        for file in sorted(files):  # Sort files before appending
            image_path = os.path.join(root, file)
            image_paths.append(image_path)

    return image_paths

def get_max_dimensions(image_paths):
    max_width = 0
    max_height = 0
    for path in image_paths:
        with Image.open(path) as img:
            width, height = img.size
            max_width = max(max_width, width)
            max_height = max(max_height, height)
    return max_width, max_height

def make_video(image_paths, video_name, fps=30, max_resolution=(3840, 2160)):
    max_width, max_height = max_resolution
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    video = cv2.VideoWriter(video_name, fourcc, fps, (max_width, max_height))

    for i, path in enumerate(image_paths):
        if i > 10:
            break
        img = cv2.imread(path)
        h, w, _ = img.shape

        # Resize images while preserving aspect ratio
        scale = min(max_width / w, max_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h))
        if (new_w, new_h) != (max_width, max_height):
            top, bottom = (max_height - new_h) // 2, (max_height - new_h + 1) // 2
            left, right = (max_width - new_w) // 2, (max_width - new_w + 1) // 2
            img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT)

        video.write(img)

    video.release()


def main(args):
    global gsd
    frame_rate=30
    image_paths = get_image_paths(args.input_dir)
    
    # 첫 번째 이미지를 기준으로 비디오 크기 설정
    first_image = cv2.imread(image_paths[0])
    frame_height, frame_width, layers = first_image.shape

    logs = read_log_file(args.log_path)
    bbox_data = read_bbox_data(args.bbox_path, first_image.shape)

    # font = ImageFont.truetype('AppleGothic.ttf', 40)
    font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 40)
    
    with open(args.GSD_path, 'r') as file:
        gsd_list = [tuple(map(float, line.strip().split())) for line in file]

    
    min_distance = '-'
    frame_count = 0
    previous_centers = {}
    max_ship_speed = 0
    
    for image_path in image_paths:
        frame = cv2.imread(image_path)
        date = logs['datetime'][frame_count]
        frame_bboxes = bbox_data.get(frame_count, [])
        gsd = gsd_list[frame_count][1]
        
        dolphin_bboxes = []
        track_ids=[]
        centers = []  # bbox 중심점들을 저장합니다.
        classes = []  # bbox의 클래스 정보를 저장합니다.
        ships_within_50m = set()
        ships_within_300m = set()
        ship_speeds = {}
        center_x, center_y = None, None
        dolphin_present = False

        rst, transformed_img, bbox, boundary_rows, boundary_cols, gsd, eo, R, focal_length, pixel_size = BEV_FullFrame(frame_count, image_path, args.log_path, gsd, args.output_dir, DEV = False)
        if rst:
            continue
        else:
            image = Image.fromarray(transformed_img)
            draw = ImageDraw.Draw(image)

        if len(frame_bboxes) > 0 :
            for bbox_info in frame_bboxes:
                track_id = bbox_info['track_id']
                class_id = bbox_info['class']
                
                if rst:
                    continue
                else:
                    rectify_points = BEV_Points(frame.shape, bbox, boundary_rows, boundary_cols, gsd, eo, R, focal_length, pixel_size, bbox_info['bbox'])

                x1, y1, x2, y2 = rectify_points

                if class_id == 1:
                    center_x, center_y = x2, y2
                else:
                    # bbox의 중심점을 계산합니다.
                    center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
                
                centers.append((center_x, center_y))
                classes.append(class_id)
                track_ids.append(track_id)

                if track_id == 999999:
                    dolphin_present = True
                    merged_dolphin_center = (center_x, center_y)

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

                else: # 돌고래인 경우
                    dolphin_bboxes.append(bbox_info)
                    dolphin_present = True
                
                if not (center_x == None and center_y == None):
                    if class_id == 0:
                        draw_radius_circles(draw, merged_dolphin_center, [(50/gsd, "black"), (300/gsd, "yellow")], font, gsd)
                        draw.rectangle(xy=(x1, y1, x2, y2), width=5, outline=(0, 0, 255))

                    # 모든 bbox 중심점들 사이에 선을 그리고 거리를 표시합니다.
                    if dolphin_present:
                        draw_lines_and_distances(draw, centers, merged_dolphin_center, classes, gsd, font)
                        nearest_distances = calculate_nearest_distance(dolphin_present, merged_dolphin_center, centers, classes, track_ids, gsd)
                        for (track_id, cls), distance in nearest_distances.items():
                            if cls == 1:
                                if distance <= 300:
                                    ships_within_300m.add(track_id)
                                if distance <= 50:
                                    ships_within_50m.add(track_id)
                        violation = False

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
                        nearest_distances = {}

                    if nearest_distances:
                        min_distance = min(nearest_distances.values())
                        min_distance = round(min_distance, 2)  # Round after finding the minimum
                        min_distance = str(min_distance)
                    else:
                        min_distance = "-"  # Or any other placeholder you prefer
                
        font_color = (0, 0, 0) # if violation else (0, 255, 0)

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
        # 결과 이미지 저장
        output_frame_path = os.path.join(args.output_dir, f'frame_{str(frame_count).zfill(6)}.png')
        cv2.imwrite(output_frame_path, img)
        frame_count += 1

    make_video(get_image_paths(args.output_dir), args.output_video)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_path', type=str, default='/home/dva4/DVA_LAB/backend/test/sync_csv/sync_log.csv')
    parser.add_argument('--bbox_path', type=str, default='/home/dva4/DVA_LAB/backend/utils/visualizing/bev_points.csv')
    parser.add_argument('--output_video', type=str, default='/home/dva4/DVA_LAB/backend/test/visualize_bev.avi')
    parser.add_argument('--input_dir', type=str, default='/home/dva4/DVA_LAB/backend/test/frame_origin')
    parser.add_argument('--output_dir', type=str, default='/home/dva4/DVA_LAB/backend/test/frame_bev_infer')
    parser.add_argument('--GSD_path', type=str, default='backend/test/GSD_total.txt')
    args = parser.parse_args()
    main(args)
