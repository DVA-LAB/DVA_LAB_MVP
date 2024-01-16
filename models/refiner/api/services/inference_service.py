import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import tqdm
from transformers import SamModel, SamProcessor

from .FastSAM.fastsam import FastSAM, FastSAMPrompt


class Refiner:
    def __init__(self, device, fastsam=False):
        """
            SAM (Segmentation-Aware Model)을 사용하여 이미지의 객체를 세그먼트화하는 Refiner 클래스의 생성자입니다.

            Args
                - device (str): 모델을 실행할 장치 ('cuda' 또는 'cpu').

            Note
                - `self.model`과 `self.processor`는 Facebook의 'sam-vit-huge' 모델을 사용하여 초기화됩니다.
                - 추후 'refiner-HQ' 옵션을 추가할 예정입니다 (https://drive.google.com/file/d/1qobFYrI4eyIANfBSmYcGuWRaSIXfMOQ8/view?usp=sharing).
        """
        self.device = device
        self.rgb_img = None

        if fastsam:
            self.model = FastSAM("./FastSAM-x.pt")
        else:
            self.model = SamModel.from_pretrained(
                pretrained_model_name_or_path="facebook/sam-vit-huge"
            ).to(self.device)
            self.processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

    def _get_loader(self, json_path, image_folder):
        """
            COCO 형식의 JSON 파일과 이미지 폴더에서 이미지와 해당 바운딩 박스, 어노테이션 ID를 로드하는 제너레이터입니다.

            Args
                - json_path (str): COCO 형식의 어노테이션 데이터가 담긴 JSON 파일 경로.
                - image_folder (str): 이미지 파일들이 있는 폴더 경로.

            Yields
                - image (np.ndarray): 로드된 이미지.
                - bbox (list): 해당 이미지의 바운딩 박스 좌표.
                - anno_id (int): 어노테이션 ID.
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
            지정된 JSON 파일과 이미지 폴더를 사용하여 바운딩 박스를 세그먼트 마스크로 세밀화합니다.

            Args
                - json_path (str): COCO 형식의 어노테이션 데이터가 담긴 JSON 파일 경로.
                - image_folder (str): 이미지 파일들이 있는 폴더 경로.

            Return
                - coco_data (json): 세그먼트 마스크로 업데이트된 어노테이션 데이터.
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
            업데이트된 어노테이션 데이터를 JSON 파일로 저장합니다.

            Args
                - coco_data (json): 업데이트된 어노테이션 데이터.
                - save_path (str): 저장할 파일 경로.
        """

        with open(save_path, "w") as file:
            json.dump(coco_data, file, indent=4)

    def _get_horizontal_bbox_from_mask(self, mask, bbox):
        """
            마스크를 기반으로 수평 바운딩 박스 좌표를 계산합니다.

            Args
                - mask (np.ndarray): 세그먼트화된 객체의 마스크.
                - bbox (list): 원래 바운딩 박스 좌표 [x_min, y_min, width, height].

            Return
                - bbox (list): 마스크에 기반한 새로운 바운딩 박스 좌표 [x_min, y_min, width, height].
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
            세그먼트 마스크를 사용하여 바운딩 박스 좌표를 업데이트합니다.

            Args
                - mask (np.ndarray): 세그먼트화된 객체의 마스크.
                - bbox (list): 원래 바운딩 박스 좌표 [x_min, y_min, width, height].

            Return
                - updated_bbox (list): 업데이트된 바운딩 박스 좌표 [x_min, y_min, width, height].
        """

        updated_bbox = self._get_horizontal_bbox_from_mask(mask[0], bbox)
        return updated_bbox

    def _do_seg(self, bgr_img, boxes):
        """
            주어진 이미지와 바운딩 박스에 대해 세그먼트화를 수행합니다.

            Args
                - bgr_img (np.ndarray): 세그먼트화할 이미지.
                - boxes (list): 세그먼트화할 영역의 바운딩 박스 좌표 목록.

            Return
                - masks (np.ndarray): 계산된 세그먼트 마스크.
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

    def _do_seg_fast(self, bgr_img, boxes):
        """
        주어진 이미지와 바운딩 박스에 대해 세그먼트화를 수행합니다.

        Args
            - bgr_img (np.ndarray): 세그먼트화할 이미지.
            - boxes (list): 세그먼트화할 영역의 바운딩 박스 좌표 목록.

        Return
            - masks (np.ndarray): 계산된 세그먼트 마스크.
        """
        self.rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        try:
            with torch.no_grad():
                everything_results = self.model(
                    self.rgb_img,
                    device=self.device,
                    retina_masks=True,
                    imgsz=1024,
                    conf=0.4,
                    iou=0.9,
                )
                prompt_process = FastSAMPrompt(
                    self.rgb_img, everything_results, device=self.device
                )
                ann = prompt_process.box_prompt(bboxes=boxes)
            return ann
        except Exception as e:
            print(e)
            return None

    def show_mask(self, masks, random_color=False, save=None):
        """
            세그먼트 마스크를 이미지 위에 표시합니다.

            Args
                - masks (np.ndarray): 표시할 마스크.
                - random_color (bool): 마스크에 적용할 색상을 무작위로 선택할지 여부.
                - save (str): 결과 이미지를 저장할 파일 경로 (저장하지 않을 경우 None).

            Note
                - 이미지는 `self.rgb_img`에 저장되어 있어야 합니다.
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

    def show_mask_bbox(
        self, masks, old_bboxes, new_bboxes, random_color=False, save=None
    ):
        """
            세그먼트 마스크와 바운딩 박스를 이미지 위에 표시합니다.

            Args
                - masks (list): 표시할 세그먼트 마스크 목록.
                - old_bboxes (list): 원래 바운딩 박스 좌표 목록.
                - new_bboxes (list): 업데이트된 바운딩 박스 좌표 목록.
                - random_color (bool): 마스크에 적용할 색상을 무작위로 선택할지 여부.
                - save (str): 결과 이미지를 저장할 파일 경로 (저장하지 않을 경우 None).

            Note
                - 이미지는 `self.rgb_img`에 저장되어 있어야 합니다.
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
            COCO 형식의 바운딩 박스 좌표를 [x_min, y_min, x_max, y_max] 형식으로 변환합니다.

            Args
                - bbox (list): COCO 형식의 바운딩 박스 좌표 [x_min, y_min, width, height].

            Return
                - bbox (list): 변환된 바운딩 박스 좌표 [x_min, y_min, x_max, y_max].
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
            주축을 따라 마스크의 길이를 계산하는 정적 메소드입니다.

            Args
                - mask (np.ndarray): 길이를 계산할 마스크입니다.

            Return
                - length (float): 계산된 길이입니다.
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
            마스크를 기반으로 회전된 바운딩 박스와 그 박스의 가장 긴 변의 길이를 찾는 정적 메소드입니다.

            Args
                - mask (np.ndarray): 객체의 세그먼트 마스크를 나타내는 2차원 배열.

            Return
                - max_length (float): 마스크에서 가장 긴 변의 길이.
                - box (np.ndarray): 마스크에 대한 회전된 최소 영역 바운딩 박스의 꼭짓점.
                - longest_edge_points (tuple): 가장 긴 변을 이루는 두 꼭짓점의 좌표.
        """
        try:
            mask_np = mask.numpy().astype(np.uint8)
        except:
            mask_np = mask.astype(np.uint8)
        mask_np = mask_np.squeeze()

        contours, _ = cv2.findContours(
            mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        box = np.int0(box)

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
