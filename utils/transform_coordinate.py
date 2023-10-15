import numpy as np
from math import sin, cos


def get_coordinate_3d(zc, intrinsic_parameter, extrinsic_parameter, coordinate_pixel):
    coordinate_world = zc * extrinsic_parameter.T * intrinsic_parameter.T * coordinate_pixel
    return coordinate_world


if __name__ == "__main__":
    # 카메라 내부 파라미터 (초점 거리, 주점, 왜곡계수) | cv2.calibrateCamera()로 대체 가능
    fx                  = False # focal length x
    fy                  = False # focal length y
    cx                  = False # principal point x
    cy                  = False # principal point y
    skew_c              = False # skew coefficient
    zc                  = False # distance between the lens aperture and the plane.

    intrinsic_parameter = np.matrix([[fx, skew_c*fx,  cx,
                                    0,  fy,         cy,
                                    0,  0,          1]])

    # 카메라 외부 파라미터
    gimb_tilt   = False
    gimb_yaw    = False

    rotation_matrix_nb  = np.matrix([[]])
    rotation_vector_nnc = np.matrix([])
    rotation_matrix_cm  = np.matrix([[0, 1, 0
                                    -1, 0, 0,
                                    0, 0, 1]])
    rotation_matrix_mb  = np.matrix([[cos(gimb_yaw) * cos(gimb_tilt),   sin(gimb_yaw) * cos(gimb_tilt),  -sin(gimb_tilt),
                                     -sin(gimb_yaw)                 ,   cos(gimb_yaw)                 ,  0              ,
                                      cos(gimb_yaw) * sin(gimb_tilt),   sin(gimb_yaw) * sin(gimb_tilt),  cos(gimb_tilt)]])

    rotation_matrix_cn = np.matmul(rotation_matrix_nb, np.matmul(rotation_matrix_cm, rotation_matrix_mb).T).T
    extrinsic_parameter = rotation_matrix_cn - np.matmul(rotation_matrix_cn, rotation_vector_nnc)

    # 픽셀 좌표계 점
    r, s = (False, False)
    coordinate_pixel = np.matrix([r,
                                s,
                                1])
    
    # 2차원 좌표 → 3차원 좌표 변환
    coorindate_world = get_coordinate_3d(zc, intrinsic_parameter, extrinsic_parameter, coordinate_pixel)