from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["VisRequest"]


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