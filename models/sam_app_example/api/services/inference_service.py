import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import SamModel, SamProcessor


class Segment:
    def __init__(self, device):
        self.device = device
        self.rgb_img = None
        # TODO@jh: SAM-HQ 옵션 추가 (https://drive.google.com/file/d/1qobFYrI4eyIANfBSmYcGuWRaSIXfMOQ8/view?usp=sharing)
        self.model = SamModel.from_pretrained(
            pretrained_model_name_or_path="facebook/sam-vit-huge"
        ).to(self.device)
        self.processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

    def do_seg(self, bgr_img, boxes):
        self.rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)

        if len(boxes):
            inputs = self.processor(
                self.rgb_img, input_boxes=[boxes], return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                # TODO@jh: multimask 처리 구상
                outputs = self.model(**inputs, multimask_output=False)

            masks = self.processor.image_processor.post_process_masks(
                outputs.pred_masks.cpu(),
                inputs["original_sizes"].cpu(),
                inputs["reshaped_input_sizes"].cpu(),
            )
            return masks[0].cpu()
        else:
            return None

    def show_mask(self, masks, random_color=False, save=None):
        plt.imshow(np.array(self.rgb_img))
        ax = plt.gca()
        for mask in masks:
            color = self.get_color(random_color)
            h, w = mask.shape[-2:]
            mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
            ax.imshow(mask_image)
            plt.axis("off")
        if save:
            plt.savefig(save, dpi=600)
        plt.show()

    def show_mask_bbox(self, masks, bboxes, random_color=False, save=None):
        for bbox in bboxes:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(self.rgb_img, (x1, y1), (x2, y2), (255, 0, 0), 10)
        self.show_mask(masks, random_color, save)

    @staticmethod
    def get_color(random_color):
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
        return color
