from autologging import logged
from fastapi import APIRouter, Depends, status
from interface.request import UserInput

router = APIRouter(tags=["model"])


@router.post(
    "/model/inference",
    status_code=status.HTTP_200_OK,
    summary="segmentation",
)
async def model_inference(body: UserInput):
    point_1 = body.point1
    point_2 = body.point2
    distance = body.distance

    # TODO@jh: mdoel inference 추가

    return point_1, point_2, distance
