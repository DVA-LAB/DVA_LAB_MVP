import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from utils.extract_meta import get_file_path, extract_exif

LEGAL_DISTANCE = 50

if __name__ == "__main__":
    filepaths = get_file_path(directory='data')
    for filepath in filepaths:
        # 이미지를 로드합니다.
        frame = cv2.imread(filepath, cv2.IMREAD_COLOR)
        
        # 메타 데이터를 추출합니다.
        exif_table          = extract_exif(filepath)
        datetime            = exif_table['DateTime']
        image_width         = exif_table['ExifImageWidth']
        image_height        = exif_table['ExifImageHeight']

        # 객체 탐지 결과를 추출합니다.
        boxes           = [['ship', 0.97, 200, 400, 600, 800], ['dolphin', 0.99, 1200, 400, 1000, 600]]
        count_ship      = 0
        count_dolphin   = 0
        
        for box in boxes:
            if box[0] == 'ship':
                count_ship += 1
            elif box[0] == 'dolphin':
                count_dolphin += 1
        
        # 객체 추적 결과를 추출합니다.
        ship_speed          = [10, 20, 30]
        max_ship_speed      = max(ship_speed)
        
        # 카메라 캘리브레이션 결과와 이를 가공한 정보를 추출합니다.
        nearest_distance    = 10
        
        # 대시보드에 표시할 정보를 생성합니다.
        text_creation_time  = f'촬영 일시:\t{datetime}\n'
        text_ship_speed     = f"최대 선박 속도:\t{max_ship_speed}km/s"
        text_distance       = f"최근접 거리:\t{nearest_distance}m"
        text_count_ship     = f"선박 수:\t{count_ship}"
        text_count_dolphin  = f"돌고래 수:{count_dolphin}"
        
        if LEGAL_DISTANCE > max_ship_speed:
            text_violation = "위반여부:\tTrue"
            font_color     = (0, 0, 255)  # Blue, Green, Red
        else:
            text_violation = "위반여부:\tFalse"
            font_color     = (0, 255, 0)

        # 흰색 배경을 생성합니다.
        background_color    = (255, 255, 255)
        background_width    = 800
        background_height   = 330
        background          = np.ones((background_height, background_width, 3), dtype=np.uint8) * background_color

        # 이미지 위에 흰색 배경을 추가합니다.
        x_position = 0
        y_position = 0
        frame[y_position:y_position + background_height, x_position:x_position + background_width] = background
        
        # 이미지에 텍스트를 추가합니다.
        font    = ImageFont.truetype("data/nanum-square/NanumSquareR.ttf", size=50)
        image   = Image.fromarray(frame)
        draw    = ImageDraw.Draw(image)
        
        draw.text(xy=(10, 0),   text=text_creation_time, font=font, align='left', fill=(0, 0, 255, 0))
        draw.text(xy=(10, 50),  text=text_violation,     font=font, align='left', fill=(0, 0, 255, 0))
        draw.text(xy=(10, 100), text=text_distance,      font=font, align='left', fill=(0, 0, 255, 0))
        draw.text(xy=(10, 150), text=text_ship_speed,    font=font, align='left', fill=(0, 0, 255, 0))
        draw.text(xy=(10, 200), text=text_count_ship,    font=font, align='left', fill=(0, 0, 255, 0))
        draw.text(xy=(10, 250), text=text_count_dolphin, font=font, align='left', fill=(0, 0, 255, 0))
        
        # bounding box를 시각화합니다.
        for box in boxes:
            class_name, conf_score, x, y, w, h = box
            if class_name == "ship":
                title = f"{class_name}({conf_score}), {10}km/h"
            elif class_name == "dolphin":
                title = f"{class_name}({conf_score})"
            draw.rectangle(xy=(x, y, x+w, y+h), width=5, outline=(0, 0, 255))
            draw.text(xy=(x, y-50), text=title, font=font, align='left', fill=(0, 0, 255, 0))
        
        img = np.array(image)
        cv2.imshow(filepath, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()