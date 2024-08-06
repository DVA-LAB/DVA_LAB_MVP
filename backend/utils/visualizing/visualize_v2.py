import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import argparse
import subprocess

def create_directory(directory):
    """디렉토리가 존재하지 않으면 생성합니다."""
    os.makedirs(directory, exist_ok=True)

def read_csv_data(csv_path):
    """CSV 파일을 읽어 DataFrame으로 반환합니다."""
    return pd.read_csv(csv_path)

def read_gsd_speed_data(gsd_speed_path):
    """GSD_speed.txt 파일을 읽어 DataFrame으로 반환합니다."""
    columns = ['frame', 'object_id', 'input_GSD', 'ship_speed']
    df = pd.read_csv(gsd_speed_path, sep=',', names=columns, header=None, skipinitialspace=True, engine='python', on_bad_lines='skip')
    df['frame'] = df['frame'].astype(int)
    df['object_id'] = df['object_id'].apply(lambda x: 999999 if x == '-' else int(float(x)))  # Ensure object_id is integer and replace '-' with 999999
    df['input_GSD'] = df['input_GSD'].astype(float)
    df['ship_speed'] = pd.to_numeric(df['ship_speed'], errors='coerce')
    return df

def calculate_distance(box1, box2):
    """두 바운딩 박스 중심점 사이의 거리를 계산합니다."""
    center1 = (box1[0] + box1[2] / 2, box1[1] + box1[3] / 2)
    center2 = (box2[0] + box2[2] / 2, box2[1] + box2[3] / 2)
    return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

