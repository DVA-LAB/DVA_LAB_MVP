# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import re
import cv2
from PIL import Image
from PIL.ExifTags import TAGS
from typing import Tuple
from scipy.spatial.transform import Rotation as R
import numpy as np
    
class IPM(object):
    """
    Inverse perspective mapping to a bird-eye view. Assume pin-hole camera model.
    There are detailed explanation of every step in the comments, and variable names in the code follow these conventions:
    `_c` for camera coordinates
    `_w` for world coordinates
    `uv` for perspective transformed uv 2d coordinates (the input image)
    """
    def __init__(self, camera_info, ipm_info):
        self.camera_info = camera_info
        self.ipm_info = ipm_info

        ## Construct matrices T, R, K
        self.T = np.eye(4)
        self.T[2, 3] = -camera_info.camera_height # 4x4 translation matrix in 3d space (3d homo coordinate)
        
        _cy = np.cos(camera_info.yaw   * np.pi / 180.)
        _sy = np.sin(camera_info.yaw   * np.pi / 180.)
        _cp = np.cos(camera_info.pitch * np.pi / 180.)
        _sp = np.sin(camera_info.pitch * np.pi / 180.)
        # _cr = np.cos(camera_info.roll * np.pi / 180.)
        # _sr = np.sin(camera_info.roll * np.pi / 180.)
        
        # troll = np.array([[_cr, -_sr, 0],
        #                  [_sr, _cr, 0],
        #                  [0, 0, 1]]) #z
        # tyaw = np.array([[_cy, 0, -_sy],
        #                  [0, 1, 0],
        #                  [_sy, 0, _cy]]) #y
        tpitch = np.array([[1, 0, 0],
                           [0, _cp, -_sp],
                           [0, _sp, _cp]]) #x

        self.R = tpitch #yxz # 3x3 Rotation matrix in 3d space
        self.R_inv = np.linalg.inv(self.R) # 역행렬 계산
        self.K = np.array([[camera_info.f_x, 0, camera_info.u_x],
                           [0, camera_info.f_y, camera_info.u_y],
                           [0, 0, 1]]).astype(float) # 3x3 intrinsic perspective projection matrix

        ## The ground plane z=0 in the world coordinates, transform to a plane `np.dot(self.normal_c, point) = self.const_c` in the camera coordinates. 
        # This is used to find (x,y,z)_c according to (u,v). See method `uv2xy` for detail.
        self.normal_c = np.dot(self.R, np.array([0,0,1])[:, None]) # normal of ground plane equation in camera coordinates
        self.const_c = np.dot(self.normal_c.T, 
                              np.dot(self.R,
                                     np.dot(self.T, np.array([0,0,0,1])[:, None])[:3])) # constant of ground plane equation in camera coordinates

        ## Get the limit to be converted on the uv map (must below vanishing point)
        # To calculate (u,v) of the vanishing point on the uv map of delta vector v=[0,1,0] in the world coordinates
        # homo coordinates of a vector will be v_4 = [0, 1, 0, 0], mapping this vector to camera coordinate:
        # vc_3 = np.dot(R_4, np.dot(T_4, v_4))[:3] = np.dot(R, v), the 2d homo coordinate of the vanishing point will be at 
        # lim_{\lambda -> \infty} np.dot(K, lambda * vc_3) = np.dot(K, vc_3)

        # lane_vec_c = np.dot(self.R, np.array([0,1,0])[:, None]) # lane vector in camera coordinates
        # lane_vec_homo_uv = np.dot(self.K, lane_vec) # lane vector on uv map (2d homo coordinate)
        lane_vec_homo_uv = np.dot(self.K, np.dot(self.R, np.array([0,1,0])[:, None])) # lane vector on uv map (2d homo coordinate)
        vp = self.vp = lane_vec_homo_uv[:2] / lane_vec_homo_uv[2] # coordinates of the vanishing point of lanes on uv map
        
        # UGLY: This is an ugly op to ensure the converted area do not goes beyond the vanishing point, as the camera intrinsic/extrinsic parameters are not accurate in my case.
        ipm_top = self.ipm_top = max(ipm_info.top, vp[1]+ipm_info.input_height/10) 
        if isinstance(ipm_top, np.ndarray):
            ipm_top = ipm_top[0]
        
        uv_limits = self.uv_limits = np.array([[ipm_info.left, ipm_top],
                              [ipm_info.right, ipm_top],
                              [vp[0][0], ipm_top],
                              [vp[0][0], ipm_info.bottom]]).T # the limits of the area on the uv map to be IPM-converted

        ## The x,y limit in the world coordinates is used to calculate xy_grid, and then the corresponding uv_grid
        self.xy_limits = self.uv2xy(uv_limits)
        xmin, xmax = min(self.xy_limits[0]), max(self.xy_limits[0])
        ymin, ymax = min(self.xy_limits[1]), max(self.xy_limits[1])
        stepx = (xmax - xmin) / ipm_info.out_width  # x to output pixel ratio
        stepy = (ymax - ymin) / ipm_info.out_height # y to output pixel ratio

        # xy_grid: what x,y coordinates in world coordinates will be stored in every output image pixel
        self.xy_grid = np.array([[(xmin + stepx * (0.5 + j), ymax - stepy * (0.5 + i)) for j in range(ipm_info.out_width)]
                                 for i in range(ipm_info.out_height)]).reshape(-1, 2).T
        # uv_grid: what u,v coordiantes on the uv map will be stored in every output image pixel
        self.uv_grid = self.xy2uv(self.xy_grid).astype(int)
        self.uv_grid = self.uv_grid * ((self.uv_grid[0] > ipm_info.left) * (self.uv_grid[0] < ipm_info.right) *\
                                       (self.uv_grid[1] > ipm_top) * (self.uv_grid[1] < ipm_info.bottom))
        self.uv_grid = tuple(self.uv_grid.reshape(2, ipm_info.out_height, ipm_info.out_width))
        self.uv_grid = (self.uv_grid[1], self.uv_grid[0])

    def xy2uv(self, xys): # all points have z=0 (ground plane): w (u,v,1) = KRT (x,y,z)_w
        # x축 좌표 반전
        xys[0, :] = -xys[0, :]
        xyzs = np.vstack((xys, -self.camera_info.camera_height * np.ones(xys.shape[1]))) # (x,y,z) after translation
        xyzs_c = np.dot(self.K, np.dot(self.R, xyzs)) # w(u,v,1) (2d homo)
        return xyzs_c[:2] / xyzs_c[2]

    def uv2xy(self, uvs): # all points have z=0 (ground plane): find (x,y,z)_c first, then x_w, y_w = (R^-1 (x,y,z)_c)[:2]
        uvs = (uvs - np.array([self.camera_info.u_x, self.camera_info.u_y])[:, None]) /\
              np.array([self.camera_info.f_x, self.camera_info.f_y])[:, None] # converted using camara intrinsic parameters
        uvs = np.vstack((uvs, np.ones(uvs.shape[1])))
        xyz_c = (self.const_c / np.dot(self.normal_c.T, uvs)) * uvs # solve the equation, get (x,y,z) on the ground plane in camera coordinates
        xy_w = np.dot(self.R_inv, xyz_c)[:2, :] # (x, y) on the ground plane in the world coordinates
        # x축 좌표 반전
        xy_w[0, :] = -xy_w[0, :]
        return xy_w

    def __call__(self, img):
        return self.ipm(img)

    def ipm(self, img):
        return img[self.uv_grid]

    def reverse_ipm(self, img, shape=None):
        if shape is None:
            shape = img.shape
        out_img = np.zeros(shape)
        out_img[self.uv_grid] = img
        return out_img

