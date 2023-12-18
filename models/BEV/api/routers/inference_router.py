import os
import shutil

import cv2
import numpy as np
from api.services.Orthophoto_Maps.main_dg import *
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException
from interface.request.bev_request import BEV1, BEV2

router = APIRouter(tags=["bev"])


@router.post(
    "/bev1",
    status_code=status.HTTP_200_OK,
    summary="first dev",
)
async def bev_1(body: BEV1):
    try:
        result = BEV_UserInputFrame(
            body.frame_num,
            body.frame_path,
            body.csv_path,
            body.objects,
            body.realdistance,
            body.dst_dir,
        )
        return result
    except:
        raise HTTPException(
            status_code=500, detail="BEV conversion failed or no image path returned"
        )


@router.post(
    "/bev2",
    status_code=status.HTTP_200_OK,
    summary="second dev",
)
async def bev_2(body: BEV2):
    try:
        result = BEV_FullFrame(
            body.frame_num,
            body.frame_path,
            body.csv_path,
            body.objects,
            body.dst_dir,
            body.gsd,
        )
        return result
    except:
        raise HTTPException(
            status_code=500, detail="BEV conversion failed or no image path returned"
        )


# @router.post(
#     "/bev2_all",
#     status_code=status.HTTP_200_OK,
#     summary="second dev for all frames",
# )
# async def bev_vid(objects):
#     frame_path = "/home/dva4/DVA_LAB/backend/test/frame_origin"
#     csv_path = "/home/dva4/DVA_LAB/backend/test/csv"
#     dst_dir = "/home/dva4/DVA_LAB/backend/test/result/bev"
#     frame_list = glob.glob(os.path.join(frame_path, "*.jpg"))
#     gsd_path = "/home/dva4/DVA_LAB/backend/test/GSD.txt"
#
#     try:
#         # Read GSD value from file
#         gsd = read_float_from_file(gsd_path)
#         if gsd is None:
#             raise ValueError("Invalid or missing GSD value")
#
#         # Process each frame
#         frame_list = glob.glob(os.path.join(frame_path, "*.jpg"))
#         for frame in frame_list:
#             frame_num = extract_frame_number(frame)
#             result = BEV_FullFrame(
#                 frame_num, frame_path, csv_path, objects, dst_dir, gsd
#             )
#
#             # Check if BEV_2 was successful and extract necessary data
#             if result.rst == 0:
#                 # You may need to define or calculate the following paths
#                 log_path = "/home/dva4/DVA_LAB/backend/test/sync_csv/sync_log.csv"
#                 video_path = glob.glob("/home/dva4/DVA_LAB/backend/test/video_origin/*")
#                 output_video = "/home/dva4/DVA_LAB/backend/test/result"
#                 bbox_path = "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt"
#
#                 # Prepare the request object for visualize
#
#                 vis_request = show_result(
#                     log_path=log_path,
#                     video_path=video_path,
#                     output_video=output_video,
#                     bbox_path=bbox_path,
#                 )
#
#                 # Call visualize
#                 visualize_result = await show_result(vis_request)
#
#                 return visualize_result
#             else:
#                 # Handle failure cases
#                 return {
#                     "error": "BEV_2 processing failed with result flag: {}".format(
#                         result.rst
#                     )
#                 }
#
#         return {"message": "All frames processed successfully"}
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


def extract_frame_number(filename):
    # Extract the part of the filename without the directory and extension
    base_name = filename.split("/")[-1]  # Get the last part of the path
    name_without_extension = base_name.split(".")[0]  # Remove the extension

    # The frame number is after the last underscore
    frame_number = name_without_extension.split("_")[-1]

    # Convert the frame number to an integer
    return int(frame_number)


def read_float_from_file(file_path):
    with open(file_path, "r") as file:
        # Read the first line of the file
        line = file.readline()

        # Convert the line to a float
        try:
            return float(line.strip())
        except ValueError:
            print("Error: The file does not contain a valid float number.")
            return None
