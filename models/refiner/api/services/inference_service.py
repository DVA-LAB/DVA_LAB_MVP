import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import tqdm
from transformers import SamModel, SamProcessor


class Refiner:
    def __init__(self, device):
        self.device = device
        self.rgb_img = None
        # TODO@jh: refiner-HQ 옵션 추가 (https://drive.google.com/file/d/1qobFYrI4eyIANfBSmYcGuWRaSIXfMOQ8/view?usp=sharing)
        self.model = SamModel.from_pretrained(
            pretrained_model_name_or_path="facebook/sam-vit-huge"
        ).to(self.device)
        self.processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

    def _get_loader(self, json_path, image_folder):
        """
            

            Args
                - json_path (str): 
                - image_folder (str): 

            Return
                - image (np.ndarray):
                - bbox (list):
                - anno_id (int):
        """
        with open(json_path, "r") as file:
            coco_data = json.load(file)

        images = {image["id"]: image["file_name"] for image in coco_data["images"]}

        for anno in coco_data["annotations"]:
            img_name = images[anno["image_id"]]
            image_path = os.path.join(image_folder, img_name)
            image = cv2.imread(image_path)
            bbox = anno["bbox"]
            anno_id = anno["id"]
            yield image, bbox, anno_id

    def do_refine(self, json_path, image_folder):
        """
            ?

            Args
                - json_path (str): ?
                - image_folder (str): ?

            Return
                - coco_data (json): ?
        """

        loader = self._get_loader(json_path, image_folder)

        with open(json_path, "r") as file:
            coco_data = json.load(file)

        for idx, (img, bbox, anno_id) in tqdm.tqdm(enumerate(loader)):
            int_bbox = [int(coord) for coord in self.convert_to_xyxy(bbox)]
            mask = self._do_seg(img, [int_bbox])
            updated_bbox = self.update_bbox_with_mask(mask, bbox)

            for i, anno in enumerate(coco_data["annotations"]):
                if anno["id"] == anno_id:
                    coco_data["annotations"][i]["bbox"] = updated_bbox

            if idx == 1:
                self.show_mask_bbox(
                    [mask],
                    [int_bbox],
                    [self.convert_to_xyxy(updated_bbox)],
                    random_color=False,
                    save="test_single_box.jpg",
                )
        return coco_data

    def save_update(self, coco_data, save_path):
        """
            ?

            Args
                - coco_data (json): ?
                - save_path (str): 파일 저장 경로
        """

        with open(save_path, "w") as file:
            json.dump(coco_data, file, indent=4)

    def _get_horizontal_bbox_from_mask(self, mask, bbox):
        """
            ?
            
            Args
                - mask (?): ?
                - bbox (?): ?

            Return
                - bbox (?): ?
        """

        mask = mask[0, :, :]
        if mask.any():
            y_indices, x_indices = mask.nonzero(as_tuple=True)
            x_min, x_max = x_indices.min().item(), x_indices.max().item()
            y_min, y_max = y_indices.min().item(), y_indices.max().item()
            return [int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)]
        else:
            return bbox

    def update_bbox_with_mask(self, mask, bbox):
        """
            ?
            
            Args
                - mask (?): ?
                - bbox (?): ?

            Return
                - updated_bbox (?): ?
        """

        updated_bbox = self._get_horizontal_bbox_from_mask(mask[0], bbox)
        return updated_bbox

    def _do_seg(self, bgr_img, boxes):
        """
            ?

            Args
                - bgr_img (?): ?
                - boxes (?): ?

            Return
                - ? (?): ?
        """

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
        """
            ?

            Args
                - mask (?): ?
                - random_color (bool): 색상 랜덤 여부
                - save (bool): mask 저장 여부
        """

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

    def show_mask_bbox(self, masks, old_bboxes, new_bboxes, random_color=False, save=None):
        """
            ?

            Args
                - mask (?): ?
                - old_bboxes (?): ?
                - new_bboxes (?): ?
                - random_color (bool): 색상 랜덤 여부
                - save (bool): mask 저장 여부
        """

        for bbox in old_bboxes:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(self.rgb_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
        for bbox in new_bboxes:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(self.rgb_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        self.show_mask(masks, random_color, save)

    def convert_to_xyxy(self, bbox):
        """
            ?

            Args
                - bbox (list): [x_min, y_min, width, height]

            Return
                - bbox (list): [x_min, y_min, x_min + width, y_min + height]
        """

        x_min, y_min, width, height = bbox
        x1, y1 = x_min, y_min
        x2, y2 = x_min + width, y_min + height
        return [x1, y1, x2, y2]

    @staticmethod
    def get_color(random_color):
        """
            색상을 반환합니다.

            Args
                - random_color (bool): 색상 랜덤 여부

            Return
                - color (np.array): 색상
        """
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
        return color

    @staticmethod
    def calculate_length_along_major_axis(mask):
        """
            ?

            Args
                - mask (?): ?

            Return
                - length (?): ?
        """

        mask_2d = mask[0, 0, :, :].numpy()  # 첫 번째 채널을 2차원 배열로 변환
        y_coords, x_coords = np.where(mask_2d)
        coords = np.column_stack((x_coords, y_coords))
        coords = coords.astype(np.float32)

        # PCA를 사용하여 주축 계산
        mean, eigenvectors = cv2.PCACompute(coords, mean=None)

        # 주축을 따라 길이 측정
        proj_coords = (coords - mean).dot(eigenvectors.T)
        min_coord, max_coord = np.min(proj_coords, axis=0), np.max(proj_coords, axis=0)
        length = np.linalg.norm(max_coord - min_coord)

        return length

    @staticmethod
    def find_rotated_bounding_box_and_max_length(mask):
        """
            ?

            Args
                - mask (?): ?

            Return
                - max_length (?): ?
                - box (?): ?
                - longest_edge_points (tuple): ?
        """

        mask_np = mask.numpy().astype(np.uint8)
        mask_np = mask_np.squeeze()

        contours, _ = cv2.findContours(
            mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # 가장 긴 변의 길이와 해당 변을 이루는 두 포인트를 찾습니다.
        max_length = 0
        longest_edge_points = None

        for i in range(4):
            p1 = box[i]
            p2 = box[(i + 1) % 4]
            edge_length = np.linalg.norm(p1 - p2)

            if edge_length > max_length:
                max_length = edge_length
                longest_edge_points = (p1, p2)

        return max_length, box, longest_edge_points
