from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SahiRequest"]


@logged
class SahiRequest(BaseModel):
    """
        SAHI를 수행하기 위한 요청에 필요한 변수를 담은 클래스입니다.

        Attribute
            - img_path (str): SAHI를 적용할 원본 프레임 디렉터리 경로
            - csv_path (str): 탐지 결과가 저장되는 파일 경로
            - sliced_path (str): 슬라이싱되어 생성된 패치 프레임이 위치하는 경로
    
    """
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

