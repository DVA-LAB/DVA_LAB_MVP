from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import os
import shutil

router = APIRouter(tags=["video"])


@router.post("/videos/")
async def create_video(file: UploadFile = File(...)):
    video_storage_path = "test_video"
    try:
        file_location = os.path.join(video_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.",
                "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")



