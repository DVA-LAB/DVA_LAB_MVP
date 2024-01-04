import os
import numpy as np
from numba import jit, prange
import time
from .module.ExifData import *
from .module.EoData import *
from .module.Boundary import boundary
from .module.BackprojectionResample import rectify_plane_parallel_with_point, rectify_plane_parallel, createGeoTiff, create_pnga_optical, create_pnga_optical_with_obj_for_dev
from rich.console import Console
from rich.table import Table
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

import math

### ADD MORE INFO ####
# model : [Sensor Width, Sensor Height, FOV]
DRONE_SENSOR_INFO = {"MAVIC PRO" : [6.3, 4.7, 78.8], "MAVIC 2" : [6.3, 4.7, 78.8]}

def estimate_focal_length(image_width: int, sensor_width_mm: float, fov_degrees: float) -> float:
    """
        FOV와 이미지 가로 길이가 주어졌을 때 focal length를 추정합니다.

        Args
            - image_width (int): 이미지 가로 크기
            - fov_degrees (float): field of view in degrees
    
        Return
            - focal_lelngth_mm (float): 추정된 focal length 길이
    """

    focal_length_mm = (sensor_width_mm / 2) / math.tan(np.radians(fov_degrees / 2))
    # focal_length_px = (focal_length_mm / sensor_width_mm) * image_width
    return focal_length_mm


def get_params_from_csv(csv_file, idx = None):
    """
        csv 파일에서 파라미터를 추출합니다.

        Args
            - csv_file (str): csv 파일의 경로
            - idx (int): 프레임 번호
            
        Return
            - df (pd.DataFrame): 프레임 번호에 해당하는 행을 반환하며, 프레임 번호가 없을 경우 전체 반환
    """


    df = pd.read_csv(csv_file, encoding_errors='ignore')
    df.loc[:,"R"] = df["GIMBAL.roll"] # +  df["OSD.roll"]
    df.loc[:,"P"] = df["GIMBAL.pitch"] # + df["OSD.pitch"]
    df.loc[:,"Y"] = df["GIMBAL.yaw"] # + df["OSD.yaw"]
    df.loc[:,"V"] = df["adjusted height"] # Meter
    df.loc[:,"Drone"] =  df["Drone type"].str.upper()
    
    df =  df.loc[:,["R", "P", "Y", "V", "Drone"]]
    if idx == None :
        return df
    else : 
        return df.iloc[idx, :]

def get_params_for_dg(csv_file, idx=None):
    """
        csv 파일에서 Georeferencing을 위한 파라미터를 추출합니다.

        Args:
            - csv_file (str): csv 파일의 경로입니다.
            - idx (int): 프레임 번호입니다.

        Return:
            - df (pd.DataFrame): 프레임 번호에 해당하는 행을 반환하며, 프레임 번호가 없을 경우 전체를 반환합니다.
    """

    df = pd.read_csv(csv_file, encoding_errors='ignore')
    df.loc[:, "R"] = df["GIMBAL.roll"]  # +  df["OSD.roll"]
    df.loc[:, "P"] = df["GIMBAL.pitch"]  # + df["OSD.pitch"]
    df.loc[:, "Y"] = df["GIMBAL.yaw"]  # + df["OSD.yaw"]
    df.loc[:, "V"] = df["adjusted height"]  # Meter
    df.loc[:, "Drone"] = df["Drone type"].str.upper()
    df.loc[:, "Lat"] = df["OSD.latitude"]  # Degree
    df.loc[:, "Lon"] = df["OSD.longitude"]  # Degree

    df = df.loc[:, ["R", "P", "Y", "V", "Drone", "Lat", "Lon"]]
    if idx == None:
        return df
    else:
        return df.iloc[idx, :]


