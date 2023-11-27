from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import os
import shutil

router = APIRouter(tags=["data"])


@router.post("/video/")
async def upload_video(file: UploadFile = File(...)):
    video_storage_path = os.path.join('test', 'video_origin')
    os.makedirs(video_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(video_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.",
                "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/csv/")
async def upload_csv(file: UploadFile = File(...)):
    csv_storage_path = os.path.join('test', 'csv')
    os.makedirs(csv_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(csv_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.",
                "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


@router.post("/srt/")
async def upload_srt(file: UploadFile = File(...)):
    srt_storage_path = os.path.join('test', 'srt')
    os.makedirs(srt_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(srt_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.",
                "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
