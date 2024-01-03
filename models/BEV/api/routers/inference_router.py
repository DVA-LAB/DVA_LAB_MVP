import os
import shutil

import cv2
import numpy as np
from models.BEV.api.services.Orthophoto_Maps.main_dg import *
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException
from models.BEV.interface.request.bev_request import BEV1, BEV2

router = APIRouter(tags=["bev"])


@router.post(
    "/bev1",
    status_code=status.HTTP_200_OK,
    summary="first dev",
)
async def bev_1(body: BEV1):
    """
        원본 프레임에 BirdEyeView(BEV) 시각화를 수행합니다.
        
        Args
            - body
                - body.frame_num (int): BEV 시각화를 적용하고자 하는 프레임 번호
                - body.frame_path (str): BEV 시각화를 적용하고자 하는 번호의 프레임 파일 경로
                - body.csv_path (str): 동기화된 csv 파일 경로
                - body.objects (list): 객체추적 결과입니다. ex) [frame_id, track_id, label, bbox, score, -1, -1, -1]
                - body.realdistance (float): 실제 거리 값
                - body.dst_dir (str): BEV 시각화가 적용된 프레임이 저장될 디렉터리 경로

        Raise
            - fastapi.HTTPException: BEV 변환에 실패했을 경우 서버 에러(500)를 발생

        Return
            - result (tuple)
                - rst (int): BEV 변환 성공 여부
                - img_dst (str): BEV 적용한 이미지 경로
                - objects (list): BEV 상에서의 bbox로 정보로 변경된 객체추적 결과 ex) [frame_id, track_id, label, bbox, score, -1, -1, -1]
                - pixel_size (float): 한 픽셀당 실제 크기
                - gsd (float): GSD 값
    """

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
        raise HTTPException(status_code=500, detail="BEV conversion failed or no image path returned")


@router.post(
    "/bev2",
    status_code=status.HTTP_200_OK,
    summary="second dev",
)
async def bev_2(body: BEV2):
    """
        원본 프레임에 BirdEyeView(BEV) 시각화를 수행합니다.
        
        Args
            - body
                - body.frame_num (int): BEV 시각화를 적용하고자 하는 프레임 번호
                - body.frame_path (str): BEV 시각화를 적용하고자 하는 번호의 프레임 파일 경로
                - body.csv_path (str): 동기화된 csv 파일 경로
                - body.objects (list): 객체추적 결과 ex) [frame_id, track_id, label, bbox, score, -1, -1, -1]
                - body.realdistance (float): 실제 거리 값
                - body.dst_dir (str): BEV 시각화가 적용된 프레임이 저장될 디렉터리 경로

        Raise
            - HTTPException: BEV 변환에 실패했을 경우 서버 에러(500)를 발생시킵니다.

        Return
            - result (tuple)
                - rst (int): BEV 변환 성공 여부
                - img_dst (str): BEV 적용한 이미지 경로
                - objects (list): BEV 상에서의 bbox로 정보로 변경된 객체추적 결과 ex) [frame_id, track_id, label, bbox, score, -1, -1, -1]
                - pixel_size (float): 한 픽셀당 실제 크기
                - gsd (float): GSD 값
    """

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
        raise HTTPException(status_code=500, detail="BEV conversion failed or no image path returned")


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
    """
        파일명에서 프레임 번호를 추출합니다.

        Args
            - filename (str): 프레임 번호를 추출할 파일명

        Return
            - frame_number (int): 프레임 번호
    """

    # Extract the part of the filename without the directory and extension
    base_name = filename.split("/")[-1]  # Get the last part of the path
    name_without_extension = base_name.split(".")[0]  # Remove the extension

    # The frame number is after the last underscore
    frame_number = name_without_extension.split("_")[-1]

    # Convert the frame number to an integer
    return int(frame_number)


def read_float_from_file(file_path):
    """
        파일에 기재된 float 값을 읽어 반환합니다.

        Args
            - file_path (str): float 값이 작성된 파일 경로

        Return
            - float type의 값이 반환
    """

    with open(file_path, "r") as file:
        # Read the first line of the file
        line = file.readline()

        # Convert the line to a float
        try:
            return float(line.strip())
        except ValueError:
            print("Error: The file does not contain a valid float number.")
            return None
