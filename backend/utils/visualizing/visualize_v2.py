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
    columns = ['frame', 'input_GSD', 'ship_speed']
    df = pd.read_csv(gsd_speed_path, sep=',', names=columns, header=None, skipinitialspace=True, engine='python', on_bad_lines='skip')
    df['frame'] = df['frame'].astype(int)
    df['input_GSD'] = df['input_GSD'].astype(float)
    df['ship_speed'] = df['ship_speed'].apply(lambda x: x.split(',')[0] if isinstance(x, str) else x)
    df['ship_speed'] = pd.to_numeric(df['ship_speed'], errors='coerce')
    return df

def calculate_distance(box1, box2):
    """두 바운딩 박스 중심점 사이의 거리를 계산합니다."""
    center1 = (box1[0] + box1[2] / 2, box1[1] + box1[3] / 2)
    center2 = (box2[0] + box2[2] / 2, box2[1] + box2[3] / 2)
    return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

def draw_bounding_boxes(frame, bboxes, classes, ids, font, px_50m, px_300m, ship_speed):
    """프레임에 바운딩 박스를 그리고 가장 가까운 선박과 돌고래를 연결합니다."""
    draw = ImageDraw.Draw(frame, 'RGBA')
    boats = []
    dolphins = []
    
    for bbox, cls, id in zip(bboxes, classes, ids):
        x, y, w, h = map(float, bbox)
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + w), int(y + h)
        
        if cls == 0:  # 선박
            color = (0, 255, 0, 255)  # 녹색
            fill_color = (0, 255, 0, 102)  # 40% 불투명 녹색
            boats.append((x1, y1, x2, y2))
            label = f"Boat_{id} ({ship_speed:.2f} km/h)"
        else:  # 돌고래
            color = (255, 71, 226, 255)  # FF47E2
            fill_color = (255, 71, 226, 102)  # 40% 불투명 FF47E2
            dolphins.append((x1, y1, x2, y2))
            label = "Dolphin"
        
        # 바운딩 박스 그리기 (채우기 포함)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2, fill=fill_color)
        
        # 라벨 그리기
        text_bbox = font.getbbox(label)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill=color)
        draw.text((x1, y1 - text_height), label, font=font, fill=(0, 0, 0))
        
        # 중심점 그리기
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        draw.rectangle([center_x - 2, center_y - 2, center_x + 2, center_y + 2], fill=(255, 0, 0))

    # 돌고래가 존재할 때만 선박 주변에 원 그리기
    if dolphins:
        for boat in boats:
            x1, y1, x2, y2 = boat
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            circle_color = (168, 85, 247, 51)  # A855F7 with 20% opacity
            draw.ellipse([center_x-px_50m, center_y-px_50m, 
                          center_x+px_50m, center_y+px_50m], 
                         outline=(168, 85, 247, 255), width=2, fill=circle_color)
            draw.ellipse([center_x-px_300m, center_y-px_300m, 
                          center_x+px_300m, center_y+px_300m], 
                         outline=(168, 85, 247, 255), width=2, fill=circle_color)
    
    # 가장 가까운 선박과 돌고래 연결
    if boats and dolphins:
        min_distance = float('inf')
        closest_pair = None
        for boat in boats:
            for dolphin in dolphins:
                distance = calculate_distance(boat, dolphin)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (boat, dolphin)
    
        if closest_pair:
            boat, dolphin = closest_pair
            boat_center = ((boat[0] + boat[2]) // 2, (boat[1] + boat[3]) // 2)
            dolphin_center = ((dolphin[0] + dolphin[2]) // 2, (dolphin[1] + dolphin[3]) // 2)
            draw.line([boat_center, dolphin_center], fill=(255, 0, 0, 255), width=2)
    
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
        
        # 현재 프레임에 해당하는 GSD와 속도 정보 가져오기
        current_gsd_speed = gsd_speed_data[gsd_speed_data['frame'] == frame_count]
        if not current_gsd_speed.empty:
            input_GSD = current_gsd_speed['input_GSD'].values[0]
            ship_speed = current_gsd_speed['ship_speed'].values[0]
            if pd.isna(ship_speed):
                ship_speed = 0.0
        else:
            input_GSD = 0.033962  # 기본값 설정
            ship_speed = 0.0

        # px_50m와 px_300m 계산
        px_50m = int(50 / input_GSD) if input_GSD != 0 else 0
        px_300m = int(300 / input_GSD) if input_GSD != 0 else 0

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        pil_image = draw_bounding_boxes(pil_image, bboxes, classes, ids, font, px_50m, px_300m, ship_speed)
        
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