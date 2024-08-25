import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import argparse
import subprocess

# Global color settings
COLORS = {
    "boat_fill": "00FF28_40",        
    "boat_outline": "00FF28_100",    
    "boat_center": "00FF28_100",
    "around_circle_50m": "D7EF46_20",    
    "around_circle_300m": "D7EF46_20",        
    "dolphin_fill": "FF47E2_40",    
    "dolphin_outline": "FF47E2_100", 
    "dolphin_center": "FF47E2_100", 
    "line_color": "374151_100",      
    "line_color_50m": "EF4444_100",  
    "text_bg_default": "374151_100",  
    "text_bg_50m": "EF4444_100",      
    "boat_fill_50m": "F87171_20",    
    "boat_outline_50m": "F87171_100",
}

def create_directory(directory):
    """디렉토리가 존재하지 않으면 생성합니다."""
    os.makedirs(directory, exist_ok=True)

def read_csv_data(csv_path):
    """CSV 파일을 읽어 DataFrame으로 반환합니다."""
    return pd.read_csv(csv_path)

def read_gsd_speed_data(gsd_speed_path):
    """Reads the GSD_speed.txt file and returns it as a DataFrame."""
    df = pd.read_csv(gsd_speed_path, sep=',', skipinitialspace=True, engine='python', on_bad_lines='skip')
    df = df.replace('-', np.nan)

    if df.isna().any().any():
        print("Warning: NaN values found in the data. These will be skipped or handled separately.")
        print(df[df.isna().any(axis=1)])  # Log rows with NaN values

    try:
        df['frame_idx'] = df['Frame'].astype(int)
        df['obj_idx'] = pd.to_numeric(df['Object_ID'], errors='coerce').dropna().astype(int)
        df['input_GSD'] = pd.to_numeric(df['Input_GSD'], errors='coerce')
        df['ship_speed'] = pd.to_numeric(df['Speed_kt'], errors='coerce')
    except ValueError as e:
        print(f"Error converting columns to the correct data types: {e}")
        raise
    
    return df

def calculate_distance(box1, box2):
    """두 바운딩 박스 중심점 사이의 거리를 계산합니다."""
    center1 = (box1[0] + box1[2] / 2, box1[1] + box1[3] / 2)
    center2 = (box2[0] + box2[2] / 2, box2[1] + box2[3] / 2)
    return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

def hex_to_rgba(hex_color):
    """Converts a hex color code and percentage opacity to an RGBA tuple."""
    hex_code, opacity_percentage = hex_color.split('_')
    r = int(hex_code[:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:], 16)
    a = int(float(opacity_percentage) * 255 / 100)  # Convert percentage to 0-255 range
    return (r, g, b, a)

def draw_dashed_line(draw, point1, point2, dash_length=40, color=(255, 0, 0, 255), width=2):
    """점선을 그립니다."""
    x1, y1 = point1
    x2, y2 = point2
    total_length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    dashes = int(total_length / dash_length)

    for i in range(dashes):
        start = (x1 + (x2 - x1) * i / dashes, y1 + (y2 - y1) * i / dashes)
        end = (x1 + (x2 - x1) * (i + 0.5) / dashes, y1 + (y2 - y1) * (i + 0.5) / dashes)
        draw.line([start, end], fill=color, width=width)