def BEV_UserInputFrame(frame_num, frame_path, csv_path, objects, realdistance, dst_dir, DEV = False):
    """
        프레임에 BirdEyeView (BEV)를 적용합니다.

        Args
            - frame_num (int): BEV를 적용할 프레임 번호
            - frame_path (str): BEV를 적용할 프레임 경로
            - csv_path (str): csv 파일 경로
            - objects (list): [frame_id, track_id, label, bbox, score, -1, -1, -1]
            - realdistance (float): 실제 거리 (Meter)
            - dst_dir (str): BEV가 적용된 프레임이 저장될 디렉터리 경로
    
        Return
            - rst (bool): 0: Success, 1: rectify fail, 2: fail to calculate gsd
            - img_dst (str): BEV가 적용된 프레임이 저장될 파일 경로
            - objects (list): [frame_id, track_id, label, bbox, score, -1, -1, -1]
            - pixel_size (float): Unit: m/pixel
            - gsd (float): Unit: m/pixel
    """

    # Step 0 : Meta Info.
    rst = 0 # Success
    info_row = get_params_from_csv(csv_path, frame_num) # R, P, Y, V, Drone
    
    drone_model  = info_row["Drone"]
    ground_height = 0   # unit: m
    
    if DRONE_SENSOR_INFO.get(drone_model) is None:
        drone_model = "MAVIC PRO"
    sensor_width = DRONE_SENSOR_INFO[drone_model][0]  # unit: mm 
    sensor_height = DRONE_SENSOR_INFO[drone_model][1]  # unit: mm 
    fov_degrees = DRONE_SENSOR_INFO[drone_model][2]
    gsd = 0 # unit: m, set 0 to compute automatically

    # Objects Point : Col1, Row1, Col2, Row2
    object_points = [int(x) for x in objects[3:3 + 4]]
    
    # Save Path
    filename = os.path.basename(frame_path).split(".")[0]
    dst_file_name = "Transformed_{}".format(filename)
    img_dst = dst_dir + '/' + dst_file_name # os.path.join(dst_dir, dst_file_name)

    # Imread
    image = cv2.imread(frame_path, -1)
    if DEV : 
        ## Visualize Original Image
        origin_img = image.copy()
        cv2.line(origin_img, (object_points[0], object_points[1]), (object_points[2], object_points[3]), color=(255, 0, 0), thickness = 10)
        cv2.imwrite(img_dst + '_Origin' + '.png', origin_img, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])   # from 0 to 9, default: 


    # Step 1. Extract metadata from a df and advance information
    # focal_length, orientation, eo, maker = get_metadata(file_path)  # unit: m, _, ndarray
    orientation = 1 # NEED Check from csv?? 
    maker = "DJI"  # 
    eo = [0, 0] # longitude, latitude : Not Used
    eo.append(info_row["V"]) # altitude
    eo.append(info_row["R"]) # Roll
    eo.append(info_row["P"]) # Pitch
    eo.append(info_row["Y"]) # Yaw

    focal_length = estimate_focal_length(image.shape[1], sensor_width, fov_degrees)/(1000)

    # Step 2. Restore the image based on orientation information
    restored_image = restoreOrientation(image, orientation)

    image_rows = restored_image.shape[0]
    image_cols = restored_image.shape[1]

    pixel_size = sensor_width / image_cols  # unit: mm/px
    pixel_size = pixel_size / 1000  # unit: m/px

    eo = geographic2plane(eo, 5186) # epsg = 5186 the global coordinate system definition # 5186 : Korea Center
    opk = rpy_to_opk(eo[3:], maker) # Roll Pitch Yaw Coorection
    eo[3:] = opk * np.pi / 180   # degree to radian
    R = Rot3D(eo) # Rotation Matrix
    
    # Step 3. Extract a projected boundary of the image
    bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)

    # Step 4. Compute GSD & Boundary size
    # GSD
    # if gsd == 0:
    gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px

    # Boundary size
    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)


    try :
        b, g, r, a, rectified_poinst = rectify_plane_parallel_with_point(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height, R, focal_length, pixel_size, image, object_points)
        objects[3:3 + 4] = rectified_poinst
        cols = [objects[3], objects[5]]
        rows = [objects[4], objects[6]]
        objects[3] = min(cols)
        objects[4] = min(rows)
        objects[5] = max(cols)
        objects[6] = max(rows)
        if DEV : 
            create_pnga_optical_with_obj_for_dev(b, g, r, a, bbox, gsd, 5186, img_dst, rectified_poinst)  
        else : 
            create_pnga_optical(b, g, r, a, bbox, gsd, 5186, img_dst)  
    except : 
        rst = 1
        return rst, None, None, None, None

    try :
        rectify_img_dist = math.dist(rectified_poinst[:2], rectified_poinst[2:])  # Pixel Count 
        pixel_size = realdistance/rectify_img_dist
        if DEV :
            print("pixel_count : ", rectify_img_dist)
            print("pixel_count : ", rectify_img_dist)
            print("Pixel Size : ", pixel_size)
            print(gsd)
    except :  
        print("FAIL")
        rst = 2
        return rst, None, None, None, None

    return rst, img_dst, objects, pixel_size, gsd


