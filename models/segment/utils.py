import cv2
import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def preprocess_image(img_array, xml_path):
    # 이미지를 불러옵니다.
    image = img_array

    # XML 파일을 파싱합니다.
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 모든 'object' 태그를 찾습니다.
    for obj in root.findall('object'):
        # 'polygon' 태그를 찾습니다.
        polygon = obj.find('polygon')

        # 'polygon' 태그가 없는 경우 continue를 통해 넘어갑니다.
        if polygon is None:
            continue

        # 폴리곤 좌표를 추출합니다.
        points = []
        idx = 1
        while True:
            x = polygon.find(f'x{idx}')
            y = polygon.find(f'y{idx}')
            if x is None or y is None:
                break
            points.append([int(x.text), int(y.text)])
            idx += 1

        # 폴리곤 좌표를 numpy array로 변환합니다.
        points = np.array(points, np.int32)
        points = points.reshape((-1, 1, 2))

        # 폴리곤 영역을 검정색으로 칠합니다.
        cv2.fillPoly(image, [points], color=(0, 0, 0))

    return image


def return_masks_on_image(raw_image, masks, scores, bboxes):
    if len(masks.shape) == 4:
        masks = masks.squeeze()
    if scores.shape[0] == 1:
        scores = scores.squeeze()
    if scores.dim() == 0:
        scores = scores.unsqueeze(0)
    if len(masks.shape) == 2:
        masks = masks.unsqueeze(0)

    # 이미지를 numpy 배열로 변환
    raw_image_np = np.array(raw_image)
    for mask, score, bbox in zip(masks, scores, bboxes):
        mask = mask.cpu().detach().numpy().astype(np.uint8) * 255

        # 마스크를 원본 이미지 크기에 맞게 재조정
        mask = cv2.resize(mask, (raw_image_np.shape[1], raw_image_np.shape[0]))
        # 마스크를 RGB로 변환
        mask_rgb = np.stack([mask, np.zeros_like(mask), np.zeros_like(mask)], axis=2)
        # 마스크 적용: 원본 이미지에 마스크를 추가합니다.
        raw_image_np = cv2.addWeighted(raw_image_np, 1, mask_rgb, 0.7, 0)

        x1, y1, x2, y2 = map(int, bbox)
        # 원본 이미지에 bbox를 그립니다.
        cv2.rectangle(raw_image_np, (x1, y1), (x2, y2), (255, 0, 0), 3)

    return raw_image_np


def is_rgb_or_bgr(image):
    # 이미지의 각 채널별 평균값을 계산합니다.
    B, G, R = cv2.split(image)
    B_avg = np.average(B)
    G_avg = np.average(G)
    R_avg = np.average(R)

    # R 채널의 평균이 B 채널의 평균보다 큰 경우, 이미지는 RGB로 간주합니다.
    if R_avg > B_avg:
        return "RGB"
    else:
        return "BGR"