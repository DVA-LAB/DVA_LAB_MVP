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
                "frame_num": 1038,
                "frame_path": "/home/dva4/DVA_LAB/backend/test/frame_origin/DJI_0149_01038.jpg",
                "csv_path": "/home/dva4/DVA_LAB/backend/test/sync_csv/sync_log.csv",
                "objects": [None, None, None, 860, 682, 860, 1034, None, -1, -1, -1],
                "realdistance": 8.9,
                "dst_dir": "/home/dva4/DVA_LAB/backend/test/frame_bev",
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
                "frame_path": "api/services/Orthophoto_Maps/Data/frame_origin/DJI_0119_200.png",
                "csv_path": "api/services//Orthophoto_Maps/Data/DJI_0119.csv",
                "objects": [None, None, None, 528.60, 537.70, 134.01, 258.51, None, -1, -1, -1],
                "dst_dir": "api/services/Orthophoto_Maps/Data/result",
                "gsd": 0.00009362739603860218,

            }
        }