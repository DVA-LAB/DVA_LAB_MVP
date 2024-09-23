import os
from dataclasses import dataclass, field
from numba import jit, prange
import cv2
import glob
import json
import math
import argparse
import subprocess
import numpy as np
import pandas as pd
from typing import Tuple, List
from numpy.linalg import inv
from PIL import Image, ImageDraw, ImageFont
from geopy.distance import geodesic
from geopy.point import Point
from multiprocessing import Pool

### ADD MORE INFO ####
# model : [Sensor Width, Sensor Height, FOV]
DRONE_SENSOR_INFO = {"MAVIC PRO" : [6.3, 4.7, 78.8], "MAVIC 2" : [6.3, 4.7, 78.8], "MAVIC 3" : [18, 13.5, 84]}

@dataclass
class ImageInfo:
    frame: Image
    bboxes: List[List[int]]
    classes: List[int]
    ids: List[int]
    frame_count: int

@dataclass
class DroneInfo:
    ori_frame_shape: Tuple[int, int]
    bev_GSD: float
    R: np.ndarray
    boundary: np.ndarray
    boundary_rows: int
    boundary_cols: int
    eo: List[float]
    focal_length: float
    pixel_size: float
    ground_height: float

@dataclass
class Colors:
    boat_fill: str = "00FF28_40"
    boat_outline: str = "00FF28_100"
    boat_center: str = "00FF28_100"
    around_circle_50m: str = "D7EF46_20"
    around_circle_300m: str = "D7EF46_20"
    dolphin_fill: str = "FF47E2_40"
    dolphin_outline: str = "FF47E2_100"
    dolphin_center: str = "FF47E2_100"
    line_color: str = "374151_100"
    line_color_50m: str = "EF4444_100"
    text_bg_default: str = "374151_100"
    text_bg_50m: str = "EF4444_100"
    boat_fill_50m: str = "F87171_20"
    boat_outline_50m: str = "F87171_100"

@dataclass
class VisualizationConfig:
    font: ImageFont
    px_50m: int
    px_300m: int
    colors: Colors = field(default_factory=Colors)

@dataclass
class FrameProcessingParams:
    bev_frames_dir: str
    original_frames_dir: str
    csv_path: str
    json_path: str
    bev_info_path: str
    output_dir: str = 'output_frames'
    output_video_bev: str = 'output_bev.mp4'
    output_video_original: str = 'output_original.mp4'

@dataclass
class BEVInfo:
    meta_GSD: float
    R: np.ndarray
    bbox: np.ndarray
    boundary: dict
    origin_image_size: Tuple[int, int]
    eo: List[float]
    ground_height: float
    focal_length: float
    pixel_size: float

@dataclass
class ObjectInfo:
    track_id: int
    bbox: List[int]
    label: int
    frame_id: int
    speed: float = None

@jit(nopython=True, parallel=True)
def BEV_Points(image_shape, boundary, boundary_rows, boundary_cols, ground_height, gsd, eo, R, focal_length, pixel_size, obj_points):
    obj_points[2] += obj_points[0]
    obj_points[3] += obj_points[1]

    # 1. projection
    proj_coords_x = 0.
    proj_coords_y = 0.
    proj_coords_z = 0.

    # 2. back-projection
    coord_CCS_m_x = 0.
    coord_CCS_m_y = 0.
    coord_CCS_m_z = 0.
    plane_coord_CCS_x = 0.
    plane_coord_CCS_y = 0.
    coord_CCS_px_x = 0.
    coord_CCS_px_y = 0.

    # 3. resample
    coord_ICS_col = 0
    coord_ICS_row = 0

    rectify_points = [0,0,0,0]

    margin = 1
    def in_range(n, start, end = 0):
        return start <= n <= end if end >= start else end <= n <= start
    
    for row in prange(boundary_rows):
        for col in range(boundary_cols):
            # 1. projection
            proj_coords_x = boundary[0, 0] + col * gsd - eo[0]
            proj_coords_y = boundary[3, 0] - row * gsd - eo[1]
            proj_coords_z = ground_height - eo[2]

            # 2. back-projection - unit: m
            coord_CCS_m_x = R[0, 0] * proj_coords_x + R[0, 1] * proj_coords_y + R[0, 2] * proj_coords_z
            coord_CCS_m_y = R[1, 0] * proj_coords_x + R[1, 1] * proj_coords_y + R[1, 2] * proj_coords_z
            coord_CCS_m_z = R[2, 0] * proj_coords_x + R[2, 1] * proj_coords_y + R[2, 2] * proj_coords_z

            scale = (coord_CCS_m_z) / (-focal_length)  # scalar
            plane_coord_CCS_x = coord_CCS_m_x / scale
            plane_coord_CCS_y = coord_CCS_m_y / scale

            # Convert CCS to Pixel Coordinate System - unit: px
            coord_CCS_px_x = plane_coord_CCS_x / pixel_size
            coord_CCS_px_y = -plane_coord_CCS_y / pixel_size

            # 3. resample
            coord_ICS_col = int(image_shape[0] / 2 + coord_CCS_px_x)  # column
            coord_ICS_row = int(image_shape[1] / 2 + coord_CCS_px_y)  # row

            if coord_ICS_col < 0 or coord_ICS_col >= image_shape[0]:      # column
                continue
            elif coord_ICS_row < 0 or coord_ICS_row >= image_shape[1]:    # row
                continue
            else:
                if in_range(coord_ICS_col, obj_points[0] - margin, obj_points[0] + margin) and in_range(coord_ICS_row, obj_points[1] - margin, obj_points[1] + margin):
                    rectify_points[0] = col
                    rectify_points[1] = row
                if in_range(coord_ICS_col, obj_points[2] - margin, obj_points[2] + margin) and in_range(coord_ICS_row, obj_points[3] - margin, obj_points[3] + margin):
                    rectify_points[2] = col
                    rectify_points[3] = row

    return rectify_points

