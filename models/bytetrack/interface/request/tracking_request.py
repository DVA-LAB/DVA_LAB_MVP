from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["TrackingRequest"]


@logged
class TrackingRequest(BaseModel):
    """
        객체 추적 인퍼런스 요청에 필요한 두 파일 경로를 담은 클래스입니다.

        Attributes
            - det_result_path (str): 객체탐지와 이상탐지의 결과가 병합된 bbox 정보가 담긴 파일 경로
            - result_path (str): 객체추적 결과가 저장될 파일 경로
    """

    det_result_path: str = Field(..., description="detection result")
    result_path: str = Field(..., description="tracking result")

    class Config:
        schema_extra = {
            "example": {
                "det_result_path": "/home/dva4/DVA_LAB/backend/test/model/merged/result.txt",
                "result_path": "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt",
            }
        }
