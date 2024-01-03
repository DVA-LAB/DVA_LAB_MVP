from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["DataRequest"]


@logged
class DataRequest(BaseModel):
    """
        SAM 모델 기반 bbox refinement 수행에 필요한 변수를 담은 클래스입니다.

        Attributes
            - img_path (str): 이미지 폴더 경로
            - json_file (str): json 라벨 경로
    """
    
    img_path: str = Field(..., description="img_folder_path")
    json_file: str = Field(..., description="json_label_path")

    class Config:
        schema_extra = {
            "example": {
                "img_path": "/mnt/coco_form/train",
                "json_file": "/mnt/coco_form/train.json",
            }
        }
