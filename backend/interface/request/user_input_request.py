from autologging import logged
from pydantic import BaseModel, Field
from typing import List

__all__ = ["UserInput"]


class Point(BaseModel):
    x: float
    y: float


class PointDistance(BaseModel):
    point1: Point = Field(description="Coordinates of the first point")
    point2: Point = Field(description="Coordinates of the second point")
    distance: float = Field(ge=0, description="The distance between point1 and point2")


@logged
class UserInput(BaseModel):
    """
        유저의 입력에 필요한 변수가 담긴 클래스입니다.

        Attributes
            - frame_number (int): 프레임 번호
            - point_distances (List[PointDistance]): 두 점의 (x, y)좌표 정보와 두 점간의 거리가 담긴 리스트
    """

    frame_number: int = Field(description="Frame number associated with the point distances")
    point_distances: List[PointDistance] = Field(description="List of point pairs with their distances")

    class Config:
        schema_extra = {
            "example": {
                "frame_number": 950,
                "point_distances": [
                    {
                    "point1": {
                        "x": 840,
                        "y": 831
                    },
                    "point2": {
                        "x": 855,
                        "y": 1208
                    },
                    "distance": 8.9
                    }
                ]
            }
        }