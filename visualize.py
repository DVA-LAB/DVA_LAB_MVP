import cv2
import argparse
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from utils.extract_meta import extract_date_from_srt, extract_video_metadata
from ultralytics import YOLO
from PIL import Image


LEGAL_SPEED     = 50
LEGAL_DISTANCE  = 50
TARGET_SIZE     = (1200, 900)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--srt_path', type=str, default='data/DJI_0010.srt')
    parser.add_argument('--video_path', type=str, default='data/DJI_0010.mp4')
    parser.add_argument('--model_name', type=str, default='yolov8n.pt')
    parser.add_argument('--output_video', type=str, default='data/DJI_0010.AVI')
    args = parser.parse_args()
    
    dates = extract_date_from_srt(args.srt_path)
    model = YOLO(args.model_name)
    
    frame_count = -1
    frame_rate, total_frames, frame_width, frame_height = extract_video_metadata(args.video_path)
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(args.output_video, fourcc, frame_rate, (frame_width, frame_height))
    
    cap = cv2.VideoCapture(args.video_path)
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        frame = cv2.resize(frame, TARGET_SIZE)
        
        # 객체 탐지 결과를 추출합니다.
        results     = model(frame)[0]
        boxes       = results.boxes
        names       = results.names
        cls         = boxes.cls
        conf        = boxes.conf
        xywh        = boxes.xywh
        boats       = 0
        dolphins    = 0

        # 객체 추적 결과를 추출합니다. (구현 필요)
        max_ship_speed      = 0

        # 카메라 캘리브레이션 결과를 추출합니다. (구현 필요)
        nearest_distance    = 0

        # 대시보드 시각화를 위해 현재 프레임 좌측 상단에 흰색 배경을 추가합니다.
        background_color    = (255, 255, 255)
        background_width    = 400
        background_height   = 200
        background          = np.ones((background_height, background_width, 3), dtype=np.uint8) * background_color
        x_position          = 0
        y_position          = 0
        frame[y_position:y_position + background_height, x_position:x_position + background_width] = background

        # 한글 텍스트 시각화를 위해 폰트 설정과 CV2 → PIL 변환을 수행합니다.
        font    = ImageFont.truetype("data/font/NanumSquareRoundR.ttf", size=24)
        image   = Image.fromarray(frame)
        draw    = ImageDraw.Draw(image)

        # 현재 프레임에 bounding box 정보를 추가하고, 탐지된 선박과 돌고래의 수를 카운트합니다.
        for i in range(len(xywh)):
            x, y, w, h  = xywh[i]
            class_name    = names[cls[i].item()]
            conf_score    = round(conf[i].item(), 2)
            if class_name == "boat":
                boats += 1
                title = f"{class_name}({conf_score}), 0km/h"
            elif class_name == "dolphin":
                dolphins += 1
                title = f"{class_name}({conf_score})"
            else:
                title = ""

            x, y, w, h = x.item(), y.item(), w.item(), h.item()
            draw.rectangle(xy=(x, y, x+w, y+h), width=5, outline=(0, 255, 0))
            draw.text(xy=(x, y-50), text=title, font=font, align='left', fill=(0, 255, 0, 0))


        # 대시보드에 표시할 텍스트 정보를 생성합니다.
        if (LEGAL_DISTANCE > nearest_distance) or (LEGAL_SPEED < max_ship_speed):
            violation  = True
            font_color = (0, 0, 255, 0)
        else:
            violation  = False
            font_color = (0, 255, 0, 0)

        # 현재 프레임에 텍스트를 추가합니다.
        draw.text(xy=(10, 0),   text=f"촬영 일시: {dates[frame_count]}",    font=font, align='left', fill=font_color)
        draw.text(xy=(10, 30),  text=f"위반여부: {violation}",              font=font, align='left', fill=font_color)
        draw.text(xy=(10, 60),  text=f"최근접거리: {nearest_distance}m",    font=font, align='left', fill=font_color)
        draw.text(xy=(10, 90),  text=f"최고선박속도: {max_ship_speed}km/s", font=font, align='left', fill=font_color)
        draw.text(xy=(10, 120), text=f"선박 수: {boats}",                   font=font, align='left', fill=font_color)
        draw.text(xy=(10, 150), text=f"돌고래 수: {dolphins}",              font=font, align='left', fill=font_color)

        img = np.array(image)
        
        cv2.imshow(args.video_path, img)
        out.write(img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        
    cap.release()
    out.release()
    cv2.destroyAllWindows()