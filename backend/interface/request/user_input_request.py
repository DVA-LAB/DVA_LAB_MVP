from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["UserInput"]


class Point(BaseModel):
    x: float
    y: float


@logged
class UserInput(BaseModel):
    point1: Point = Field(description="Coordinates of the first point")
    point2: Point = Field(description="Coordinates of the second point")
    distance: float = Field(ge=0, description="The distance parameter")

    class Config:
        schema_extra = {
            "example": {
                "point1": {"x": 100, "y": 150},
                "point2": {"x": 200, "y": 150},
                "distance": 5.0
            }
        }