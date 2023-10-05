# DOTA base로 생성한 HF competition용 데이터 셋
import json
import os
import random
import tempfile

import cv2
import numpy as np
import pandas as pd
import tqdm
from datasets import Dataset, load_dataset, load_from_disk
from PIL import Image, ImageDraw


def calculate_object_ratio(obj_w, obj_h, img_w, img_h):
    obj_area = obj_w * obj_h
    img_area = img_w * img_h
    return (obj_area / img_area) * 100


def generate_random_crop_coordinates(xmin, ymin, xmax, ymax, img_w, img_h, crop_size):
    min_x = max(0, xmin - crop_size + (xmax - xmin))
    max_x = min(img_w - crop_size, xmin)
    min_y = max(0, ymin - crop_size + (ymax - ymin))
    max_y = min(img_h - crop_size, ymin)

    if min_x >= max_x or min_y >= max_y:
        return None

    start_x = random.randint(min_x, max_x)
    start_y = random.randint(min_y, max_y)
    end_x = start_x + crop_size
    end_y = start_y + crop_size

    return start_x, start_y, end_x, end_y


def check_object_within_crop(xmin, ymin, xmax, ymax, start_x, start_y, end_x, end_y):
    return xmax > start_x and xmin < end_x and ymax > start_y and ymin < end_y


def process_image_and_labels(row):
    img = row["image"]
    img_h, img_w = img.height, img.width

    labels = row["objects"]

    bboxes = labels["bbox"]
    categories = labels["categories"]

    imgs = []
    objects = []

    for bbox, category in zip(bboxes, categories):
        xmin, ymin, xmax, ymax = bbox
        obj_w, obj_h = xmax - xmin, ymax - ymin

        cropped_bboxes = []
        cropped_categories = []
        check_size = True
        target_ratio = random.uniform(0.005, 0.010)  # 0.5% ~ 1.0% 사이의 랜덤한 비율
        target_area = obj_w * obj_h / target_ratio
        crop_size = int(target_area**0.5)  # Crop 할 영역의 한 변의 길이 (정사각형)

        coords = generate_random_crop_coordinates(
            xmin, ymin, xmax, ymax, img_w, img_h, crop_size
        )
        if coords is None:
            continue

        start_x, start_y, end_x, end_y = coords
        cropped_img = img.crop(coords)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            cropped_img.save(temp_file.name, format="PNG")
            cropped_img = Image.open(temp_file.name)
            c_img_h, c_img_w = cropped_img.height, cropped_img.width
        os.remove(temp_file.name)

        for bbox, category in zip(bboxes, categories):
            oxmin, oymin, oxmax, oymax = bbox

            if check_object_within_crop(
                oxmin, oymin, oxmax, oymax, start_x, start_y, end_x, end_y
            ):
                new_xmin, new_ymin = max(0, oxmin - start_x), max(0, oymin - start_y)
                new_xmax, new_ymax = min(c_img_w, max(0, oxmax - start_x)), min(c_img_h, max(0, oymax - start_y))
                cropped_bboxes.append(
                    [new_xmin, new_ymin, new_xmax - new_xmin, new_ymax - new_ymin]
                )
                cropped_categories.append(category)

                obj_w, obj_h = new_xmax - new_xmin, new_ymax - new_ymin
                obj_ratio = calculate_object_ratio(obj_w, obj_h, c_img_w, c_img_h)
                if obj_ratio < 0.15:
                    check_size = False
        if check_size:
            imgs.append(cropped_img)
            objects.append({"bbox": cropped_bboxes, "categories": cropped_categories})

    if len(imgs):
        return imgs, objects
    else:
        return None, None


def get_dataset(save_path, exist_ok=False):
    os.makedirs(save_path, exist_ok=True)
    meta_path = os.path.join(save_path, "metadata.jsonl")
    if exist_ok or not os.path.exists(meta_path):
        if os.path.exists(meta_path):
            os.remove(meta_path)
        dataset = load_dataset(
            path="datadrivenscience/ship-detection",
        )
        tr_data = dataset["train"]
        test_data = dataset["test"]
        count = 0
        for dataset in [tr_data, test_data]:
            for data in tqdm.tqdm(dataset):
                Image.MAX_IMAGE_PIXELS = None
                img_list, objects_list = process_image_and_labels(data)
                if img_list:
                    for img, objects in zip(img_list, objects_list):
                        with open(meta_path, "a") as f:
                            json_line = json.dumps(
                                {"img_id": count, "file_name": f"img_{count}.png", "objects": objects}
                            )
                            f.write(json_line + "\n")
                            img.save(os.path.join(save_path, f"img_{count}.png"))
                            count += 1

    dataset = load_dataset("imagefolder", data_dir=save_path)
    dataset = dataset["train"].train_test_split(train_size=0.9)
    return dataset


if __name__ == "__main__":
    save_path = "/mnt/sda/DVA_ship/hf_data"
    exist_ok = False

    dataset = get_dataset(save_path, exist_ok)
