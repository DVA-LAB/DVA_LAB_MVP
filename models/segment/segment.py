import os
import glob

import cv2
import numpy as np
import torch

from utils import preprocess_image, is_rgb_or_bgr
from detect import get_bbox
from segment import get_seg
from mmdet.apis import init_detector
from transformers import SamModel, SamProcessor
from config import device, config_file, checkpoint_file, score_threshold, save
import cv2
import os
import numpy as np
from PIL import Image, ImageDraw

import torch
from transformers import SamModel, SamProcessor
from config import device


class Chipseg():
    def __init__(self, config_file, checkpoint_file):
        self.det_model = init_detector(config_file, checkpoint_file, device=device)
        self.seg_model = SamModel.from_pretrained("facebook/sam-vit-huge").to(device)
        self.processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

    @staticmethod
    def check_rgb(img_array):
        if is_rgb_or_bgr(img_array) == 'RGB':
            print('아래 코드는 cv2로 불러온 BGR image array 입력 기준으로 작성되었습니다.')
            print('이미지 채널을 한번 더 확인해 주세요. 혹시나,,')

    def get_bbox(self, mask_img):
        return get_bbox(mask_img, self.det_model)

    def get_seg(self, img_array, boxes):
        return self.do_seg(img_array, boxes, self.seg_model, self.processor)

    @staticmethod
    def do_seg(img, boxes, seg_model, processor):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if len(boxes[0]):
            boxes = boxes.unsqueeze(0).cpu().tolist()
            inputs = processor(rgb_img, return_tensors="pt").to(device)
            image_embeddings = seg_model.get_image_embeddings(
                inputs["pixel_values"])

            inputs = processor(rgb_img, input_boxes=boxes,
                               return_tensors="pt").to(device)
            inputs.pop("pixel_values", None)
            inputs.update({"image_embeddings": image_embeddings})

            with torch.no_grad():
                outputs = seg_model(**inputs, multimask_output=False)

            masks = processor.image_processor.post_process_masks(
                outputs.pred_masks.cpu(),
                inputs["original_sizes"].cpu(),
                inputs["reshaped_input_sizes"].cpu())
            scores = outputs.iou_scores
            return masks[0].squeeze().cpu().detach().numpy().astype(np.uint8)
        else:
            return [[]]

    @staticmethod
    def get_mask_img(img_array, video_name):
        mask_path = os.path.join('/home/vision/Models/chip_segmentation/mask_info', video_name+'.xml')
        mask_img = preprocess_image(img_array, mask_path)
        return mask_img

    @staticmethod
    def save_seg(filename, img_array, chip_masks):
        print_img = cv2.cvtColor(img_array.copy(), cv2.COLOR_BGR2RGB)
        for mask in chip_masks:
            mask = mask * 255
            chip_mask_rgb = np.stack(
                [mask, np.zeros_like(mask), np.zeros_like(mask)], axis=2)
            print_img = cv2.addWeighted(print_img, 1, chip_mask_rgb, 0.7, 0)
        cv2.imwrite(filename, cv2.cvtColor(print_img, cv2.COLOR_RGB2BGR))


if __name__ == "__main__":
    video_name = 'GX010271'
    img_array = cv2.imread('/mnt/sda/09_chips/test/test_video/GX010271/GX010271_11100.png')
    segment = Chipseg(config_file, checkpoint_file)
    segment.check_rgb(img_array)
    mask_img = segment.get_mask_img(img_array, video_name)
    bboxes = segment.get_bbox(mask_img)
    chip_masks = segment.get_seg(img_array, bboxes)
    if save:
        segment.save_seg('/mnt/sda/09_chips/test/test.png', img_array, chip_masks)