class _DictObjHolder(object):
    def __init__(self, dct):
        self.dct = dct

    def __getattr__(self, name):
        return self.dct[name]

def get_file_path(directory: str) -> list:
    filepaths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if filepath.lower().endswith('.jpg'):
                filepaths.append(filepath)
    
    return filepaths

def extract_exif(filepath: str) -> dict:
    image       = Image.open(filepath)
    info        = image._getexif()
    exif_table  = {}
    
    for (tag, value) in info.items():
        decoded = TAGS.get(tag, tag)
        exif_table[decoded] = value

    image.close()
    
    return exif_table

def extract_xmp(filepath: str) -> Tuple[Tuple, Tuple, Tuple]:
    with open(filepath, mode="rb") as f:
        data        = f.read()
        xmp_start   = data.find(b'<x:xmpmeta')
        xmp_end     = data.find(b'</x:xmpmeta')
        xmp_data    = data[xmp_start : xmp_end+12]
        
        pattern_absolute_altitude       = re.compile(b'AbsoluteAltitude="[+-]\d{1,}\.\d{1,}"')
        pattern_relative_altitude       = re.compile(b'RelativeAltitude="[+-]\d{1,}\.\d{1,}"')
        pattern_gimbal_yaw_degree       = re.compile(b'GimbalYawDegree="[+-]\d{1,}\.\d{1,}"')
        pattern_gimbal_pitch_degree     = re.compile(b'GimbalPitchDegree="[+-]\d{1,}\.\d{1,}"')
        pattern_gimbal_roll_degree      = re.compile(b'GimbalRollDegree="[+-]\d{1,}\.\d{1,}"')
        pattern_flight_yaw_degree       = re.compile(b'FlightYawDegree="[+-]\d{1,}\.\d{1,}"')
        pattern_flight_pitch_degree     = re.compile(b'FlightPitchDegree="[+-]\d{1,}\.\d{1,}"')
        pattern_flight_roll_degree      = re.compile(b'FlightRollDegree="[+-]\d{1,}\.\d{1,}"')
        
        match_absolute_altitude         = pattern_absolute_altitude.search(xmp_data)
        match_relative_altitude         = pattern_relative_altitude.search(xmp_data)
        match_gimbal_yaw_degree         = pattern_gimbal_yaw_degree.search(xmp_data)
        match_gimbal_pitch_degree       = pattern_gimbal_pitch_degree.search(xmp_data)
        match_gimbal_roll_degree        = pattern_gimbal_roll_degree.search(xmp_data)
        match_flight_yaw_degree         = pattern_flight_yaw_degree.search(xmp_data)
        match_flight_pitch_degree       = pattern_flight_pitch_degree.search(xmp_data)
        match_flight_roll_degree        = pattern_flight_roll_degree.search(xmp_data)
        
        altitude_absolute   = match_absolute_altitude.group().split(b'"')[1].decode('utf-8')
        altitude_relative   = match_relative_altitude.group().split(b'"')[1].decode('utf-8')
        flight_yaw          = match_flight_yaw_degree.group().split(b'"')[1].decode('utf-8')
        flight_pitch        = match_flight_pitch_degree.group().split(b'"')[1].decode('utf-8')
        flight_roll         = match_flight_roll_degree.group().split(b'"')[1].decode('utf-8')
        gimbal_yaw          = match_gimbal_yaw_degree.group().split(b'"')[1].decode('utf-8')
        gimbal_pitch        = match_gimbal_pitch_degree.group().split(b'"')[1].decode('utf-8')
        gimbal_roll         = match_gimbal_roll_degree.group().split(b'"')[1].decode('utf-8')
        
        return (altitude_absolute, altitude_relative), (flight_yaw, flight_pitch, flight_roll), (gimbal_yaw, gimbal_pitch, gimbal_roll)

