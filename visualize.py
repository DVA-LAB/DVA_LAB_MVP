import cv2
import math
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backend.utils.extract_meta import extract_date_from_srt, extract_video_metadata

LEGAL_SPEED = 50
LEGAL_DISTANCE = 50

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
    """
    지정된 두 클래스(여기서는 보트와 돌고래) 간의 거리만을 그립니다.
    """
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            # 클래스 확인: 하나는 보트이고 다른 하나는 돌고래여야 합니다.
            if (classes[i] == 1 and classes[j] == 0) or (classes[i] == 0 and classes[j] == 1):
                # 두 중심점 사이에 선을 그립니다.
                start, end = centers[i], centers[j]
                draw.line([start, end], fill=line_color, width=2)

                # 두 점 사이의 거리를 계산합니다.
                distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                mid_point = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
                draw.text(mid_point, f"{int(distance)}px", font=font, fill=line_color)


def draw_radius_circles(draw, center, radii_info, font):
    """
    주어진 중심점에서 지정된 반지름으로 원을 그리고 반지름 값을 표시합니다.
    radii_info는 (반지름, 색상) 튜플의 리스트입니다.
    """
    for radius, color in radii_info:
        # 원을 그립니다.
        draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], outline=color, width=2)
        # 원의 선 위에 텍스트를 표시합니다.
        draw.text((center[0] + radius + 10, center[1] - 10), f"{radius/4}m", font=font, fill=color)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--srt_path', type=str, default='data/DJI_0010.srt')
    parser.add_argument('--video_path', type=str, default='in/DJI_0119_30.MP4')
    parser.add_argument('--output_video', type=str, default='out/DJI_0119_30.MP4')
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

        centers = []  # bbox 중심점들을 저장합니다.
        classes = []  # bbox의 클래스 정보를 저장합니다.

        for bbox_info in frame_bboxes:
            x, y, w, h = bbox_info['bbox']
            class_id = bbox_info['class']
            conf_score = round(bbox_info['conf'], 2)
            # bbox의 중심점을 계산합니다.
            center_x, center_y = x + w / 2, y + h / 2
            # bbox 중심점과 클래스 정보를 추가합니다.
            centers.append((center_x, center_y))
            classes.append(class_id)
            draw.rectangle(xy=(x, y, x + w, y + h), width=5, outline=(0, 255, 0))
            if class_id == 0:
                draw_radius_circles(draw, (center_x, center_y), [(200, "yellow"), (1200, "purple")], font)
            # draw.text(xy=(x, y - 20), text=f"Conf: {conf_score}", font=font, fill=(0, 255, 0))

        # 대시보드에 표시할 텍스트 정보를 생성합니다.
        max_ship_speed, nearest_distance = 0, 0  # 구현 필요
        violation = (LEGAL_DISTANCE > nearest_distance) or (LEGAL_SPEED < max_ship_speed)
        font_color = (0, 0, 255) if violation else (0, 255, 0)

        # 모든 bbox 중심점들 사이에 선을 그리고 거리를 표시합니다.
        draw_lines_and_distances(draw, centers, classes, font)

        # 텍스트를 흰색 배경 사각형 위에 그립니다.
        text_positions = [(30, 30), (30, 80), (30, 130)]
        texts = [
            f"Violation: {violation}",
            f"Nearest distance: {nearest_distance}m",
            f"Max ship speed: {max_ship_speed}km/s"
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
