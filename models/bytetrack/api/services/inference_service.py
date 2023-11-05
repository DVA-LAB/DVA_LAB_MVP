import os
import cv2
import time
import torch
from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import postprocess
from yolox.utils.visualize import plot_tracking
from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracking_utils.timer import Timer
from loguru import logger


class Predictor(object):
    def __init__(self, model, exp, decoder=None, device=torch.device("cpu"), fp16=False):
        self.model          = model
        self.decoder        = decoder
        self.num_classes    = exp.num_classes
        self.confthre       = exp.test_conf
        self.nmsthre        = exp.nmsthre
        self.test_size      = exp.test_size
        self.device         = device
        self.fp16           = fp16
        self.rgb_means      = (0.485, 0.456, 0.406)
        self.std            = (0.229, 0.224, 0.225)


    def inference(self, image, timer):
        image_info              = {"id": 0}
        
        if isinstance(image, str):
            image_info["file_name"] = os.path.basename(image)
            image = cv2.imread(image)
        else:
            image_info['file_name'] = None
            
        height, width           = image.shape[:2]
        image_info["height"]    = height
        image_info["width"]     = width
        image_info["raw_img"]   = image

        image, ratio = preproc(image, self.test_size, self.rgb_means, self.std)
        image_info["ratio"] = ratio
        image = torch.from_numpy(image).unsqueeze(0).float().to(self.device)
        if self.fp16:
            image = image.half()

        with torch.no_grad():
            outputs = self.model(image)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())
            outputs = postprocess(outputs, self.num_classes, self.confthre, self.nmsthre)
        return outputs, image_info


def predict_image(predictor, exp, args):
    tracker     = BYTETracker(args, frame_rate=args.fps)
    results     = []
    timer       = Timer()

    outputs, image_info = predictor.inference(args.path, timer)
    
    if outputs[0] is not None:
        online_targets  = tracker.update(outputs[0], [image_info['height'], image_info['width']], exp.test_size)
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
        timer.toc()
        online_im = plot_tracking(image_info['raw_img'], online_tlwhs, online_ids, fps=1. / timer.average_time)
    else:
        timer.toc()
        online_im = image_info['raw_img']
    return results


def predict_video(predictor, exp, args):
    tracker     = BYTETracker(args, frame_rate=args.fps)
    cap         = cv2.VideoCapture(args.path)
    width       = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height      = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps         = cap.get(cv2.CAP_PROP_FPS)
    
    timer           = Timer()
    current_time    = time.localtime()
    timestamp       = time.strftime("%Y_%m_%d_%H_%M_%S", current_time)
    os.makedirs(os.path.join('output', timestamp), exist_ok=True)
    
    save_path   = os.path.join('output', timestamp, args.path.split("/")[-1])
    vid_writer  = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (int(width), int(height)))
    frame_id    = 0
    results     = []
    
    while True:
        if frame_id % 20 == 0:
            logger.info('Processing frame {} ({:.2f} fps)'.format(frame_id, 1. / max(1e-5, timer.average_time)))

        ret_val, frame = cap.read()
        if not ret_val:
            continue
        
        outputs, image_info = predictor.inference(frame, timer)
        if outputs[0] is not None:
            online_targets  = tracker.update(outputs[0], [image_info['height'], image_info['width']], exp.test_size)
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
                    results.append(f"{frame_id},{tid},{tlwh[0]:.2f},{tlwh[1]:.2f},{tlwh[2]:.2f},{tlwh[3]:.2f},{t.score:.2f},-1,-1,-1\n")
            timer.toc()
            online_im = plot_tracking(image_info['raw_img'], online_tlwhs, online_ids, fps=1. / timer.average_time)
        else:
            timer.toc()
            online_im = image_info['raw_img']
            
        if args.save_result:
            vid_writer.write(online_im)
            
        frame_id += 1

    cap.release()
    vid_writer.release()

    return results