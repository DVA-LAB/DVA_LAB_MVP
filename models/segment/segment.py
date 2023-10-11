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
                outputs = self.model(**inputs, multimask_output=False)

            masks = self.processor.image_processor.post_process_masks(
                outputs.pred_masks.cpu(),
                inputs["original_sizes"].cpu(),
                inputs["reshaped_input_sizes"].cpu(),
            )
            return masks[0].cpu()
        else:
            return None, None

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


if __name__ == "__main__":
    def convert_to_xyxy(bbox):
        x_min, y_min, width, height = bbox
        x1, y1 = x_min, y_min
        x2, y2 = x_min + width, y_min + height
        return [x1, y1, x2, y2]

    sample_img = "sample_img/sample.PNG"
    save_img = "sample_img/result.PNG"
    sample_bboxes_coco = [
        [2299.2, 1267.1, 74.0, 30.44],
        [2383.68, 1250.45, 72.12, 31.87],
        [2271.17, 1212.1, 82.78, 27.92],
        [2669.33, 1217.23, 71.13, 22.9],
        [2682.2, 1167.2, 77.17, 29.2],
        [2992.7, 1339.79, 72.1, 37.32],
        [3066.6, 1300.09, 75.84, 34.34],
        [3674.59, 1221.44, 59.48, 31.53],
        [2508.45, 1018.4, 26.22, 56.92],
        [2344.2, 1021.18, 74.4, 28.12],
        [2260.55, 1123.86, 77.92, 22.06],
        [2452.69, 1123.86, 62.63, 20.28],
        [2374.31, 1184.84, 57.82, 30.89],
        [2232.1, 970.75, 68.55, 23.23],
        [2644.38, 1131.35, 46.95, 27.19],
        [2303.68, 998.19, 66.17, 27.49],
        [2379.57, 1000.31, 78.85, 20.08],
        [2279.86, 955.34, 55.79, 29.0],
        [2310.42, 1175.47, 65.45, 30.74],
    ]

    segment = Segment("cpu")
    img = cv2.imread(sample_img)
    int_bbox = [[int(coord) for coord in convert_to_xyxy(bbox)] for bbox in sample_bboxes_coco]
    masks = segment.do_seg(img, int_bbox)
    # segment.show_mask(masks, random_color=True)
    segment.show_mask_bbox(masks, int_bbox, random_color=True, save=save_img)
