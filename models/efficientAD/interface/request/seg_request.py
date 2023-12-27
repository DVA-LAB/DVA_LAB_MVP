from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SegRequest"]


@logged
class SegRequest(BaseModel):
    frame_path: str = Field(description="Frame path")

    class Config:
        schema_extra = {
            "example": {
                "frame_path": '/home/dva4/DVA_LAB/backend/test/frame_origin/DJI_0119_30_00000.jpg',
                "slices_path": '',
                "output_path": '',
            }
        }
