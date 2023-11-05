import os
import torch
import argparse

from autologging import logged
from fastapi import APIRouter, Depends, status

from yolox.exp import get_exp
from yolox.utils import fuse_model
from api.services import Predictor, predict_image, predict_video
from api.services.yolox.exp import get_exp

os.environ["CUDA_VISIBLE_DEVICES"] = "1"

parser = argparse.ArgumentParser("ByteTrack")
parser.add_argument("-n", "--name", type=str, default=None, help="model name")
parser.add_argument("-c", "--ckpt", type=str, default="YOLOX_outputs/dva/best_ckpt.pth.tar",  help="ckpt for eval")
parser.add_argument("-t", "--type", type=str, default='image', help='image or video')
parser.add_argument("--path", default="./videos/palace.mp4", help="path to images or video")
parser.add_argument("--save_result",action="store_true", help="whether to save the inference result of image/video")

parser.add_argument("-f", "--exp_file", default=None, type=str, help="pls input your expriment description file")
parser.add_argument("--fps", default=30, type=int, help="frame rate (fps)")
parser.add_argument("--fp16", dest="fp16", default=False, action="store_true", help="Adopting mix precision evaluating.")
parser.add_argument("--trt", dest="trt", default=False, action="store_true", help="Using TensorRT model for testing.")
parser.add_argument("--conf", default=None, type=float, help="test conf")
parser.add_argument("--nms", default=None, type=float, help="test nms threshold")
parser.add_argument("--tsize", default=None, type=int, help="test img size")

parser.add_argument("--track_thresh", type=float, default=0.5, help="tracking confidence threshold")
parser.add_argument("--track_buffer", type=int, default=30, help="the frames for keep lost tracks")
parser.add_argument("--match_thresh", type=float, default=0.8, help="matching threshold for tracking")
parser.add_argument("--aspect_ratio_thresh", type=float, default=1.6, help="threshold for filtering out boxes of which aspect ratio are above the given value.")
parser.add_argument('--min_box_area', type=float, default=10, help='filter out tiny boxes')
parser.add_argument("--mot20", dest="mot20", default=False, action="store_true", help="test mot20.")
args = parser.parse_args()

exp = get_exp(args.exp_file, args.name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = exp.get_model().to(device)
model.eval()
ckpt = torch.load(args.ckpt, map_location="cpu")
model.load_state_dict(ckpt["model"])
model = fuse_model(model)
model = model.half()  # to FP16

predictor = Predictor(model, exp, None, device, args.fp16)
router = APIRouter(tags=["bytetrack"])

@router.post(
    "/bytetrack/inference",
    status_code=status.HTTP_200_OK,
    summary="object tracking",
)
async def bytetrack_inference(request_body: ByteTrackRequest, request: Request):
    if args.type == "image":
        results = predict_image(predictor, exp, args)
        
    elif args.type == "video":
        results = predict_video(predictor, exp, args)

    return results