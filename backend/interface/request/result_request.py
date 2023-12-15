from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["VisRequest", "VisRequestBev"]


@logged
class VisRequest(BaseModel):
    log_path: str
    input_dir: str
    output_video: str
    bbox_path: str
    set_merged_dolphin_center: bool = False

    class Config:
        schema_extra = {
            "example": {
                "log_path": "/home/dva4/dva/backend/test/sync_csv",
                "input_dir": "/home/dva4/dva/backend/test/frame_origin",
                "output_video": "/home/dva4/dva/backend/test/result/result.mp4",
                "bbox_path": "/home/dva4/dva/backend/test/model/tracking/result.txt",
                "set_merged_dolphin_center": False
            }
        }

@logged
class VisRequestBev(BaseModel):
    user_input: str = Field(..., description="user_input_save file")
    frame_path: str = Field(..., description="img_frame_save_path (folder)")
    tracking_result: str = Field(..., description="detection_result file")
    GSD_path: str = Field(..., description="original GSD file")

    class Config:
        schema_extra = {
            "example": {
                "user_input": "/home/dva4/dva/backend/test/input/user_input.txt",
                "frame_path": "/home/dva4/dva/backend/test/frame_origin",
                "tracking_result": "/home/dva4/dva/backend/test/model/tracking/result.txt",
                "GSD_path": "/home/dva4/dva/backend/test/GSD.txt",
            }
        }