def create_directory(directory):
    os.makedirs(directory, exist_ok=True)

def read_json_data(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def hex_to_rgba(hex_color):
    hex_code, opacity_percentage = hex_color.split('_')
    r = int(hex_code[:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:], 16)
    a = int(float(opacity_percentage) * 255 / 100)
    return (r, g, b, a)

def draw_dashed_line(draw, point1, point2, dash_length=40, color=(255, 0, 0, 255), width=2):
    x1, y1 = point1
    x2, y2 = point2
    total_length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    dashes = int(total_length / dash_length)

    for i in range(dashes):
        start = (x1 + (x2 - x1) * i / dashes, y1 + (y2 - y1) * i / dashes)
        end = (x1 + (x2 - x1) * (i + 0.5) / dashes, y1 + (y2 - y1) * (i + 0.5) / dashes)
        draw.line([start, end], fill=color, width=width)

def read_bev_info(bev_info_path):
    with open(bev_info_path, 'r') as f:
        bev_info = json.load(f)
    bev_info_dict = {entry['frame_num']: entry for entry in bev_info}
    return bev_info_dict

def calculate_distance(box1, box2):
    center1 = (box1[0] + box1[2] / 2, box1[1] + box1[3] / 2)
    center2 = (box2[0] + box2[2] / 2, box2[1] + box2[3] / 2)
    return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

def calculate_object_point(p: Tuple[float, float], bearing: float, distance: float) -> List[float]:
    point_center = Point(p[0], p[1])
    distance_km = distance / 1000.0
    point_obj = geodesic(kilometers=distance_km).destination(point_center, bearing)
    return [point_obj.latitude, point_obj.longitude]

def calculate_bearing(pointA, pointB):
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diff_long = math.radians(pointB[1] - pointA[1])

    x = math.sin(diff_long) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diff_long))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def get_bev(sync_logs, num_frame: int, new_objects: List[dict], im_shape, im_center):
    df_frame = sync_logs.loc[sync_logs["FrameCnt"] == num_frame]

    point = df_frame[["OSD.latitude", "OSD.longitude"]].values[0].tolist()
    frame_time = df_frame["datetime"].values[0]  # Use the datetime64 object directly

    pixel_size = df_frame["adjusted height"].values[0] / im_shape[0]
    ground_height = df_frame["adjusted height"].values[0]  # Adjusted height as ground height

    objects_info = []
    for obj in new_objects:
        bbox = obj["bbox"]
        obj_center = [int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2)]
        
        objects_info.append((obj["track_id"], obj, pixel_size, obj_center, im_center, point, frame_time))

    return objects_info, ground_height

def transform_bbox_using_get_point(ori_frame_shape, boundary, boundary_rows, boundary_cols, ground_height, gsd, eo, R, focal_length, pixel_size, obj_bbox):
    rectify_points = BEV_Points(ori_frame_shape, boundary, boundary_rows, boundary_cols, ground_height, gsd, np.array(eo), np.array(R), focal_length, pixel_size, obj_bbox)
    bev_x1, bev_y1, bev_x2, bev_y2 = rectify_points
    return bev_x1, bev_y1, bev_x2, bev_y2

