from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["DataRequest"]


@logged
class DataRequest(BaseModel):
    img_path: str = Field(..., description="img_folder_path")
    json_file: str = Field(..., description="json_label_path")

    class Config:
        schema_extra = {
            "example": {
                "img_path": "/mnt/coco_form/train",
                "json_file": "/mnt/coco_form/train.json",
            }
        }
