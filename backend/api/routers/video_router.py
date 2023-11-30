from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import cv2

router = APIRouter(tags=["video"])


@router.post("/videos/")
async def create_video(file: UploadFile = File(...)):
    video_storage_path = "test_video"
    os.makedirs(video_storage_path, exist_ok=True)
    try:
        file_location = os.path.join(video_storage_path, file.filename)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"message": "File saved successfully.",
                "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

@router.get("/videos/{filename}/")
async def get_video(filename: str):
    video_storage_path = "test_video"
    file_location = os.path.join(video_storage_path, filename)
    if not os.path.isfile(file_location):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_location)

@router.post("/bev/{filename}")
async def create_bev_image(filename: str, file: UploadFile = File(...)):
    frame_storage_path = "extracted_frames"
    os.makedirs(frame_storage_path, exist_ok=True)
    frame_path = os.path.join(frame_storage_path, filename)

    # Save the uploaded frame
    with open(frame_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # TODO: Implement BEV conversion module using the saved frame

    return JSONResponse(content={"message": "Frame uploaded and BEV conversion started.", "framePath": frame_path})

# def mount_static_files(app: FastAPI):
#     app.mount("/extracted_frames", StaticFiles(directory="extracted_frames"), name="extracted_frames")

@router.get("/extracted_frames/{frame_name}")
async def get_frame(frame_name: str):
    frame_path = os.path.join("extracted_frames", frame_name)
    print(frame_path)
    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(frame_path)
