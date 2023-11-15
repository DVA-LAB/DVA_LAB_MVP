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
                "frame_path": 'test_frame_path'
            }
        }