def draw_combined_layers(frame, bboxes, classes, ids, font, px_50m, px_300m, gsd_speed_data, frame_count, input_GSD):
    # 이미지 레이어들을 합성하기 위해 RGBA 포맷으로 변환
    base_frame = frame.convert("RGBA")

    # 레이어 2a: 선박 주위 50m 원
    layer2a = Image.new("RGBA", frame.size)
    draw2a = ImageDraw.Draw(layer2a, 'RGBA')

    # 레이어 2b: 선박 주위 300m 원
    layer2b = Image.new("RGBA", frame.size)
    draw2b = ImageDraw.Draw(layer2b, 'RGBA')

    # 레이어 4: 돌고래, 선박 바운딩 박스
    layer4 = Image.new("RGBA", frame.size)
    draw4 = ImageDraw.Draw(layer4, 'RGBA')

    boats = []
    dolphins = []

    # 돌고래와 선박을 레이어 4에 그리기
    for bbox, cls, id in zip(bboxes, classes, ids):
        x, y, w, h = map(float, bbox)
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + w), int(y + h)

        if cls == 0:  # 선박
            fill_color = hex_to_rgba(COLORS["boat_fill"])
            outline_color = hex_to_rgba(COLORS["boat_outline"])
            ship_speed_row = gsd_speed_data[(gsd_speed_data['frame_idx'] == frame_count) & (gsd_speed_data['obj_idx'] == id)]
            ship_speed = ship_speed_row.iloc[0]['ship_speed'] if not ship_speed_row.empty else 0.0
            boats.append((x1, y1, x2, y2, id, ship_speed))

            # 선박 바운딩 박스 그리기 (레이어 4)
            draw4.rectangle([x1, y1, x2, y2], outline=outline_color, width=2, fill=fill_color)
            label = f"Boat{id} ({int(ship_speed)} knots)"
            label_bbox = draw4.textbbox((0, 0), label, font=font)
            label_width = label_bbox[2] - label_bbox[0]
            label_height = (label_bbox[3] - label_bbox[1]) * 1.3

            # 선박 중심점 그리기 (레이어 4)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw4.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10],
                            fill=outline_color, outline=outline_color)
            # 레이블이 이미지 밖으로 벗어나는지 확인
            if y1 - label_height < 0:
                # 벗어나면 좌하단에 레이블 배치
                label_position = (x1, y2)
                draw4.rectangle([x1, y2, x1 + label_width, y2 + label_height], fill=outline_color)
                draw4.text(label_position, label, font=font, fill=(0, 0, 0))
            else:
                # 벗어나지 않으면 기본 위치에 레이블 배치
                label_position = (x1, y1 - label_height)
                draw4.rectangle([x1, y1 - label_height, x1 + label_width, y1], fill=outline_color)
                draw4.text(label_position, label, font=font, fill=(0, 0, 0))

        else:  # 돌고래
            outline_color = hex_to_rgba(COLORS["dolphin_outline"])
            dolphins.append((x1, y1, x2, y2))

            # 돌고래 바운딩 박스 그리기 (레이어 4)
            draw4.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)
            label = "Dolphin"
            text_bbox = draw4.textbbox((0, 0), label, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3
            draw4.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill=outline_color)
            draw4.text((x1, y1 - text_height), label, font=font, fill=(0, 0, 0))

            # 돌고래 중심점 그리기 (레이어 4)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw4.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=outline_color, outline=outline_color)

    # 레이어 2a: 50m 원 그리기
    if dolphins:
        for boat in boats:
            x1, y1, x2, y2, id, ship_speed = boat
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            circle_color_50m = hex_to_rgba(COLORS["around_circle_50m"])

            draw2a.ellipse([center_x - px_50m, center_y - px_50m, center_x + px_50m, center_y + px_50m], 
                           outline=circle_color_50m, width=2, fill=circle_color_50m)

    # 레이어 2b: 300m 원 그리기
    if dolphins:
        for boat in boats:
            x1, y1, x2, y2, id, ship_speed = boat
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            circle_color_300m = hex_to_rgba(COLORS["around_circle_300m"])

            draw2b.ellipse([center_x - px_300m, center_y - px_300m, center_x + px_300m, center_y + px_300m], 
                           outline=circle_color_300m, width=2, fill=circle_color_300m)

    # 레이어 3: 가장 가까운 선박과 돌고래 연결 및 거리 표시
    if boats and dolphins:
        min_distance = float('inf')
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

            # Check if distance is less than or equal to 50m
            if min_distance * input_GSD <= 50:
                # Change colors based on the distance being less than or equal to 50m
                outline_color = hex_to_rgba(COLORS["boat_outline_50m"])
                fill_color = hex_to_rgba(COLORS["boat_fill_50m"])
                line_color = hex_to_rgba(COLORS["line_color_50m"])
                text_bg_color = hex_to_rgba(COLORS["text_bg_50m"])
            else:
                # Use default colors
                line_color = hex_to_rgba(COLORS["line_color"])
                text_bg_color = hex_to_rgba(COLORS["text_bg_default"])

            # 레이어 3 생성 및 그리기
            layer3 = Image.new("RGBA", frame.size)
            draw3 = ImageDraw.Draw(layer3, 'RGBA')
            draw_dashed_line(draw3, boat_center, dolphin_center, dash_length=10, color=line_color, width=2)

            # 거리 텍스트 그리기
            distance_text = f"{min_distance * input_GSD:.1f}m"
            mid_point = ((boat_center[0] + dolphin_center[0]) // 2, (boat_center[1] + dolphin_center[1]) // 2)
            text_bbox = draw3.textbbox((0, 0), distance_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3

            draw3.rectangle([mid_point[0] - text_width // 2, mid_point[1] - text_height // 2, mid_point[0] + text_width // 2, mid_point[1] + text_height // 2], fill=text_bg_color)
            draw3.text((mid_point[0] - text_width // 2, mid_point[1] - text_height // 2), distance_text, font=font, fill=(255, 255, 255))

            # 레이어 3과 레이어 4 합성
            combined = Image.alpha_composite(layer3, layer4)
    else:
        combined = layer4

    # 레이어 2a, 2b와 합성
    combined = Image.alpha_composite(layer2a, combined)
    combined = Image.alpha_composite(layer2b, combined)

    # 최종적으로 모든 레이어와 원본 이미지를 합성
    final_image = Image.alpha_composite(base_frame, combined)
    return final_image.convert("RGB")  # 최종 이미지는 RGB로 변환하여 저장

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
        
        current_gsd_speed = gsd_speed_data[gsd_speed_data['frame_idx'] == frame_count]
        input_GSD = current_gsd_speed.iloc[0]['input_GSD'] if not current_gsd_speed.empty else 0.033962
        px_50m = int(50 / input_GSD) if input_GSD != 0 else 0
        px_300m = int(300 / input_GSD) if input_GSD != 0 else 0

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        final_image = draw_combined_layers(pil_image, bboxes, classes, ids, font, px_50m, px_300m, gsd_speed_data, frame_count, input_GSD)
        
        # 최종 이미지를 저장
        output_frame_path = os.path.join(output_dir, f'frame_{str(frame_count).zfill(6)}.jpg')
        final_image.save(output_frame_path)
        
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
