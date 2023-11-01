import argparse
from autologging import logged
from fastapi import APIRouter, Depends, status
from api.services import Predictor, predict_image
from api.services.yolox.exp import get_exp

parser = argparse.ArgumentParser("ByteTrack")
parser.add_argument("-n", "--name", type=str, default=None, help="model name")
parser.add_argument("-c", "--ckpt", type=str, default="YOLOX_outputs/dva/best_ckpt.pth.tar", help="ckpt for eval")
parser.add_argument("-p", "--path", type=str, default=None, help="path to images")

# exp file
parser.add_argument("-f", "--exp_file", type=str, default=None, help="pls input your expriment description file")
parser.add_argument("--fp16",   dest="fp16", default=False, action="store_true", help="Adopting mix precision evaluating.")
parser.add_argument("--trt",    dest="trt", default=False, action="store_true", help="Using TensorRT model for testing.")
parser.add_argument("--fps",    type=int, default=30, help="frame rate (fps)")
parser.add_argument("--conf",   type=float, default=None, help="test conf")
parser.add_argument("--nms",    type=float, default=None, help="test nms threshold")
parser.add_argument("--tsize",  type=int, default=None, help="test img size")

# tracking args
parser.add_argument("--track_thresh", type=float, default=0.5, help="tracking confidence threshold")
parser.add_argument("--track_buffer", type=int, default=30, help="the frames for keep lost tracks")
parser.add_argument("--match_thresh", type=float, default=0.8, help="matching threshold for tracking")
parser.add_argument("--aspect_ratio_thresh", type=float, default=1.6, help="threshold for filtering out boxes of which aspect ratio are above the given value.")
parser.add_argument('--min_box_area', type=float, default=10, help='filter out tiny boxes')
parser.add_argument("--mot20", dest="mot20", default=False, action="store_true", help="test mot20.")
args = parser.parse_args()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
exp = get_exp(args.exp_file, args.name)
model = exp.get_model().to(device)
model.eval()

cpkt = torch.load(args.ckpt, map_location="cpu")
model.load_state_dict(ckpt["model"])
model = fuse_model(model)
model = model.half() # to FP16
predictor = Predictor(model, exp, None, device, args.fp16)

router = APIRouter(tags=["bytetrack"])

@router.post(
    "/bytetrack/inference",
    status_code=status.HTTP_200_OK,
    summary="object tracking",
)
async def bytetrack_inference(request_body: ByteTrackRequest, request: Request):
    results = predict_image(predictor, exp, args)
    return results