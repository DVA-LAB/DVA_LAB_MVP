import glob
import os
import shutil

from fastapi import (APIRouter, Depends, FastAPI, File, HTTPException,
                     UploadFile, status)
from fastapi.responses import FileResponse, JSONResponse
from utils.log_sync.adjust_log import do_sync
from api.services.data_service import parse_videos_multithreaded

router = APIRouter(tags=["data"])

video_path = os.path.join("test", "video_origin")
frame_path = os.path.join("test", "frame_origin")
csv_path = os.path.join("test", "csv")
srt_path = os.path.join("test", "srt")
sync_path = os.path.join("test", "sync_csv")


@router.post("/video/")
async def upload_video(file: UploadFile = File(...)):
    os.makedirs(video_path, exist_ok=True)
    os.makedirs(frame_path, exist_ok=True)
    delete_files_in_folder(video_path)
    delete_files_in_folder(frame_path)
    try:
        file_location = os.path.join(
            video_path, lowercase_extensions(file.filename)
        )
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        # TODO@jh: frame parsing을 background task로 처리하는 경우, 다 parsing되기전에 사용자 요청이 오는 경우 처리가 힘들지만 먼가 방법 고안이 필요함
        parse_videos_multithreaded(video_path, frame_path)

        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.get("/video/")
async def get_video():
    video_storage_path = video_path
    try:
        videos = [
            f
            for f in os.listdir(video_storage_path)
            if os.path.isfile(os.path.join(video_storage_path, f))
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error accessing video storage: {e}"
        )
    if not videos or len(videos) > 1:
        return JSONResponse(
            status_code=404,
            content={"message": "Video not found or multiple videos present"},
        )
    file_location = os.path.join(video_storage_path, lowercase_extensions(videos[0]))
    return FileResponse(file_location)

@router.get("/frame/{frame_number}")
async def get_frame(frame_number: int):
    try:
        frames = glob.glob(os.path.join(frame_path, '*.jpg'))
        image_path = [x for x in frames if int(x.split('_')[-1].split('.')[0])==frame_number]
        if not len(image_path):
            return JSONResponse(status_code=404, content={"message": "Frame not found"})
        return FileResponse(image_path[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing frame: {e}")

@router.post("/csv/")
async def upload_csv(file: UploadFile = File(...)):
    csv_storage_path = csv_path
    os.makedirs(csv_storage_path, exist_ok=True)
    delete_files_in_folder(csv_storage_path)
    try:
        file_location = os.path.join(
            csv_storage_path, lowercase_extensions(file.filename)
        )
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/srt/")
async def upload_srt(file: UploadFile = File(...)):
    srt_storage_path = srt_path
    os.makedirs(srt_storage_path, exist_ok=True)
    delete_files_in_folder(srt_storage_path)
    try:
        file_location = os.path.join(
            srt_storage_path, lowercase_extensions(file.filename)
        )
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/sync/")
async def sync_log():
    os.makedirs(sync_path, exist_ok=True)
    try:
        do_sync(video_path, csv_path, srt_path, sync_path)
        return {"message": "synchronized csv saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during file synchronization: {e}"
        )


def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, "*"))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)


def lowercase_extensions(file_name):
    name, extension = os.path.splitext(file_name)
    new_file_name = name + extension.lower()
    return new_file_name

@router.delete("/reset/")
async def reset_data():
    try:
        delete_files_in_folder(video_path)
        delete_files_in_folder(frame_path)
        delete_files_in_folder(csv_path)
        delete_files_in_folder(srt_path)
        delete_files_in_folder(sync_path)
        return {"message": "All data reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during data reset: {e}")
