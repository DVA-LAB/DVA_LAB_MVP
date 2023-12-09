import os
import cv2
import numpy as np
from fastapi import APIRouter, Depends, status

from api.services.Orthophoto_Maps.main_dg import *
from interface.request.bev_request import BEV1, BEV2

router = APIRouter(tags=["bev"])


@router.post(
    "/bev1",
    status_code=status.HTTP_200_OK,
    summary="first dev",
)
async def bev_1(body: BEV1):
    result = BEV_1(body.frame_num, body.frame_path, body.csv_path, body.objects, body.realdistance, body.dst_dir)
    # result_flg, img_dst, objects, pixel_size, gsd = result
    return result

@router.post(
    "/bev2",
    status_code=status.HTTP_200_OK,
    summary="second dev",
)
async def bev_2(body: BEV2):
    result = BEV_2(body.frame_num, body.frame_path, body.csv_path, body.objects, body.dst_dir, body.gsd)
    # result_flg, img_dst, objects, pixel_size, gsd = result
    return result