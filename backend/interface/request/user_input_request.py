from autologging import logged
from pydantic import BaseModel, Field

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
    frame_number: int = Field(description="Frame number associated with the point distances")
    point_distances: list[PointDistance] = Field(description="List of point pairs with their distances")

    class Config:
        schema_extra = {
            "example": {
                "frame_number": 1,
                "point_distances": [
                    {
                        "point1": {"x": 100, "y": 150},
                        "point2": {"x": 200, "y": 150},
                        "distance": 5.0
                    },
                    {
                        "point1": {"x": 300, "y": 350},
                        "point2": {"x": 400, "y": 350},
                        "distance": 10.0
                    }
                    # 추가적인 포인트 쌍과 거리들...
                ]
            }
        }