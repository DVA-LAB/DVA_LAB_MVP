from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["ModelRequest"]


@logged
class ModelRequest(BaseModel):
    """
        AI 모델 인퍼런스 요청에 필요한 변수를 담은 클래스입니다.

        Attributes
            - frame_path (str): 원본 프레임 경로
            - detection_save_path (str): 탐지 결과를 저장할 경로
            - sliced_path (str): 슬라이싱된 이미지를 저장할 경로
            - output_merge_path (str): 객체탐지와 이상탐지 결과를 병합한 결과를 저장할 파일 경로
    """

    frame_path: str
    detection_save_path: str
    sliced_path: str
    output_merge_path: str

    class Config:
        schema_extra = {
            "example": {
                "frame_path": "/home/dva4/DVA_LAB/backend/test/frame_origin",
                "detection_save_path": "/home/dva4/DVA_LAB/backend/test/model/detection/result.csv",
                "sliced_path": "/home/dva4/DVA_LAB/backend/test/model/sliced",
                "output_merge_path": "/home/dva4/DVA_LAB/backend/test/model/merged",
            }
        }