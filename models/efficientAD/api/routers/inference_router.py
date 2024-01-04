import os
import sys
script_path = os.path.abspath(__file__)
add_path = os.path.dirname(os.path.dirname(script_path))
target_directory = os.path.join(add_path, 'services', 'src')
absolute_target_directory = os.path.abspath(target_directory)
if absolute_target_directory not in sys.path:
    sys.path.append(absolute_target_directory)

import cv2
import numpy as np
import torch
from itertools import groupby

from anomalib.config import get_configurable_parameters
from anomalib.data.inference import InferenceDataset
from anomalib.data.utils import InputNormalizationMethod, get_transforms
from anomalib.models import get_model

from anomalib.utils import slicing, merge_tensors_max  # 추가
from anomalib.utils.callbacks import get_callbacks
from autologging import logged
from fastapi import APIRouter, Depends, status
from interface.request import SegRequest
from PIL import Image
from pytorch_lightning import Trainer
from torch.utils.data import DataLoader
from skimage.segmentation import mark_boundaries

router = APIRouter(tags=["anomaly"])


@router.post(
    "/anomaly/inference",
    status_code=status.HTTP_200_OK,
    summary="anomaly segmentation",
)
async def anomaly_inference(request_body: SegRequest):
    """
        이상탐지 모델에 인퍼런스를 수행한 결과를 반환합니다.

        Args
            - request_body
                - request_body.frame_path (str): 이상탐지를 수행할 프레임 파일경로
                - request_body.slices_path (str): 이상탐지를 수행할 프레임 파일이 슬라이싱된 디렉터리 경로
                - request_body.output_path (str): 이상탐지 결과가 저장될 파일경로

        Return
            - output_img (np.ndarray): 이상탐지를 수행한 결과 이미지
            - output_mask (?): ?
            - output_list (list): N x [frame_number, class_id, x1, y1, w1, h1, anomaly_score]
    """

    output_img, output_mask, output_list = ad_slice_inference(request_body.frame_path, request_body.slices_path, request_body.output_path, request_body.patch_size, request_body.overlap_ratio) # 설정 필요
    return output_img, output_mask, output_list

def ad_slice_inference(frame_path, slices_path, output_path, patch_size, overlap_ratio):
    """
        이상탐지 모델에 인퍼런스를 수행한 결과를 반환합니다.

        Args
            - frame_path (str): 이상탐지를 수행할 프레임 파일경로
            - slices_path (str): 이상탐지를 수행할 프레임 파일이 슬라이싱된 디렉터리 경로
            - output_path (str): 이상탐지 결과가 저장될 파일경로

        Return
            - output_img (np.ndarray): 이상탐지를 수행한 결과 이미지
            - output_mask (?): ?
            - output_list (list): N x [frame_number, class_id, x1, y1, w1, h1, anomaly_score]
    """
    
    config = get_configurable_parameters("efficient_ad")
    config.trainer.resume_from_checkpoint = os.path.join(add_path, 'services', 'weights', 'model.ckpt')

    efficient_ad = get_model(config)
    callbacks = get_callbacks(config)
    trainer = Trainer(callbacks=callbacks, **config.trainer)

    transform_config = (
        config.dataset.transform_config.eval
        if "transform_config" in config.dataset.keys()
        else None
    )
    
    image_size = (config.dataset.image_size[0], config.dataset.image_size[1])
    center_crop = config.dataset.get("center_crop")
    if center_crop is not None:
        center_crop = tuple(center_crop)
    normalization = InputNormalizationMethod(config.dataset.normalization)
    transform = get_transforms(
        config=transform_config,
        image_size=image_size,
        center_crop=center_crop,
        normalization=normalization,
    )

    frame = frame_path
    frame_img = cv2.imread(frame)
    
    h, w = frame_img.shape[:2]
    # Replace local variable(request body input value)
    patch_size = patch_size
    overlap = overlap_ratio
    step = 1 - overlap
    resize_rate = 1

    # SHAI folder : sahi_path > frame > slices('filename_0000n_*.png'라고 가정)
    sahi_path = slices_path
        
    output_list = []
    for frame_number, frame_folder in enumerate(sorted(os.listdir(sahi_path))):
        frame_path = os.path.join(sahi_path, frame_folder)

        inf = []
        output_bbox = []
        dataset = InferenceDataset(
            frame_path, 
            image_size=tuple(config.dataset.image_size), 
            transform=transform  # type: ignore
            )
        dataloader = DataLoader(dataset)
        result = trainer.predict(model=efficient_ad, dataloaders=[dataloader])

        for i in range(len(result)):
            inf.append(result[i]["anomaly_maps"][0])

        ''' merge slices ''' 
        merge_result = merge_tensors_max(inf, h, w, resize_rate, patch_size, step)    # -> torch.Tensor
        
        ''' anomaly map -> mask '''
        anomaly_map = merge_result.squeeze()
        mask: np.ndarray = np.zeros_like(anomaly_map).astype(np.uint8)
        mask[anomaly_map > 0.5] = 1
        kernel = morphology.disk(4)
        mask = morphology.opening(mask, kernel)
        mask *= 255

        ''' score map '''
        score_map = anomaly_map.clone()
        score_map[anomaly_map <= 0.5] = 0
        score_map = score_map.numpy()
        
        ''' output '''
        output_mask = cv2.resize(mask, (w, h))
        output_score_mask = cv2.resize(score_map, (w, h))
        mask_contours, _ = cv2.findContours(output_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in mask_contours:
            x1, y1, w1, h1 = cv2.boundingRect(contour)
            class_id = 1
            
            ''' anomaly score '''
            anomaly_region = output_score_mask[y1:y1+h1, x1:x1+w1]
            anomaly_score = np.mean(anomaly_region[anomaly_region != 0])
            
            output_bbox.append((frame_number, class_id, x1, y1, w1, h1, anomaly_score))
        output_list.append(output_bbox) 

        ''' visualization '''    # 정상구동 확인용
        background_image = np.zeros_like(output_mask)
        background_image[output_mask == 255] = 128
        for bbox in output_bbox:
            _, _, x2, y2, w2, h2, _ = bbox
            cv2.rectangle(background_image, (x2, y2), (x2 + w2, y2 + h2), (255, 255, 255), 2)  
        #cv2.imwrite(f"results/output_bbox_{frame_number}.jpg", background_image)

        v = mark_boundaries(frame_img, mask, color=(1, 0, 0), mode="thick")
        output_img = (v * 255).astype(np.uint8)    # -> numpy.ndarray
        #cv2.imwrite(f"results/output_img_{frame_number}.jpg", output_img)

    ''' save output '''
    save_path = output_path
    with open(save_path, 'w') as f:
        for j in output_list[0]:
            frame_number, class_id, xx, yy, ww, hh, anomaly_score = j
            f.write(f"{frame_number},{class_id},{xx},{yy},{ww},{hh},{anomaly_score}\n")


    return output_img, output_mask, output_list


