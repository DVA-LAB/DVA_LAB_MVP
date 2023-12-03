import cv2
import math
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backend.utils.extract_meta import extract_date_from_srt, extract_video_metadata

LEGAL_SPEED = 50
GSD = 0.06 #m/px
merged_dolphin_center = None

def calculate_nearest_distance(centers, classes, track_ids, GSD):
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
    # bbox.txt 파일을 읽고 프레임별 bounding box 데이터를 저장합니다.
    data = {}
    with open(file_path, 'r') as file:
        for line in file:
            frame_id, track_id, label, x, y, w, h, conf, _, _, _ = map(float, line.split(','))
            if frame_id not in data:
                data[frame_id] = []
            data[frame_id].append({'track_id': int(track_id), 'bbox': (x, y, w, h), 'class': label, 'conf': conf})
    return data

def draw_lines_and_distances(draw, centers, classes, font, line_color=(255, 0, 0)):
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
            
            draw.text(mid_point, f"{round(distance*GSD, 2)}m", font=font, fill=line_color)


def draw_radius_circles(draw, center, radii_info, font):
    """
    주어진 중심점에서 지정된 반지름으로 원을 그리고 반지름 값을 표시합니다.
    radii_info는 (반지름, 색상) 튜플의 리스트입니다.
    """
    for radius, color in radii_info:
        # 원을 그립니다.
        draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], outline=color, width=2)
        # 원의 선 위에 텍스트를 표시합니다.
        draw.text((center[0] + radius + 10, center[1] - 10), f"{radius*GSD}m", font=font, fill=color)

def merge_bboxes(bboxes):
    """
    여러 경계 상자들을 포함하는 하나의 큰 경계 상자를 계산합니다.
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--srt_path', type=str, default='data/DJI_0010.srt')
    parser.add_argument('--video_path', type=str, default='in/input.mp4')
    parser.add_argument('--output_video', type=str, default='out/output.mp4')
    parser.add_argument('--bbox_path', type=str, default='in/bbox.txt')
    args = parser.parse_args()

    # bbox 데이터를 읽어옵니다.
    bbox_data = read_bbox_data(args.bbox_path)
    frame_rate, total_frames, frame_width, frame_height = extract_video_metadata(args.video_path)
    
    font = ImageFont.truetype('AppleGothic.ttf', 40)
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    out = cv2.VideoWriter(args.output_video, fourcc, frame_rate, (frame_width, frame_height))
    cap = cv2.VideoCapture(args.video_path)
    
    frame_count = 0
    previous_centers = {}
    max_ship_speed = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_bboxes = bbox_data.get(frame_count, [])
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image)

        # 좌상단에 흰색 배경 사각형을 그립니다.
        dashboard_background = (0, 0, 700, 300)  # 좌표 (x0, y0, x1, y1)
        draw.rectangle(dashboard_background, fill=(255, 255, 255))
        
        dolphin_bboxes = []
        track_ids=[]
        centers = []  # bbox 중심점들을 저장합니다.
        classes = []  # bbox의 클래스 정보를 저장합니다.
        ships_within_300m = set()
        ship_speeds = {}

        for bbox_info in frame_bboxes:
            track_id = bbox_info['track_id']
            x, y, w, h = bbox_info['bbox']
            class_id = bbox_info['class']
            if class_id == 2:
                class_id = 0 # dolphin
            else:
                class_id = 1 # boat

            conf_score = round(bbox_info['conf'], 2)
            if class_id == 1 and conf_score < 0.6:
                continue
            
            # bbox의 중심점을 계산합니다.
            center_x, center_y = x + w / 2, y + h / 2
            # bbox 중심점과 클래스 정보를 추가합니다.
            centers.append((center_x, center_y))
            classes.append(class_id)
            track_ids.append(track_id)
            
            if class_id == 1:  # 선박인 경우
                draw.rectangle(xy=(x, y, x + w, y + h), width=5, outline=(0, 255, 0))
                # 중심점 저장
                if track_id not in previous_centers:
                    previous_centers[track_id] = (center_x, center_y)
                else:
                    # 속도 계산
                    speed_kmh = calculate_speed(previous_centers[track_id], (center_x, center_y), frame_rate, GSD)
                    ship_speeds[track_id] = speed_kmh
                    max_ship_speed = max(max_ship_speed, speed_kmh)
                    # 중심점 업데이트
                    previous_centers[track_id] = (center_x, center_y)

            if class_id == 0:
                dolphin_bboxes.append(bbox_info)

        # 모든 돌고래 bbox를 하나로 합칩니다.
        merged_dolphin_bbox = merge_bboxes(dolphin_bboxes)
        if merged_dolphin_bbox is not None:
            center_x, center_y = merged_dolphin_bbox[0], merged_dolphin_bbox[1] 
            draw_radius_circles(draw, (center_x, center_y), [(50/GSD, "yellow"), (300/GSD, "purple")], font)
            # 그리고 해당 bbox를 그립니다.
            draw.rectangle(xy=merged_dolphin_bbox, width=5, outline=(0, 255, 0))

        # 모든 bbox 중심점들 사이에 선을 그리고 거리를 표시합니다.
        draw_lines_and_distances(draw, centers, classes, font)

        dolphin_present, nearest_distances = calculate_nearest_distance(centers, classes, track_ids, GSD)
        for (track_id, cls), distance in nearest_distances.items():
            if cls == 1:
                if distance <= 300:
                    ships_within_300m.add(track_id)

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
        font_color = (0, 0, 255) # if violation else (0, 255, 0)

        # 텍스트를 흰색 배경 사각형 위에 그립니다.
        text_positions = [(30, 30), (30, 80), (30, 130), (30, 180)]
        texts = [
            f"Frame number: {frame_count}",
            f"Nearest distance: {min_distance}m",
            f"Max ship speed: {max_ship_speed}km/h",
            f"Ships within 300m: {len(ships_within_300m)}"
        ]

        for text, pos in zip(texts, text_positions):
            draw.text(pos, text, font=font, fill=font_color)
        
        # 나머지 코드
        img = np.array(image)
        out.write(img)
        cv2.imshow(args.video_path, img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_count += 1
        
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
