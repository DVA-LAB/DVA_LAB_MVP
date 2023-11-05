"""Helpers for downloading files, calculating metrics, computing anomaly maps, and visualization."""

# Copyright (C) 2022 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from PIL import Image
from math import ceil
import cv2
import numpy as np
import torch



def slicing(image, patch=1024, overlap=0.5):

    img = cv2.imread(image)
    h, w = img.shape[:2]
    step_x = int(patch * overlap)  
    step_y = int(patch * overlap)  
    
    x_num = 1 if w <= patch else ceil((w-patch)/step_x+1)
    y_num = 1 if h <= patch else ceil((h-patch)/step_y+1)
    x, y = 0, 0
    imgs = []

    for yy in range(y_num):
        for xx in range(x_num):
            if yy == y_num - 1 and xx == x_num - 1:
                slc = img[h-patch:h, w-patch:w]
                imgs.append(slc)
                x = 0
                continue
                  
            elif yy == y_num - 1: 
                slc = img[h-patch:h, x:x+patch]
                imgs.append(slc)
                x = 0
                continue
                    
            elif xx == x_num - 1:
                slc = img[y:y+patch, w-patch:w]
                imgs.append(slc)
                x = 0
                continue

            x1 = x
            y1 = y 
            x2 = x1 + patch
            y2 = y1 + patch
            slc = img[y1:y2, x1:x2]
            imgs.append(slc)
            x = 0               
            x += step_x
                
        x =0
        y += step_y

    return imgs