@jit(nopython=True, parallel=True)
def BEV_Points(image_shape, boundary, boundary_rows, boundary_cols, gsd, eo, R, focal_length, pixel_size, obj_points):
    # def BEV_Points(image_shape, R, pixel_size, boundary, boundary_cols, boundary_rows, height, focal_length, obj_points, gsd): #, image.shape[1], coord_CCS_px_x, coord_CCS_px_y, dst_dir, gsd, DEV = False):
    """
        BEV 상에서의 bbox로 변환된 bbox 정보를 반환합니다.

        Args
            - image_shape (tuple): 이미지의 가로 세로
            - boundary (?): ? 
            - boundary_rows (?): ?
            - boundary_cols (?): ? 
            - gsd (float): GSD 값
            - eo (?): ?
            - R (?): BEV 변환에 활용되는 회전행렬
            - focal_length (float): ?
            - pixel_size (float): unit: m/px
            - obj_points (list): ?

        Return
            - rectify_points (list): BEV 상의 bbox로 변환된 bbox
    """

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

    obj_points = [int(x) for x in obj_points]
    rectify_points = [0,0,0,0]

    margin = 1
    def in_range(n, start, end = 0):
        return start <= n <= end if end >= start else end <= n <= start

    for row in prange(boundary_rows):
        for col in range(boundary_cols):
            # 1. projection
            proj_coords_x = boundary[0, 0] + col * gsd - eo[0]
            proj_coords_y = boundary[3, 0] - row * gsd - eo[1]
            proj_coords_z = 0 - eo[2]

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
            # Nearest Neighbor
            coord_ICS_col = int(image_shape[1] / 2 + coord_CCS_px_x)  # column
            coord_ICS_row = int(image_shape[0] / 2 + coord_CCS_px_y)  # row

            if coord_ICS_col < 0 or coord_ICS_col >= image_shape[1]:      # column
                continue
            elif coord_ICS_row < 0 or coord_ICS_row >= image_shape[0]:    # row
                continue
            else:
                if in_range(coord_ICS_col, obj_points[0] - margin, obj_points[0] + margin) and in_range(coord_ICS_row, obj_points[1] - margin, obj_points[1] + margin) :
                    rectify_points[0] = col
                    rectify_points[1] = row
                if in_range(coord_ICS_col, obj_points[2] - margin, obj_points[2] + margin) and in_range(coord_ICS_row, obj_points[3] - margin, obj_points[3] + margin) :
                    rectify_points[2] = col
                    rectify_points[3] = row
    
    cols = [rectify_points[0], rectify_points[2]]
    rows = [rectify_points[1], rectify_points[3]]
    rectify_points[0] = min(cols)
    rectify_points[1] = min(rows)
    rectify_points[2] = max(cols)
    rectify_points[3] = max(rows)

    return rectify_points


