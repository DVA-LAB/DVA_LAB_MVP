import torch
from mmdet.apis import init_detector, inference_detector
from config import device, config_file, checkpoint_file, score_threshold


def get_bbox(img, det_model):
    # det_model = init_detector(config_file, checkpoint_file, device=device)
    result = inference_detector(det_model, img).to_dict()
    correct_idx = torch.where(result['pred_instances']['scores'] > score_threshold)
    boxes = result['pred_instances']['bboxes'][correct_idx]

    return boxes
