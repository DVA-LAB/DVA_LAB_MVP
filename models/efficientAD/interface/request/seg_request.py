from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SegRequest"]


@logged
class SegRequest(BaseModel):
    """
        이상탐지 요청 수행에 필요한 프레임 변수 경로를 포함하는 클래스입니다.

        Attributes
            - frame_path (str): 프레임 경로
    """

    frame_path: str = Field(description="Frame path")
    slices_path: str = Field(description="Slices path")
    output_path: str = Field(description="Test path")
    patch_size: int = Field(default=1024, description="Sahi patch size")
    overlap_ratio: float = Field(default= 0.2, description="Sahi overlap ratio")

    class Config:
        schema_extra = {
            "example": {
                "frame_path": '/home/dva4/DVA_LAB/backend/test/frame_origin',
                "slices_path": '/home/dva4/DVA_LAB/backend/test/model/sliced',
                "output_path": '/home/dva4/DVA_LAB/backend/test/model/segment',
                "patch_size": '1024',
                "overlap_ratio": '0.2'
            }
        }
