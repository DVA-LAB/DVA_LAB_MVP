import torch
from config import checkpoint_file, config_file, device, score_threshold
from mmdet.apis import inference_detector, init_detector


def get_bbox(img, det_model):
    # det_model = init_detector(config_file, checkpoint_file, device=device)
    result = inference_detector(det_model, img).to_dict()
    correct_idx = torch.where(result["pred_instances"]["scores"] > score_threshold)
    boxes = result["pred_instances"]["bboxes"][correct_idx]

    return boxes
