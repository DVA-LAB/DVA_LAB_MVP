import cv2
import numpy as np
import torch
from anomalib.config import get_configurable_parameters
from anomalib.data.inference import InferenceDataset
from anomalib.data.utils import InputNormalizationMethod, get_transforms
from anomalib.models import get_model
from anomalib.utils import slicing  # 추가
from anomalib.utils.callbacks import get_callbacks
from autologging import logged
from fastapi import APIRouter, Depends, status
from interface.request import SegRequest
from PIL import Image
from pytorch_lightning import Trainer
from torch.utils.data import DataLoader

router = APIRouter(tags=["anomaly"])


@router.post(
    "/anomaly/inference",
    status_code=status.HTTP_200_OK,
    summary="anomaly segmentation",
)
async def anomaly_inference(request_body: SegRequest):
    res_img, res_boxes, res_scores = ad_slice_inference(request_body.frame_path)
    return res_img, res_boxes, res_scores


def ad_slice_inference(frame_path):
    config = get_configurable_parameters("efficient_ad")
    config.trainer.resume_from_checkpoint = "services/weights/model.ckpt"
    config.visualization.mode = "full"

    frame = frame_path

    img_size = 1920
    slice_frame = slicing(frame, img_size)

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

    res_img, res_boxes, res_scores = [], [], []
    for i in range(len(slice_frame)):
        input_frame = slice_frame[i]
        t = transform(image=input_frame)["image"]
        dataloader = DataLoader(t)
        result = trainer.predict(model=efficient_ad, dataloaders=[dataloader])

        img = result[0]["image"]  # -> torch.Tensor
        pred_boxes = result[0]["pred_boxes"][0].tolist()  # -> list
        pred_scores = result[0]["pred_scores"][0].tolist()  # -> float
        # print(img, pred_boxes, pred_scores)

        res_img.append(img)
        res_boxes.append(pred_boxes)
        res_scores.append(pred_scores)

    """ merge_slices() 적용 예정 """

    return res_img, res_boxes, res_scores


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
