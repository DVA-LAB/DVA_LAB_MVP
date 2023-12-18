from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SahiRequest"]


@logged
class SahiRequest(BaseModel):
    img_path: str 
    csv_path: str
    sliced_path: str

    class Config:
        schema_extra = {
            "example": {
                "img_path": "/home/dva4/DVA_LAB/backend/test/frame_origin",
                "csv_path": "/home/dva4/DVA_LAB/backend/test/model/detection/result.csv",
                "sliced_path": "/home/dva4/DVA_LAB/backend/test/model/sliced",
            }
        }

