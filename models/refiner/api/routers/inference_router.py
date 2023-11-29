import cv2
import numpy as np
from fastapi import APIRouter, Depends, status

from api.services import Refiner
from interface.request import DataRequest

router = APIRouter(tags=["data"])


@router.post(
    "/refinement",
    status_code=status.HTTP_200_OK,
    summary="bbox refinement with SAM",
)
async def inference(request_body: DataRequest):
    refiner = Refiner("cuda")

    imgs_path = request_body.img_path
    json_path = request_body.json_file

    updated_data = refiner.do_refine(json_path, imgs_path)
    refiner.save_update(updated_data, f"refined_{json_path}")
