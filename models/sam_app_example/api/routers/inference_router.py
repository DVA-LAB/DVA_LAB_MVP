from autologging import logged
from fastapi import APIRouter, Depends, status

from api.services import Segment
from interface.request import SamRequest


router = APIRouter(tags=["sam"])

@router.post(
    "/sam/inference",
    status_code=status.HTTP_200_OK,
    summary="segmentation",
)
async def sam_inference(request_body: SamRequest, request: Request):
    segment = Segment("cuda")

    frame_bytes = await request.body()
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), -1)
    # frame_no = request_body.frame_count

    bboxes = request_body.bboxes

    masks = segment.do_seg(frame, bboxes)
    print(masks)

    return masks
