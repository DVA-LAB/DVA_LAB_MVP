import cv2
import torch
from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess
from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracking_utils.timer import Timer


class Predictor(object):
    def __init__(self, model, exp, decoder=None, device=torch.device("cpu"), fp16=False):
        self.model = model
        self.decoder = decoder
        self.num_classes = exp.num_classes
        self.confthre = exp.test_conf
        self.nmsthre = exp.nmsthre
        self.test_size = exp.test_size
        self.device = device
        self.fp16 = fp16
        self.rgb_means = (0.485, 0.456, 0.406)
        self.std = (0.229, 0.224, 0.225)


    def inference(self, img, timer):
        img_info                = {"id": 0}
        img                     = cv2.imread(img)
        height, width           = img.shape[:2]
        img_info["height"]      = height
        img_info["width"]       = width
        img_info["raw_img"]     = img

        img, ratio = preproc(img, self.test_size, self.rgb_means, self.std)
        img_info["ratio"] = ratio
        img = torch.from_numpy(img).unsqueeze(0).float().to(self.device)
        if self.fp16:
            img = img.half()  # to FP16

        with torch.no_grad():
            outputs = self.model(img)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())
            outputs = postprocess(outputs, self.num_classes, self.confthre, self.nmsthre)
        return outputs, img_info


def predict_image(predictor, exp, args):
    tracker     = BYTETracker(args, frame_rate=args.fps)
    timer       = Timer()
    results     = []

    outputs, img_info = predictor.inference(args.path, timer)
    if outputs[0] is None:
        return None
    
    online_targets  = tracker.update(outputs[0], [img_info['height'], img_info['width']], exp.test_size)
    online_tlwhs    = []
    online_ids      = []
    online_scores   = []
    
    for t in online_targets:
        tlwh = t.tlwh
        tid = t.track_id
        vertical = tlwh[2] / tlwh[3] > args.aspect_ratio_thresh
        if tlwh[2] * tlwh[3] > args.min_box_area and not vertical:
            online_tlwhs.append(tlwh)
            online_ids.append(tid)
            online_scores.append(t.score)        
            results.append(f"{tid},{tlwh[0]:.2f},{tlwh[1]:.2f},{tlwh[2]:.2f},{tlwh[3]:.2f},{t.score:.2f},-1,-1,-1\n")
            
    return results