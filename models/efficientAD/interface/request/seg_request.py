from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SegRequest"]


@logged
class SegRequest(BaseModel):
    frame_path: str = Field(description="Frame path")
    slices_path: str = Field(description="Slices path")
    output_path: str = Field(description="Test path")

    class Config:
        schema_extra = {
            "example": {
                "frame_path": '/home/dva4/DVA_LAB/backend/test/frame_origin',
                "slices_path": '/home/dva4/DVA_LAB/backend/test/model/sliced',
                "output_path": '/home/dva4/DVA_LAB/backend/test/model/segment'
            }
        }
