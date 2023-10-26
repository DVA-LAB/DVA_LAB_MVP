from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SamRequest", "SamResponse"]


@logged
class SamRequest(BaseModel):
    frame_count: int = Field(description="Frame count")
    bboxes: list[list[int]] = Field(description="List of bounding boxes")

    class Config:
        schema_extra = {
            "example": {
                "bboxes": [[10, 10, 100, 100]],
                "frame_count": 1
            }
        }


@logged
class SamResponse(BaseModel):
    masks: List[List[List[bool]]] = Field(description="List of 2D mask arrays")