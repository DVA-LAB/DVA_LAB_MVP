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


@router.get("/video/{filename}")
async def get_video(filename: str):
    video_storage_path = os.path.join("test", "video_origin")
    file_location = os.path.join(video_storage_path, filename)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="File not found")
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
