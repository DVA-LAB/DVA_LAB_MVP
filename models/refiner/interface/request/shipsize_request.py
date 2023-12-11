from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["ShipRequest"]


@logged
class ShipRequest(BaseModel):
    user_input: str = Field(..., description="user_input_save_path (folder)")
    frame_path: str = Field(..., description="img_frame_save_path (folder)")
    tracking_result: str = Field(..., description="detection_result")

    class Config:
        schema_extra = {
            "example": {
                "user_input": "/home/dva4/dva/backend/test/input",
                "frame_path": "/home/dva4/dva/backend/test/frame_origin",
                "tracking_result": "/home/dva4/dva/backend/test/model/tracking/result.txt",
            }
        }