def draw_bounding_boxes(frame, bboxes, classes, ids, font, px_50m, px_300m, gsd_speed_data, frame_count, input_GSD):
    draw = ImageDraw.Draw(frame, 'RGBA')
    boats = []
    dolphins = []

    for bbox, cls, id in zip(bboxes, classes, ids):
        x, y, w, h = map(float, bbox)
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + w), int(y + h)

        if cls == 0:  # 선박
            ship_speed_row = gsd_speed_data[(gsd_speed_data['frame'] == frame_count) & (gsd_speed_data['object_id'] == id)]
            if not ship_speed_row.empty:
                ship_speed = ship_speed_row.iloc[0]['ship_speed']
            else:
                ship_speed = 0.0

            boats.append((x1, y1, x2, y2, id, ship_speed))
        else:  # 돌고래
            color = (255, 71, 226, 255)  # FF47E2
            fill_color = (255, 71, 226, 102)  # 40% 투명도 FF47E2
            dolphins.append((x1, y1, x2, y2))

            # 돌고래 바운딩 박스 그리기
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2, fill=fill_color)
            label = "Dolphin"
            text_bbox = font.getbbox(label)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3  # 텍스트 박스 높이 1.3배로 키움
            draw.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill=color)
            draw.text((x1, y1 - text_height), label, font=font, fill=(0, 0, 0))

            # 중심점 그리기
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=color, outline=color)

    # 돌고래가 존재할 때만 선박 주변에 원 그리기
    if dolphins:
        for boat in boats:
            x1, y1, x2, y2, id, ship_speed = boat
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            circle_color = (216,171,138,51)  # D946EF with 40% opacity
            draw.ellipse([center_x - px_50m, center_y - px_50m, center_x + px_50m, center_y + px_50m],
                         outline=(216,171,138,51), width=2, fill=circle_color)
            draw.ellipse([center_x - px_300m, center_y - px_300m, center_x + px_300m, center_y + px_300m],
                         outline=(216,171,138,51), width=2, fill=circle_color)

    # 가장 가까운 선박과 돌고래 연결 및 거리 표시
    min_distance = float('inf')
    if boats and dolphins:
        closest_pair = None
        for boat in boats:
            bx1, by1, bx2, by2, id, ship_speed = boat
            for dolphin in dolphins:
                dx1, dy1, dx2, dy2 = dolphin
                distance = calculate_distance([bx1, by1, bx2 - bx1, by2 - by1], [dx1, dy1, dx2 - dx1, dy2 - dy1])
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (boat, dolphin)

        if closest_pair:
            boat, dolphin = closest_pair
            bx1, by1, bx2, by2, id, ship_speed = boat
            dx1, dy1, dx2, dy2 = dolphin
            boat_center = ((bx1 + bx2) // 2, (by1 + by2) // 2)
            dolphin_center = ((dx1 + dx2) // 2, (dy1 + dy2) // 2)
            draw.line([boat_center, dolphin_center], fill=(255, 0, 0, 255), width=2)

            # 텍스트 박스 그리기 및 높이 조정
            distance_text = f"{min_distance * input_GSD:.1f}m"
            mid_point = ((boat_center[0] + dolphin_center[0]) // 2, (boat_center[1] + dolphin_center[1]) // 2)
            text_bbox = font.getbbox(distance_text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3  # 텍스트 박스 높이 1.3배로 키움

            # 배경색 결정
            if min_distance * input_GSD <= 50:
                # 선박의 바운딩 박스를 F87171의 40% 투명도로 채우고, 테두리와 글자 bbox를 F87171로 변경
                for boat in boats:
                    bx1, by1, bx2, by2, id, ship_speed = boat
                    fill_color = (248, 113, 113, 102)  # F87171 with 40% opacity
                    draw.rectangle([bx1, by1, bx2, by2], outline=(248, 113, 113, 255), width=2, fill=fill_color)
                    label = f"Boat{id} ({int(ship_speed)} km/h)"
                    text_bbox = font.getbbox(label)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = (text_bbox[3] - text_bbox[1]) * 1.3  # 텍스트 박스 높이 1.3배로 키움
                    draw.rectangle([bx1, by1 - text_height, bx1 + text_width, by1], fill=(248, 113, 113, 255))
                    draw.text((bx1, by1 - text_height), label, font=font, fill=(0, 0, 0))

                    # 중심점도 색상 변경
                    center_x, center_y = (bx1 + bx2) // 2, (by1 + by2) // 2
                    draw.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=(248, 113, 113, 255), outline=(248, 113, 113, 255))

                background_color = (239, 68, 68, 255)  # EF4444
            else:
                background_color = (55, 65, 81, 255)  # 374151

            draw.rectangle([mid_point[0] - text_width // 2, mid_point[1] - text_height // 2,
                            mid_point[0] + text_width // 2, mid_point[1] + text_height // 2], fill=background_color)
            draw.text((mid_point[0] - text_width // 2, mid_point[1] - text_height // 2), distance_text, font=font, fill=(255, 255, 255))

    # 선박 바운딩 박스 그리기 (마지막에 그리기)
    for boat in boats:
        x1, y1, x2, y2, id, ship_speed = boat
        color = (0, 255, 40, 255)  # 00FF28
        fill_color = (0, 255, 40, 102)  # 40% 투명도 00FF28

        if min_distance * input_GSD <= 50:
            color = (248, 113, 113, 255)  # F87171
            fill_color = (248, 113, 113, 102)  # 40% 투명도 F87171

        draw.rectangle([x1, y1, x2, y2], outline=color, width=2, fill=fill_color)
        label = f"Boat{id} ({int(ship_speed)} km/h)"
        text_bbox = font.getbbox(label)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = (text_bbox[3] - text_bbox[1]) * 1.3  # 텍스트 박스 높이 1.3배로 키움
        draw.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill=color)
        draw.text((x1, y1 - text_height), label, font=font, fill=(0, 0, 0))

        # 중심점 그리기
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        draw.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=color, outline=color)

    return frame


def process_video(input_video, csv_path, gsd_speed_path, output_dir, output_video):
    """비디오를 처리하고 시각화된 프레임을 저장합니다."""
    create_directory(output_dir)
    
    cap = cv2.VideoCapture(input_video)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    csv_data = read_csv_data(csv_path)
    gsd_speed_data = read_gsd_speed_data(gsd_speed_path)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 25)
    
    frame_count = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_data = csv_data[csv_data['Frame'] == frame_count]
        bboxes = frame_data[['X', 'Y', 'Width', 'Height']].values
        classes = frame_data['Label'].values
        ids = frame_data['Track_ID'].values
        
        # px_50m와 px_300m 계산
        current_gsd_speed = gsd_speed_data[gsd_speed_data['frame'] == frame_count]
        if not current_gsd_speed.empty:
            input_GSD = current_gsd_speed.iloc[0]['input_GSD']
        else:
            input_GSD = 0.033962  # 기본값 설정

        px_50m = int(50 / input_GSD) if input_GSD != 0 else 0
        px_300m = int(300 / input_GSD) if input_GSD != 0 else 0

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        pil_image = draw_bounding_boxes(pil_image, bboxes, classes, ids, font, px_50m, px_300m, gsd_speed_data, frame_count, input_GSD)
        
        frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)
        
        output_frame_path = os.path.join(output_dir, f'frame_{str(frame_count).zfill(6)}.jpg')
        cv2.imwrite(output_frame_path, frame)
        
        frame_count += 1

    cap.release()

    # ffmpeg을 사용하여 프레임을 비디오로 변환
    cmd = [
        'ffmpeg',
        '-y',
        '-framerate', str(fps),
        '-i', f'{output_dir}/frame_%06d.jpg',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '22',
        '-pix_fmt', 'yuv420p',
        output_video
    ]
    subprocess.run(cmd, check=True)


def main(args):
    process_video(args.input_video, args.csv_path, args.gsd_speed_path, args.output_dir, args.output_video)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video with bounding boxes")
    parser.add_argument('--input_video', type=str, required=True, help='Path to input video file')
    parser.add_argument('--csv_path', type=str, required=True, help='Path to CSV file with bounding box data')
    parser.add_argument('--gsd_speed_path', type=str, required=True, help='Path to GSD_speed.txt file')
    parser.add_argument('--output_dir', type=str, default='output_frames', help='Directory to save output frames')
    parser.add_argument('--output_video', type=str, default='output.mp4', help='Path to save output video')
    args = parser.parse_args()
    
    main(args)
