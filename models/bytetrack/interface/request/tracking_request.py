from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["TrackingRequest"]


@logged
class TrackingRequest(BaseModel):
    det_result_path: str = Field(..., description="detection result")
    result_path: str = Field(..., description="tracking result")

    class Config:
        schema_extra = {
            "example": {
                "det_result_path": "/home/dva4/DVA_LAB/backend/test/model/merged/result.txt",
                "result_path": "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt",
            }
        }
