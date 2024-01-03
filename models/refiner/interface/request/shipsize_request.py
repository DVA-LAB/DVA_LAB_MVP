from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["ShipRequest"]


@logged
class ShipRequest(BaseModel):
    """
        SAM 모델 추론 수행에 필요한 변수를 담은 클래스입니다.

        Attributes
            - user_input (str): 사용자 입력이 담긴 파일 경로
            - frame_path (str): 프레임 경로
            - tracking_result (str): 객체추적 결과 bbox 파일 경로
    """
    
    user_input: str = Field(..., description="user_input_save file")
    frame_path: str = Field(..., description="img_frame_save_path (folder)")
    tracking_result: str = Field(..., description="detection_result file")

    class Config:
        schema_extra = {
            "example": {
                "user_input": "/home/dva4/DVA_LAB/backend/test/input/user_input.txt",
                "frame_path": "/home/dva4/DVA_LAB/backend/test/frame_origin",
                "tracking_result": "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt",
            }
        }