def BEV_FullFrame(frame_num, frame_path, csv_path, gsd, dst_dir='./', DEV = False):
    """
        프레임에 BirdEyeView (BEV)를 적용합니다.
        
        Args
            - frame_num (int): BEV를 적용할 프레임 번호
            - frame_path (str): BEV를 적용할 프레임 경로
            - csv_path (str): csv 파일 경로
            - gsd (float): gsd 값
            - dst_dir (str): BEV가 적용된 프레임이 저장될 디렉터리 경로
            - DEV (bool): ?
    
        Return
            - rst (int): 0: Success, 1: rectify fail, 2: fail to calculate gsd
            - transformed_img (np.ndarray): BEV로 변환된 이미지
            - bbox (?): ?
            - boundary_rows (?): ?
            - boundary_cols (?): ?
            - gsd (float): gsd 값입니다.
            - eo (?): ?
            - R (?): BEV 변환에 활용되는 회전행렬
            - focal_length (float): 초점 거리
            - pixel_size (?): ?
    """

    # Step 0 : Meta Info.
    rst = 0 # Success
    info_row = get_params_from_csv(csv_path, frame_num) # R, P, Y, V, Drone
    
    drone_model  = info_row["Drone"]
    ground_height = 0   # unit: m
    
    if DRONE_SENSOR_INFO.get(drone_model) is None:
        drone_model = "MAVIC PRO"
    sensor_width = DRONE_SENSOR_INFO[drone_model][0]  # unit: mm 
    sensor_height = DRONE_SENSOR_INFO[drone_model][1]  # unit: mm 
    fov_degrees = DRONE_SENSOR_INFO[drone_model][2]
    gsd = gsd # From BEV1

    # Save Path
    if 1 : 
        filename = os.path.basename(frame_path).split(".")[0]
        dst_file_name = "Transformed_{}".format(filename)
        img_dst = dst_dir + '/' + dst_file_name # os.path.join(dst_dir, dst_file_name)
        # Imread
        image = cv2.imread(frame_path, -1)
    else :  # Local DEV
        img_dst = os.path.join(dst_dir, str(frame_num))
        image = frame_path # cv2.imread(frame_path, -1)


    if DEV : 
        ## Visualize Original Image
        origin_img = image.copy()
        # cv2.line(origin_img, (object_points[0], object_points[1]), (object_points[2], object_points[3]), color=(255, 0, 0), thickness = 10)
        cv2.imwrite(img_dst + '_Origin' + '.png', origin_img, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])   # from 0 to 9, default: 

    # Step 1. Extract metadata from a df and advance information
    # focal_length, orientation, eo, maker = get_metadata(file_path)  # unit: m, _, ndarray
    orientation = 1 # NEED Check from csv?? 
    maker = "DJI"  # 
    eo = [0, 0] # longitude, latitude : Not Used
    eo.append(info_row["V"]) # altitude
    eo.append(info_row["R"]) # Roll
    eo.append(info_row["P"]) # Pitch
    eo.append(info_row["Y"]) # Yaw

    focal_length = estimate_focal_length(image.shape[1], sensor_width, fov_degrees)/(1000)

    # Step 2. Restore the image based on orientation information
    restored_image = restoreOrientation(image, orientation)

    image_rows = restored_image.shape[0]
    image_cols = restored_image.shape[1]

    pixel_size = sensor_width / image_cols  # unit: mm/px
    pixel_size = pixel_size / 1000  # unit: m/px

    eo = geographic2plane(eo, 5186) # epsg = 5186 the global coordinate system definition # 5186 : Korea Center
    opk = rpy_to_opk(eo[3:], maker) # Roll Pitch Yaw Coorection
    eo[3:] = opk * np.pi / 180   # degree to radian
    R = Rot3D(eo) # Rotation Matrix
    
    # Step 3. Extract a projected boundary of the image
    bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)

    # Step 4. Compute GSD & Boundary size
    # GSD
    if gsd == 0:
        gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px

    # Boundary size
    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)
    
    try :
        b, g, r, a = rectify_plane_parallel(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height, R, focal_length, pixel_size, image)
        # if DEV : 
            # create_pnga_optical_with_obj_for_dev(b, g, r, a, bbox, gsd, 5186, img_dst, rectified_poinst)  
        # else : 
        transformed_img = cv2.merge((b, g, r))
        if 0 :
            create_pnga_optical(b, g, r, a, bbox, gsd, 5186, img_dst)  
    except : 
        rst = 1
        return rst, None, None, None, None, None, None, None, None, None

    return rst, transformed_img, bbox, boundary_rows, boundary_cols, gsd, eo, R, focal_length, pixel_size

