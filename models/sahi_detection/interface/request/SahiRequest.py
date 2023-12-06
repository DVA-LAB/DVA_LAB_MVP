from autologging import logged
from pydantic import BaseModel, Field
import numpy as np

__all__ = ["SahiRequest"]


@logged
class SahiRequest(BaseModel):
    img_path: str 
    csv_path: str
