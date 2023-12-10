from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["ModelRequest"]


@logged
class ModelRequest(BaseModel):
    frame_path: str
    detection_save_path: str
    sliced_path: str
    output_merge_path: str

    class Config:
        schema_extra = {
            "example": {
                "frame_path": "/home/dva4/dva/backend/test/frame_origin",
                "detection_save_path": "/home/dva4/dva/backend/test/model/detection/result.csv",
                "sliced_path": "/home/dva4/dva/backend/test/model/sliced",
                "output_merge_path": "/home/dva4/dva/backend/test/model/merged",
            }
        }
