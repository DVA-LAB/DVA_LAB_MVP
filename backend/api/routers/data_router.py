import os
import shutil

from fastapi import (APIRouter, Depends, FastAPI, File, HTTPException,
                     UploadFile, status)
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(tags=["data"])


@router.post("/video/")
async def upload_video(file: UploadFile = File(...)):
    video_storage_path = os.path.join("test", "video_origin")
    os.makedirs(video_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(video_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.get("/video/")
async def get_video():
    video_storage_path = os.path.join("test", "video_origin")
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
    file_location = os.path.join(video_storage_path, videos[0])
    return FileResponse(file_location)


@router.post("/csv/")
async def upload_csv(file: UploadFile = File(...)):
    csv_storage_path = os.path.join("test", "csv")
    os.makedirs(csv_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(csv_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/srt/")
async def upload_srt(file: UploadFile = File(...)):
    srt_storage_path = os.path.join("test", "srt")
    os.makedirs(srt_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(srt_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