def draw_ellipse_with_gsd(draw, center_x, center_y, radius_m, gsd_x, gsd_y, color, width):
    """
    GSD를 고려하여 원을 그림.

    Args:
        draw (ImageDraw.Draw): ImageDraw 객체.
        center_x (int): 원의 중심 x 좌표.
        center_y (int): 원의 중심 y 좌표.
        radius_m (float): 원의 반지름(m).
        gsd_x (float): 가로 방향 GSD(m/픽셀).
        gsd_y (float): 세로 방향 GSD(m/픽셀).
        color (tuple): 원의 색상 (RGBA).
        width (int): 원의 두께.
    """

    radius_px_x = radius_m / gsd_x
    radius_px_y = radius_m / gsd_y

    draw.ellipse([
        (center_x - radius_px_x, center_y - radius_px_y),
        (center_x + radius_px_x, center_y + radius_px_y)
    ], outline=color, width=width, fill=color)

def calculate_distance_with_gsd(box1, box2, gsd_x, gsd_y):
    """
    돌고래와 선박 간의 거리 계산 시 가로, 세로 GSD를 고려.

    Args:
        box1 (list): 첫 번째 객체의 좌표 [x1, y1, x2, y2].
        box2 (list): 두 번째 객체의 좌표 [x1, y1, x2, y2].
        gsd_x (float): 가로 방향 GSD(m/픽셀).
        gsd_y (float): 세로 방향 GSD(m/픽셀).

    Returns:
        float: 두 객체 간의 거리(m).
    """
    center1 = (box1[0] + box1[2] / 2, box1[1] + box1[3] / 2)
    center2 = (box2[0] + box2[2] / 2, box2[1] + box2[3] / 2)
    
    # 가로, 세로 GSD를 고려한 거리 계산
    distance = np.sqrt(((center1[0] - center2[0]) * gsd_x) ** 2 + ((center1[1] - center2[1]) * gsd_y) ** 2)
    
    return distance

def calculate_original_gsd(focal_length, sensor_width, sensor_height, drone_height, image_width, image_height):
    """
    원본 이미지의 GSD를 계산합니다.

    Args:
        focal_length (float): 카메라의 초점 거리(mm).
        sensor_width (float): 센서의 너비(mm).
        sensor_height (float): 센서의 높이(mm).
        drone_height (float): 카메라와 지표면 간의 거리(m).
        image_width (int): 이미지의 너비(픽셀 단위).
        image_height (int): 이미지의 높이(픽셀 단위).

    Returns:
        gsd_x (float): 원본 이미지에서의 가로 방향 GSD(m/픽셀).
        gsd_y (float): 원본 이미지에서의 세로 방향 GSD(m/픽셀).
    """
    # 센서 크기와 이미지 크기 비율 계산
    sensor_pixel_ratio_x = sensor_width / image_width
    sensor_pixel_ratio_y = sensor_height / image_height

    # 원본 이미지에서의 GSD 계산
    gsd_x = ((drone_height * sensor_pixel_ratio_x) / focal_length) / 1000
    gsd_y = ((drone_height * sensor_pixel_ratio_y) / focal_length) / 1000

    return gsd_x, gsd_y

def get_drone_info(bev_info_data: dict, input_GSD: float, image_shape: Tuple[int, int]) -> DroneInfo:
    if bev_info_data:
        bev_info = BEVInfo(
            meta_GSD=bev_info_data['meta_GSD'],
            R=np.array(bev_info_data['R']),
            bbox=np.array(bev_info_data['bbox']),
            boundary=bev_info_data['boundary'],
            origin_image_size=tuple(bev_info_data['origin_image_size']),
            eo=bev_info_data['eo'],
            ground_height=bev_info_data['ground_height'],
            focal_length=bev_info_data['focal_length'],
            pixel_size=bev_info_data['pixel_size']
        )
    else:
        bev_info = None

    ori_frame_shape = bev_info.origin_image_size if bev_info else image_shape
    bev_GSD = bev_info.meta_GSD if bev_info else input_GSD
    R = bev_info.R if bev_info else np.eye(3)
    boundary = bev_info.bbox.reshape(4, 1) if bev_info else np.zeros((4, 1))
    boundary_rows = bev_info.boundary['rows'] if bev_info else image_shape[1]
    boundary_cols = bev_info.boundary['cols'] if bev_info else image_shape[0]
    eo = bev_info.eo if bev_info else [0, 0, 0, 0, 0, 0]
    focal_length = bev_info.focal_length if bev_info else 1
    pixel_size = bev_info.pixel_size if bev_info else 1
    ground_height = bev_info.ground_height if bev_info else 0
    
    return DroneInfo(ori_frame_shape, bev_GSD, R, boundary, boundary_rows, boundary_cols, eo, focal_length, pixel_size, ground_height)

