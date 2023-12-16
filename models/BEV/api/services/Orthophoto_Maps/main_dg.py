import sys
sys.path.append("C:\\Users\\MYJS\\Desktop\\DVA\\master_Pjt\\DVA_LAB\\models\\BEV")

import os
import numpy as np
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
    Estimate the focal length given the FOV and the image width.
    
    Parameters:
    - image_width: width of the image in pixels
    - fov_degrees: field of view in degrees
    
    Returns:
    - Estimated focal length in pixels.
    """

    focal_length_mm = (sensor_width_mm / 2) / math.tan(np.radians(fov_degrees / 2))
    # focal_length_px = (focal_length_mm / sensor_width_mm) * image_width
    return focal_length_mm


def get_params_from_csv(csv_file, idx = None):
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


def BEV_UserInputFrame(frame_num, frame_path, csv_path, objects, realdistance, dst_dir, DEV = False):
    """
    * Parameters 
    frame_num : int 
    frame_path : str, png file path
    csv_path : str, csv file path
    drone_model : int, 
    objects : list [frame_id, track_id, label, bbox, score, -1, -1, -1 ]
            : BEV1 : dummy, dummy, dummy, pt1, pt2, dummy, -1, -1, -1
    realdistance : float, Meter

    * return 
    rst : result flag // 0 : Success, 1 : rectify fail, 2 : gsd calc Fail
    img_dst : string 
    objects : list object
    pixel_size : float. Unit : m/pixel
    gsd : floag. Unit : m/pixel
    
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


def BEV_Points(image_shape, col, row, coord_CCS_px_x,coord_CCS_px_y, obj_points): #, image.shape[1], coord_CCS_px_x, coord_CCS_px_y, dst_dir, gsd, DEV = False):
    """
    * Parameters 
    frame_num : int 
    frame_path : str, png file path
    csv_path : str, csv file path
    drone_model : int, 
    objects : list [frame_id, track_id, label, bbox, score, -1, -1, -1 ]
    
    * return 
    rst : result flag // 0 : Success, 1 : rectify fail, 2 : gsd calc Fail
    img_dst : string 
    objects : list object
    """
    # 3. resample
    # Nearest Neighbor
    rectify_points = []
    coord_ICS_col = int(image_shape[1] / 2 + coord_CCS_px_x)  # column
    coord_ICS_row = int(image_shape[0] / 2 + coord_CCS_px_y)  # row

    if coord_ICS_col == obj_points[0] and coord_ICS_row == obj_points[1] : 
        rectify_points[0] = col
        rectify_points[1] = row
    if coord_ICS_col == obj_points[2] and coord_ICS_row == obj_points[3] : 
        rectify_points[2] = col
        rectify_points[3] = row
    
    return rectify_points


def BEV_FullFrame(frame_num, frame_path, csv_path, dst_dir, gsd, DEV = False):
    """
    * Parameters 
    frame_num : int 
    frame_path : str, png file path
    csv_path : str, csv file path
    drone_model : int, 
    objects : list [frame_id, track_id, label, bbox, score, -1, -1, -1 ]
    
    * return 
    rst : result flag // 0 : Success, 1 : rectify fail, 2 : gsd calc Fail
    img_dst : string 
    objects : list object
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
    filename = os.path.basename(frame_path).split(".")[0]
    dst_file_name = "Transformed_{}".format(filename)
    img_dst = dst_dir + '/' + dst_file_name # os.path.join(dst_dir, dst_file_name)

    # Imread
    image = cv2.imread(frame_path, -1)
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
        b, g, r, a, image_shape, col, row, coord_CCS_px_x,coord_CCS_px_y = rectify_plane_parallel(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height, R, focal_length, pixel_size, image)
        # if DEV : 
            # create_pnga_optical_with_obj_for_dev(b, g, r, a, bbox, gsd, 5186, img_dst, rectified_poinst)  
        # else : 
        create_pnga_optical(b, g, r, a, bbox, gsd, 5186, img_dst)  
    except : 
        rst = 1
        return rst, None, None, None, None, None, None, None


    return rst, img_dst, gsd, image_shape, col, row, coord_CCS_px_x,coord_CCS_px_y

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

    print("GSD1 Done")
    col1, row1  = 528.60, 537.70
    col2, row2  = 134.01, 258.51

    objects = [None, None, None, col1, row1, col2, row2, None, -1, -1, -1]
    rst, img_dst, objects, gsd = BEV_FullFrame(frame_num, frame_path, csv_path, objects, dst_dir, gsd, DEV)
    print("GSD2 Done")

    
