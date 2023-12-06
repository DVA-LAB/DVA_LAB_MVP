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
    output_img, output_mask, output_list = ad_slice_inference(request_body.frame_path, slices_path, output_path) # 설정 필요
    return output_img, output_mask, output_list

def ad_slice_inference(frame_path, slices_path, output_path):
    config = get_configurable_parameters("efficient_ad")
    config.trainer.resume_from_checkpoint = os.path.join(add_path, 'services', 'weights', 'model.ckpt')
    slice_frame = slicing(frame, patch_size, overlap)

    efficient_ad = get_model(config)
    callbacks = get_callbacks(config)
    trainer = Trainer(callbacks=callbacks, **config.trainer)

    transform_config = (
        config.dataset.transform_config.eval
        if "transform_config" in config.dataset.keys()
        else None
    )
    
    image_size = (patch_size*resize_rate, patch_size*resize_rate)
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
    patch_size = 512   # 최종적으로는 SAHI에서 적용된 값을 그대로 받아오도록 수정
    overlap = 0.5      # 
    resize_rate = 2

    folder_path = slices_path
    file_paths = sorted(glob.glob(os.path.join(folder_path, '*')))  

    # SHAI file명: 'filename_0000n_*.png'라고 가정
    grouped_files = {k: list(g) for k, g in groupby(file_paths, key=lambda x: int(x.split('_')[1]))}

    output_list = []
    for frame_number, slc_files in grouped_files.items():

        inf = []
        for slice in slc_files :
            dataset = InferenceDataset(
                slice, 
                image_size=tuple(config.dataset.image_size), 
                transform=transform  # type: ignore
                )
            dataloader = DataLoader(dataset)

            result = trainer.predict(model=efficient_ad, dataloaders=[dataloader])
            pred_mask = result[0]["pred_masks"][0]
            inf.append(pred_mask)

        ''' merge slices ''' 
        merge_result = merge_tensors_max(inf, h, w, resize_rate, patch_size, overlap)    # -> torch.Tensor
        output_t = merge_result.squeeze().numpy()

        ''' original resizing '''
        original_size = (w, h)
        resized_result = cv2.resize(output_t, original_size)

        ''' output '''
        v = mark_boundaries(frame_img, resized_result, color=(1, 0, 0), mode="thick")
        output_img = (v * 255).astype(np.uint8)    # -> numpy.ndarray
        output_mask = (resized_result * 255).astype(np.uint8)    # -> numpy.ndarray

        mask_contours, _ = cv2.findContours(output_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        output_bbox = []    # -> list (x, y, w, h)
        for contour in mask_contours:
            x, y, w, h = cv2.boundingRect(contour)
            class_id = 1
            pred_score = 1  # 수정 예정
            output_bbox.append((frame_number, class_id, x, y, w, h, pred_score))
        output_list.append(output_bbox) 

    save_path = output_path

    with open(save_path, 'w') as f:
        for j in output_list[0]:
            frame_number, class_id, x, y, w, h, pred_score = j
            f.write(f"{frame_number},{class_id},{x},{y},{w},{h},{pred_score}\n")


    return output_img, output_mask, output_list



def ad_inference():
    config = get_configurable_parameters("efficient_ad")
    config.trainer.resume_from_checkpoint = "services/weights/model.ckpt"
    config.visualization.mode = "full"

    # api에 맞추어 frame 수정필요
    frame = "services/datasets/sample/002/0001.jpg"

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

    dataset = InferenceDataset(
        frame, image_size=tuple(config.dataset.image_size), transform=transform  # type: ignore
    )
    dataloader = DataLoader(dataset)

    result = trainer.predict(model=efficient_ad, dataloaders=[dataloader])

    img = result[0]["image"]  # torch.Tensor
    pred_boxes = result[0]["pred_boxes"][0].tolist()[0]  # list
    pred_scores = result[0]["pred_scores"][0].tolist()  # float
    # print(img, pred_boxes, pred_scores)

    return img, pred_boxes, pred_scores
