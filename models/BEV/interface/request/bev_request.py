from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["BEV1", "BEV2"]


@logged
class BEV1(BaseModel):
    frame_num: int = Field(..., description="Frame number")
    frame_path: str = Field(..., description="Path to the frame image")
    csv_path: str = Field(..., description="Path to the CSV file")
    objects: list = Field(..., description="List of object parameters")
    realdistance: float = Field(..., description="Real distance value")
    dst_dir: str = Field(..., description="Destination directory for results")

    class Config:
        schema_extra = {
            "example": {
                "frame_num": 200,
                "frame_path": "api/services/Orthophoto_Maps/Data/frame_img/DJI_0119_200.png",
                "csv_path": "api/services/Orthophoto_Maps/Data/DJI_0119.csv",
                "objects": [None, None, None, 528.60, 537.70, 528.60 + 134.01, 537.70 + 258.51, None, -1, -1, -1],
                "realdistance": 20,
                "dst_dir": "api/services/Orthophoto_Maps/Data/result",
            }
        }

@logged
class BEV2(BaseModel):
    frame_num: int = Field(..., description="Frame number")
    frame_path: str = Field(..., description="Path to the frame image")
    csv_path: str = Field(..., description="Path to the CSV file")
    objects: list = Field(..., description="List of object parameters")
    dst_dir: str = Field(..., description="Destination directory for results")
    gsd: float = Field(..., description="Real distance value")

    class Config:
        schema_extra = {
            "example": {
                "frame_num": 200,
                "frame_path": "api/services/Orthophoto_Maps/Data/frame_img/DJI_0119_200.png",
                "csv_path": "api/services//Orthophoto_Maps/Data/DJI_0119.csv",
                "objects": [None, None, None, 528.60, 537.70, 134.01, 258.51, None, -1, -1, -1],
                "dst_dir": "api/services/Orthophoto_Maps/Data/result",
                "gsd": 0.00009362739603860218,

            }
        }