def draw_combined_layers(image_info: ImageInfo, drone_info: DroneInfo, vis_config: VisualizationConfig, previous_objects_info, df_log, frame_objects):
    base_frame = image_info.frame.convert("RGBA")
    # Create layers for drawing
    layer2a = Image.new("RGBA", image_info.frame.size)
    draw2a = ImageDraw.Draw(layer2a, 'RGBA')

    layer2b = Image.new("RGBA", image_info.frame.size)
    draw2b = ImageDraw.Draw(layer2b, 'RGBA')

    layer4 = Image.new("RGBA", image_info.frame.size)
    draw4 = ImageDraw.Draw(layer4, 'RGBA')

    boats = []
    dolphins = []

    # Initialize a dictionary to collect data for each object
    objects_data = {}

    current_time = df_log.iloc[image_info.frame_count - 1]['datetime']

    current_objects_info, _ = get_bev(df_log, image_info.frame_count, frame_objects, drone_info.ori_frame_shape,
                                      [image_info.frame.size[0] // 2, image_info.frame.size[1] // 2])

    for obj_bbox, cls, id in zip(image_info.bboxes, image_info.classes, image_info.ids):
        transformed_bbox = transform_bbox_using_get_point(drone_info.ori_frame_shape, drone_info.boundary,
                                                          drone_info.boundary_rows, drone_info.boundary_cols,
                                                          drone_info.ground_height, drone_info.bev_GSD, drone_info.eo,
                                                          drone_info.R, drone_info.focal_length, drone_info.pixel_size,
                                                          obj_bbox)
        x1, y1, x2, y2 = map(int, transformed_bbox)

        if cls == 0:  # Ship
            fill_color = hex_to_rgba(vis_config.colors.boat_fill)
            outline_color = hex_to_rgba(vis_config.colors.boat_outline)
            ship_speed = None

            for obj_id, obj_row, pixel_size, obj_center, im_center, point, time in current_objects_info:
                if obj_id == id and id in previous_objects_info:
                    prev_pixel_size, prev_obj_center, prev_im_center, prev_point, prev_time = previous_objects_info[id][
                                                                                              1:]

                    delta_t = (time - prev_time) / np.timedelta64(1, 'ms')
                    if delta_t != 0:
                        bearing = calculate_bearing(prev_point, point)
                        distance_a = math.dist(prev_obj_center, prev_im_center) * prev_pixel_size
                        distance_b = math.dist(obj_center, im_center) * pixel_size
                        point_a_obj = calculate_object_point(prev_point, bearing, distance_a)
                        point_b_obj = calculate_object_point(point, bearing, distance_b)
                        distance_obj = geodesic(point_a_obj, point_b_obj).meters
                        speed_ms = (distance_obj / delta_t) * 1000
                        ship_speed = speed_ms * 1.94384  # Convert m/s to knots

            previous_objects_info[id] = (obj_row, pixel_size, obj_center, im_center, point, current_time)

            boats.append((x1, y1, x2, y2, id, ship_speed))

            # Collect data for the boat
            boat_data = {
                'datetime': current_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'frame': image_info.frame_count,
                'object_id': id,
                'class': 'boat',
                'bbox_x1': x1,
                'bbox_y1': y1,
                'bbox_x2': x2,
                'bbox_y2': y2,
                'speed_knots': f"{ship_speed:.2f}" if ship_speed is not None else "-",
                'distance_m': None  # Will be updated later if distance is computed
            }
            objects_data[id] = boat_data

            draw4.rectangle([x1, y1, x2, y2], outline=outline_color, width=2, fill=fill_color)
            label = f"Boat{id} {f'{ship_speed:.2f} kt' if ship_speed else ''}"
            label_bbox = draw4.textbbox((0, 0), label, font=vis_config.font)
            label_width = label_bbox[2] - label_bbox[0]
            label_height = (label_bbox[3] - label_bbox[1]) * 1.3

            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw4.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=outline_color,
                            outline=outline_color)

            if y1 - label_height < 0:
                label_position = (x1, y2)
                draw4.rectangle([x1, y2, x1 + label_width, y2 + label_height], fill=outline_color)
                draw4.text(label_position, label, font=vis_config.font, fill=(0, 0, 0))
            else:
                label_position = (x1, y1 - label_height)
                draw4.rectangle([x1, y1 - label_height, x1 + label_width, y1], fill=outline_color)
                draw4.text(label_position, label, font=vis_config.font, fill=(0, 0, 0))

        else:  # Dolphin
            outline_color = hex_to_rgba(vis_config.colors.dolphin_outline)
            dolphins.append((x1, y1, x2, y2, id))

            # Collect data for the dolphin
            dolphin_data = {
                'datetime': current_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'frame': image_info.frame_count,
                'object_id': id,
                'class': 'dolphin',
                'bbox_x1': x1,
                'bbox_y1': y1,
                'bbox_x2': x2,
                'bbox_y2': y2,
                'speed_knots': None,
                'distance_m': None  # Will be updated later if distance is computed
            }
            objects_data[id] = dolphin_data

            draw4.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)
            label = "Dolphin"

            text_bbox = draw4.textbbox((0, 0), label, font=vis_config.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3
            draw4.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill=outline_color)
            draw4.text((x1, y1 - text_height), label, font=vis_config.font, fill=(0, 0, 0))

            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw4.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=outline_color,
                            outline=outline_color)

    for boat in boats:
        x1, y1, x2, y2, id, ship_speed = boat
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        circle_color_50m = hex_to_rgba(vis_config.colors.around_circle_50m)

        draw2a.ellipse([center_x - vis_config.px_50m, center_y - vis_config.px_50m, center_x + vis_config.px_50m,
                        center_y + vis_config.px_50m],
                       outline=circle_color_50m, width=2, fill=circle_color_50m)

        circle_color_300m = hex_to_rgba(vis_config.colors.around_circle_300m)

        draw2b.ellipse(
            [center_x - vis_config.px_300m, center_y - vis_config.px_300m, center_x + vis_config.px_300m,
             center_y + vis_config.px_300m],
            outline=circle_color_300m, width=2, fill=circle_color_300m)

    if boats and dolphins:
        min_distance = float('inf')
        closest_pair = None
        for boat in boats:
            bx1, by1, bx2, by2, boat_id, _ = boat
            for dolphin in dolphins:
                dx1, dy1, dx2, dy2, dolphin_id = dolphin
                distance = calculate_distance([bx1, by1, bx2 - bx1, by2 - by1],
                                              [dx1, dy1, dx2 - dx1, dy2 - dy1])
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (boat, dolphin)

        if closest_pair:
            boat, dolphin = closest_pair
            bx1, by1, bx2, by2, boat_id, _ = boat
            dx1, dy1, dx2, dy2, dolphin_id = dolphin
            boat_center = ((bx1 + bx2) // 2, (by1 + by2) // 2)
            dolphin_center = ((dx1 + dx2) // 2, (dy1 + dy2) // 2)

            distance_m = min_distance * drone_info.bev_GSD

            # Update distance_m for both boat and dolphin
            objects_data[boat_id]['distance_m'] = f"{distance_m:.2f}"
            objects_data[dolphin_id]['distance_m'] = f"{distance_m:.2f}"

            if distance_m <= 50:
                outline_color = hex_to_rgba(vis_config.colors.boat_outline_50m)
                fill_color = hex_to_rgba(vis_config.colors.boat_fill_50m)
                line_color = hex_to_rgba(vis_config.colors.line_color_50m)
                text_bg_color = hex_to_rgba(vis_config.colors.text_bg_50m)
            else:
                line_color = hex_to_rgba(vis_config.colors.line_color)
                text_bg_color = hex_to_rgba(vis_config.colors.text_bg_default)

            layer3 = Image.new("RGBA", image_info.frame.size)
            draw3 = ImageDraw.Draw(layer3, 'RGBA')
            draw_dashed_line(draw3, boat_center, dolphin_center, dash_length=10, color=line_color, width=2)

            distance_text = f"{distance_m:.1f}m"
            mid_point = ((boat_center[0] + dolphin_center[0]) // 2,
                         (boat_center[1] + dolphin_center[1]) // 2)
            text_bbox = draw3.textbbox((0, 0), distance_text, font=vis_config.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3

            draw3.rectangle([mid_point[0] - text_width // 2, mid_point[1] - text_height // 2,
                             mid_point[0] + text_width // 2, mid_point[1] + text_height // 2], fill=text_bg_color)
            draw3.text((mid_point[0] - text_width // 2, mid_point[1] - text_height // 2), distance_text,
                       font=vis_config.font, fill=(255, 255, 255))

            combined = Image.alpha_composite(layer3, layer4)
    else:
        combined = layer4

    combined = Image.alpha_composite(layer2a, combined)
    combined = Image.alpha_composite(layer2b, combined)

    final_image = Image.alpha_composite(base_frame, combined)

    # Collect all object data into frame_data
    frame_data = list(objects_data.values())

    return final_image.convert("RGB"), frame_data

def draw_combined_layers_on_original(image_info: ImageInfo, drone_info: DroneInfo, vis_config: VisualizationConfig, previous_objects_info, df_log, frame_objects):
    base_frame = image_info.frame.convert("RGBA")
    
    # Create layers for drawing
    layer2a = Image.new("RGBA", image_info.frame.size)
    draw2a = ImageDraw.Draw(layer2a, 'RGBA')
    
    layer2b = Image.new("RGBA", image_info.frame.size)
    draw2b = ImageDraw.Draw(layer2b, 'RGBA')
    
    layer4 = Image.new("RGBA", image_info.frame.size)
    draw4 = ImageDraw.Draw(layer4, 'RGBA')
    
    boats = []
    dolphins = []

    current_time = df_log.iloc[image_info.frame_count - 1]['datetime']

    current_objects_info, ground_height = get_bev(df_log, image_info.frame_count, frame_objects, drone_info.ori_frame_shape, [image_info.frame.size[0] // 2, image_info.frame.size[1] // 2])
    gsd_x, gsd_y = calculate_original_gsd(drone_info.focal_length, DRONE_SENSOR_INFO['MAVIC 2'][0], DRONE_SENSOR_INFO['MAVIC 2'][1], ground_height, image_info.frame.size[0], image_info.frame.size[1])

    for obj_bbox, cls, id in zip(image_info.bboxes, image_info.classes, image_info.ids):
        x1, y1, x2, y2 = map(int, obj_bbox)
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1  
        if cls == 0:  # Ship
            fill_color = hex_to_rgba(vis_config.colors.boat_fill)
            outline_color = hex_to_rgba(vis_config.colors.boat_outline)
            ship_speed = None

            for obj_id, obj_row, pixel_size, obj_center, im_center, point, time in current_objects_info:
                if obj_id == id and id in previous_objects_info:
                    prev_pixel_size, prev_obj_center, prev_im_center, prev_point, prev_time = previous_objects_info[id][1:]

                    delta_t = (time - prev_time) / np.timedelta64(1, 'ms')
                    if delta_t != 0:
                        bearing = calculate_bearing(prev_point, point)
                        distance_a = math.dist(prev_obj_center, prev_im_center) * prev_pixel_size
                        distance_b = math.dist(obj_center, im_center) * pixel_size
                        point_a_obj = calculate_object_point(prev_point, bearing, distance_a)
                        point_b_obj = calculate_object_point(point, bearing, distance_b)
                        distance_obj = geodesic(point_a_obj, point_b_obj).meters
                        ship_speed = (distance_obj / delta_t) * 1000 * 1.94384  # Convert m/s to knots

            previous_objects_info[id] = (obj_row, pixel_size, obj_center, im_center, point, current_time)

            boats.append((x1, y1, x2, y2, id, ship_speed))

            draw4.rectangle([x1, y1, x2, y2], outline=outline_color, width=2, fill=fill_color)
            label = f"Boat{id} {f'{ship_speed:.2f} kt' if ship_speed else ''}"
            label_bbox = draw4.textbbox((0, 0), label, font=vis_config.font)
            label_width = label_bbox[2] - label_bbox[0]
            label_height = (label_bbox[3] - label_bbox[1]) * 1.3

            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw4.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=outline_color, outline=outline_color)

            if y1 - label_height < 0:
                label_position = (x1, y2)
                draw4.rectangle([x1, y2, x1 + label_width, y2 + label_height], fill=outline_color)
                draw4.text(label_position, label, font=vis_config.font, fill=(0, 0, 0))
            else:
                label_position = (x1, y1 - label_height)
                draw4.rectangle([x1, y1 - label_height, x1 + label_width, y1], fill=outline_color)
                draw4.text(label_position, label, font=vis_config.font, fill=(0, 0, 0))
        
        else:  # Dolphin
            outline_color = hex_to_rgba(vis_config.colors.dolphin_outline)
            dolphins.append((x1, y1, x2, y2))
            draw4.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)
            label = "Dolphin"
            text_bbox = draw4.textbbox((0, 0), label, font=vis_config.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3
            draw4.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill=outline_color)
            draw4.text((x1, y1 - text_height), label, font=vis_config.font, fill=(0, 0, 0))

            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            draw4.rectangle([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill=outline_color, outline=outline_color)

    for boat in boats:
        x1, y1, x2, y2, id, ship_speed = boat
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

        draw_ellipse_with_gsd(draw2a, center_x, center_y, 50, gsd_x, gsd_y, hex_to_rgba(vis_config.colors.around_circle_50m), 2)
        draw_ellipse_with_gsd(draw2b, center_x, center_y, 300, gsd_x, gsd_y, hex_to_rgba(vis_config.colors.around_circle_300m), 2)
            
    if boats and dolphins:
        min_distance = float('inf')
        closest_pair = None
        for boat in boats:
            bx1, by1, bx2, by2, id, _ = boat
            for dolphin in dolphins:
                dx1, dy1, dx2, dy2 = dolphin
                distance = calculate_distance_with_gsd([bx1, by1, bx2 - bx1, by2 - by1], [dx1, dy1, dx2 - dx1, dy2 - dy1], gsd_x, gsd_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (boat, dolphin)

        if closest_pair:
            boat, dolphin = closest_pair
            bx1, by1, bx2, by2, id, _ = boat
            dx1, dy1, dx2, dy2 = dolphin
            boat_center = ((bx1 + bx2) // 2, (by1 + by2) // 2)
            dolphin_center = ((dx1 + dx2) // 2, (dy1 + dy2) // 2)

            if min_distance <= 50:
                outline_color = hex_to_rgba(vis_config.colors.boat_outline_50m)
                fill_color = hex_to_rgba(vis_config.colors.boat_fill_50m)
                line_color = hex_to_rgba(vis_config.colors.line_color_50m)
                text_bg_color = hex_to_rgba(vis_config.colors.text_bg_50m)
            else:
                line_color = hex_to_rgba(vis_config.colors.line_color)
                text_bg_color = hex_to_rgba(vis_config.colors.text_bg_default)

            layer3 = Image.new("RGBA", image_info.frame.size)
            draw3 = ImageDraw.Draw(layer3, 'RGBA')
            draw_dashed_line(draw3, boat_center, dolphin_center, dash_length=10, color=line_color, width=2)

            distance_text = f"{min_distance:.1f}m"
            mid_point = ((boat_center[0] + dolphin_center[0]) // 2, (boat_center[1] + dolphin_center[1]) // 2)
            text_bbox = draw3.textbbox((0, 0), distance_text, font=vis_config.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = (text_bbox[3] - text_bbox[1]) * 1.3

            draw3.rectangle([mid_point[0] - text_width // 2, mid_point[1] - text_height // 2, mid_point[0] + text_width // 2, mid_point[1] + text_height // 2], fill=text_bg_color)
            draw3.text((mid_point[0] - text_width // 2, mid_point[1] - text_height // 2), distance_text, font=vis_config.font, fill=(255, 255, 255))

            combined = Image.alpha_composite(layer3, layer4)
    else:
        combined = layer4

    combined = Image.alpha_composite(layer2a, combined)
    combined = Image.alpha_composite(layer2b, combined)
    final_image = Image.alpha_composite(base_frame, combined)
    return final_image.convert("RGB")

def process_frames(params: FrameProcessingParams):
    create_directory(params.output_dir)
    
    bev_output_dir = os.path.join(params.output_dir, "bev_frames")
    original_output_dir = os.path.join(params.output_dir, "original_frames")
    create_directory(bev_output_dir)
    create_directory(original_output_dir)
    
    bev_frame_files = sorted(glob.glob(os.path.join(params.bev_frames_dir, "*.png")))
    ori_frame_files = sorted(glob.glob(os.path.join(params.original_frames_dir, "*.png")))
    bev_info_dict = read_bev_info(params.bev_info_path)
    json_data = read_json_data(params.json_path)
    df_log = pd.read_csv(params.csv_path)
    df_log['datetime'] = pd.to_datetime(df_log['datetime'], format='%Y-%m-%d %H:%M:%S.%f')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 25)

    bev_previous_objects_info = {}
    ori_previous_objects_info = {}

    collected_data = []  # Initialize an empty list to collect data

    for frame_count, (bev_frame_file, ori_frame_file) in enumerate(zip(bev_frame_files, ori_frame_files), start=1):
        frame_data = next((item['result'] for item in json_data['data'] if item['frame_id'] == frame_count - 1), [])
        bboxes = [item['bbox'] for item in frame_data]
        classes = [item['label'] for item in frame_data]
        ids = [item['track_id'] for item in frame_data]

        # Load BEV Frame
        bev_frame = Image.open(bev_frame_file)
        bev_info = ImageInfo(bev_frame, bboxes.copy(), classes.copy(), ids.copy(), frame_count)

        # Process BEV Frame
        input_GSD = bev_info_dict[frame_count]['meta_GSD'] if frame_count in bev_info_dict else 0.033962
        px_50m = int(50 / input_GSD) if input_GSD != 0 else 0
        px_300m = int(300 / input_GSD) if input_GSD != 0 else 0
        drone_info = get_drone_info(bev_info_dict.get(frame_count), input_GSD, bev_frame.size)
        vis_config = VisualizationConfig(font, px_50m, px_300m)
        
        final_image_bev, frame_data_bev = draw_combined_layers(bev_info, drone_info, vis_config, bev_previous_objects_info, df_log, frame_data)
        bev_output_frame_path = os.path.join(bev_output_dir, f'frame_{str(frame_count).zfill(6)}.jpg')
        final_image_bev.save(bev_output_frame_path)
        collected_data.extend(frame_data_bev)  # Collect data

        # Load Original Frame
        ori_frame = Image.open(ori_frame_file)
        ori_info = ImageInfo(ori_frame, bboxes, classes, ids, frame_count)

        # Process Original Frame independently of BEV
        ori_drone_info = get_drone_info(bev_info_dict.get(frame_count), input_GSD, ori_frame.size)  # Ensure the size matches ori_frame
        final_image_ori = draw_combined_layers_on_original(ori_info, ori_drone_info, vis_config, ori_previous_objects_info, df_log, frame_data)
        ori_output_frame_path = os.path.join(original_output_dir, f'frame_{str(frame_count).zfill(6)}.jpg')
        final_image_ori.save(ori_output_frame_path)

    # Save collected data to CSV
    output_csv_filename = f"{params.csv_path.split('/')[-1].split('.')[0]}_rawdata.csv"
    df_collected_data = pd.DataFrame(collected_data)
    df_collected_data.to_csv(output_csv_filename, index=False)

    # Create BEV video
    create_video(bev_output_dir, params.output_video_bev)

    # Create Original video
    create_video(original_output_dir, params.output_video_original)

def create_video(output_dir: str, output_video: str):
    cmd = [
        'ffmpeg',
        '-y',
        '-framerate', '30',
        '-i', f'{output_dir}/frame_%06d.jpg',
        '-vf', 'scale=ceil(iw/2)*2:ceil(ih/2)*2',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '22',
        '-pix_fmt', 'yuv420p',
        output_video
    ]
    subprocess.run(cmd, check=True)

def main(args):
    params = FrameProcessingParams(
        bev_frames_dir=args.bev_frames,
        original_frames_dir=args.original_frames,
        csv_path=args.csv_path,
        json_path=args.final_json_path,
        bev_info_path=args.bev_info_path,
        output_dir=args.output_dir,
        output_video_bev=args.output_video_bev,
        output_video_original=args.output_video_original,
    )
    process_frames(params)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process BEV frames with bounding boxes")
    parser.add_argument('--bev_frames', type=str, required=True, help='Directory containing input BEV frames')
    parser.add_argument('--original_frames', type=str, required=True, help='Directory containing input origin frames')
    parser.add_argument('--csv_path', type=str, required=True, help='Path to CSV file with drone log data')
    parser.add_argument('--final_json_path', type=str, required=True, help='Path to JSON file with bounding box data')
    parser.add_argument('--bev_info_path', type=str, required=True, help='Path to bev_info.json file')
    parser.add_argument('--output_dir', type=str, default='output_frames', help='Directory to save output frames')
    parser.add_argument('--output_video_bev', type=str, default='output_bev.mp4', help='Path to save BEV output video')
    parser.add_argument('--output_video_original', type=str, default='output_original.mp4', help='Path to save Original output video')
    args = parser.parse_args()

    main(args)