def DG_Boundary(frame_num, frame_path, csv_path):
    """
        프레임에 Georeferencing을 위한 영역 정보를 산출합니다.

        Args:
            - frame_num (int): Georeferencing을 적용할 프레임 번호입니다.
            - frame_path (str): Georeferencing을 적용할 프레임 경로입니다.
            - csv_path (str): csv 파일 경로입니다.

        Return:
            - bbox ():
    """

    # Step 0 : Meta Info.
    info_row = get_params_for_dg(csv_path, frame_num)  # R, P, Y, V, Drone, Lat, Lon

    drone_model = info_row["Drone"]
    ground_height = 0  # unit: m

    if DRONE_SENSOR_INFO.get(drone_model) is None:
        drone_model = "MAVIC PRO"
    sensor_width = DRONE_SENSOR_INFO[drone_model][0]  # unit: mm
    sensor_height = DRONE_SENSOR_INFO[drone_model][1]  # unit: mm
    fov_degrees = DRONE_SENSOR_INFO[drone_model][2]

    image = cv2.imread(frame_path, -1)

    # Step 1. Extract metadata from a df and advance information
    # focal_length, orientation, eo, maker = get_metadata(file_path)  # unit: m, _, ndarray
    orientation = 1  # NEED Check from csv??
    maker = "DJI"  #
    eo = []  #
    eo.append(info_row["Lon"]) # longitude
    eo.append(info_row["Lat"]) # latitude
    eo.append(info_row["V"])  # altitude
    eo.append(info_row["R"])  # Roll
    eo.append(info_row["P"])  # Pitch
    eo.append(info_row["Y"])  # Yaw

    focal_length = estimate_focal_length(image.shape[1], sensor_width, fov_degrees) / (1000)

    # Step 2. Restore the image based on orientation information
    restored_image = restoreOrientation(image, orientation)

    image_rows = restored_image.shape[0]
    image_cols = restored_image.shape[1]

    pixel_size = sensor_width / image_cols  # unit: mm/px
    pixel_size = pixel_size / 1000  # unit: m/px

    eo = geographic2plane(eo, 5186)  # epsg = 5186 the global coordinate system definition # 5186 : Korea Center
    opk = rpy_to_opk(eo[3:], maker)  # Roll Pitch Yaw Correction
    eo[3:] = opk * np.pi / 180  # degree to radian
    R = Rot3D(eo)  # Rotation Matrix

    # Step 3. Extract a projected boundary of the image
    bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)

    return bbox

if __name__ == "__main__":
    ### Test Data ###
    frame_num = 200
    frame_path = "C:\\Users\\MYJS\\Desktop\\DVA\\master_Pjt\\DVA_LAB\\models\\BEV\\api\\services\\Orthophoto_Maps\\Data\\frame_img\\DJI_0119_200.png"
    csv_path = "C:\\Users\\MYJS\\Desktop\\DVA\\master_Pjt\\DVA_LAB\\models\\BEV\\api\\services\\Orthophoto_Maps\\Data\\DJI_0119.csv" 
    col1, row1  = 528.60, 537.70
    col2, row2  = col1 + 134.01, row1 + 258.51

    objects = [None, None, None, col1, row1, col2, row2, None, -1, -1, -1]
    realdistance = 20

    dst_dir = "C:\\Users\\MYJS\\Desktop\\DVA\\master_Pjt\\DVA_LAB\\models\\BEV\\api\\services\\Orthophoto_Maps\\Data\\result"
    # Test # 
    DEV = False
    rst, img_dst, objects, pixel_size, gsd = BEV_UserInputFrame(frame_num, frame_path, csv_path, objects, realdistance, dst_dir, DEV)
    print(gsd)

    # print("GSD1 Done")
    # col1, row1  = 528.60, 537.70
    # col2, row2  = 134.01, 258.51

    # objects = [None, None, None, col1, row1, col2, row2, None, -1, -1, -1]
    # rst, img_dst, objects, gsd = BEV_FullFrame(frame_num, frame_path, csv_path, objects, dst_dir, gsd, DEV)
    # print("GSD2 Done")

    