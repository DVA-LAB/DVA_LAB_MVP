from autologging import logged
from fastapi import APIRouter, Depends, status
from interface.request import ModelRequest
from utils.merge_bboxes import read_file, read_csv_file, match_and_ensemble, plot_detections
import requests
import json
import glob
import os

router = APIRouter(tags=["model"])


use_segment = False
@router.post(
    "/inference",
    status_code=status.HTTP_200_OK,
    summary="AI model run",
)
async def model_inference(body: ModelRequest):
    img_path, csv_path, sliced_path = inference_detection(body.frame_path, body.detection_save_path, body.sliced_path)
    if use_segment:
        # TODO@jh: check segment service
        for frame in glob.glob(os.path.join(body.frame_path, '*.jpg')):
            frame_path, slices_path, output_path = inference_segmentation(frame, body.sliced_path, output_path)

    # merge function test
    anomaly_detection_output = read_csv_file(csv_path)
    detection_output = read_csv_file(csv_path)

    os.makedirs(body.output_merge_path, exist_ok=True)
    delete_files_in_folder(body.output_merge_path)

    output = match_and_ensemble(anomaly_detection_output, detection_output, use_anomaly=True,
                                output_file=os.path.join(body.output_merge_path, 'result.txt'))
    # TODO@jh: change to plt save function
    # plot_detections(anomaly_detection_output, detection_output, output)

    # TODO@jh: tracking
    # TODO@jh: visualization
    return output


def inference_detection(img_path, csv_path, sliced_path):
    url = "http://localhost:8002/sahi/inference"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {
        "img_path": img_path,
        "csv_path": csv_path,
        "sliced_path": sliced_path
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()


def inference_segmentation(frame_path, slices_path, output_path):
    url = "http://localhost:8003/anomaly/inference"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {
        "frame_path": frame_path,
        "slices_path": slices_path,
        "output_path": output_path
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*"))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)