from autologging import logged
from pydantic import BaseModel, Field

__all__ = ["VisRequest", "VisRequestBev"]


@logged
class VisRequest(BaseModel):
    """
        Attributes:
            - log_path (str): 로그 파일의 경로입니다.
            - input_dir (str): 시각화가 적용될 원본 파일의 폴더 경로입니다.
            - output_video (str): 시각화가 적용된 출력 비디오가 생성될 파일 경로입니다.
            - bbox_path (str): 객체 추적 결과 bbox 정보가 담긴 파일의 경로입니다.
            - set_merged_dolphin_center (bool): 돌고래 bbox를 병합하여 중심점을 설정합니다. 기본값은 False입니다.

    Examples:
        이 클래스에는 이해를 돕기 위해 `Config` 클래스 내에 예시 구성이 포함되어 있습니다.
        다음과 같이 인스턴스를 생성할 수 있습니다:

        >>> request_data = {
        ...     "log_path": "/home/user/log/sync_csv",
        ...     "input_dir": "/home/user/frames",
        ...     "output_video": "/home/user/result/result.mp4",
        ...     "bbox_path": "/home/user/model/tracking/result.txt",
        ...     "set_merged_dolphin_center": False
        ... }
        >>> request = VisRequest(**request_data)

    """

    log_path: str
    input_dir: str
    output_video: str
    bbox_path: str
    set_merged_dolphin_center: bool = False

    class Config:
        schema_extra = {
            "example": {
                "log_path": "/home/dva4/DVA_LAB/backend/test/sync_csv",
                "input_dir": "/home/dva4/DVA_LAB/backend/test/frame_origin",
                "output_video": "/home/dva4/DVA_LAB/backend/test/result/result.mp4",
                "bbox_path": "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt",
                "set_merged_dolphin_center": False
            }
        }

@logged
class VisRequestBev(BaseModel):
    """
        Attributes:
            - user_input (str): 사용자의 입력이 저장된 파일 경로입니다.
            - frame_path (str): BEV 시각화를 적용할 프레임이 저장된 경로입니다.
            - tracking_result (str): 객체 추적 결과 bbox가 담긴 파일 경로입니다.
            - GSD_path (str): GSD 값이 저장된 파일 경로입니다.
            - GSD_save_path (str): 전체 GSD 값이 저장된 파일 경로입니다.

    Examples:
        이 클래스에는 이해를 돕기 위해 `Config` 클래스 내에 예시 구성이 포함되어 있습니다.
        다음과 같이 인스턴스를 생성할 수 있습니다:

        >>> request_data = {
        ...     "user_input": "/home/dva4/DVA_LAB/backend/test/input/user_input.txt",
        ...     "frame_path": "/home/dva4/DVA_LAB/backend/test/frame_origin",
        ...     "tracking_result": "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt",
        ...     "GSD_path": "/home/dva4/DVA_LAB/backend/test/GSD.txt",
        ...     "GSD_save_path": "/home/dva4/DVA_LAB/backend/test/GSD_total.txt",
        ... }
        >>> request = VisRequestBev(**request_data)

    """

    user_input: str = Field(..., description="user_input_save file")
    frame_path: str = Field(..., description="img_frame_save_path (folder)")
    tracking_result: str = Field(..., description="detection_result file")
    GSD_path: str = Field(..., description="original GSD file")
    GSD_save_path: str = Field(..., description="saved GSD file")

    class Config:
        schema_extra = {
            "example": {
                "user_input": "/home/dva4/DVA_LAB/backend/test/input/user_input.txt",
                "frame_path": "/home/dva4/DVA_LAB/backend/test/frame_origin",
                "tracking_result": "/home/dva4/DVA_LAB/backend/test/model/tracking/result.txt",
                "GSD_path": "/home/dva4/DVA_LAB/backend/test/GSD.txt",
                "GSD_save_path": "/home/dva4/DVA_LAB/backend/test/GSD_total.txt",
            }
        }