def estimate_focal_length(image_width: int, fov_degrees: float) -> float:
    """
    Estimate the focal length given the FOV and the image width.
    
    Parameters:
    - image_width: width of the image in pixels
    - fov_degrees: field of view in degrees
    
    Returns:
    - Estimated focal length in pixels.
    """

    sensor_width_mm = 6.16  # for 1/2.3" sensor, usually around 6.3mm
    focal_length_mm = (sensor_width_mm / 2) / math.tan(np.radians(fov_degrees / 2))
    focal_length_px = (focal_length_mm / sensor_width_mm) * image_width
    return focal_length_px

if __name__ == "__main__":
    filepaths = get_file_path(directory='./data') # 스틸컷이 담긴 폴더명을 인자로 전달합니다.
    for filepath in filepaths:
        # 이미지 로드
        image = cv2.imread(filepath)
        exif_table  = extract_exif(filepath)
        xmp         = extract_xmp(filepath)
        altitude, flight_degree, gimbal_degree = xmp
        flight_yaw, flight_pitch, flight_roll = map(float, flight_degree)
        gimbal_yaw, gimbal_pitch, gimbal_roll = map(float, gimbal_degree)

        fov_degrees = 85
        focal_length = estimate_focal_length(image.shape[1], fov_degrees)

        print(flight_yaw, flight_pitch, flight_roll)
        print(gimbal_yaw, gimbal_pitch, gimbal_roll)

        camera_info = _DictObjHolder({
            "f_x": focal_length,             # focal length x
            "f_y": focal_length,             # focal length y
            "u_x": image.shape[1] / 2,             # optical center x
            "u_y": image.shape[0] / 2,             # optical center y
            "camera_height": abs(float(altitude[1]))*1000,             # camera height in `mm`
            "pitch": gimbal_pitch,             # rotation degree around y
            "yaw": gimbal_yaw,             # rotation degree around z
            "roll": gimbal_roll           # rotation degree around x
        })

        ipm_info = _DictObjHolder({
            "input_width": image.shape[1],
            "input_height": image.shape[0],
            "out_width": image.shape[1],
            "out_height": image.shape[0],
            "left": 0,
            "right": image.shape[1],
            "top": 0,
            "bottom": image.shape[0]
        })

        ipm = IPM(camera_info, ipm_info)
        out_img = ipm(image)
        reverse_out_img = ipm.reverse_ipm(image)
        
        # 이미지를 그대로 BGR 형식으로 저장
        cv2.imwrite('./original_image.png', image)
        cv2.imwrite('./ipm_output.png', out_img)
        cv2.imwrite('./reverse_output.png', reverse_out_img)
