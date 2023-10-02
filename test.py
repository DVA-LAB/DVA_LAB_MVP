import os
import re
from PIL import Image
from PIL.ExifTags import TAGS
from typing import Tuple


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
        xmp_end     = data.find(b'/x:xmpmeta')
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
        

def extract_georeference(exif_table: dict, xmp: Tuple[Tuple, Tuple, Tuple]) -> None:
    # Extract exif value by key
    datetime            = exif_table['DateTime']
    image_width         = exif_table['ExifImageWidth']
    image_height        = exif_table['ExifImageHeight']
    gps_info            = exif_table['GPSInfo']
    make                = exif_table['Make']
    model               = exif_table['Model']
    orientation         = exif_table['Orientation']
    focal_length        = exif_table['FocalLength']
    maker_note          = exif_table['MakerNote']
    
    # Unpack xmp in JPEG
    altitude, flight_degree, gimbal_degree  = xmp
    altitude_absolute, altitude_relative    = altitude
    flight_yaw, flight_pitch, flight_roll   = flight_degree
    gimbal_yaw, gimbal_pitch, gimbal_roll   = gimbal_degree
    
    # Calculate GPS
    lat = 0.0
    lon = 0.0
    alt = 0.0
    
    lat_d, lat_m, lat_s = gps_info[2]
    lon_d, lon_m, lon_s = gps_info[4]
    alt                 = gps_info[6]
    
    lat += float(lat_d)
    lat += float(lat_m) / 60.0
    lat += float(lat_s) / 3600.0
    
    lon += float(lon_d)
    lon += float(lon_m) / 60.0
    lon += float(lon_s) / 3600.0
    
    print (f'이미지 경로\t{filepath}')
    print (f"생성 시간\t{datetime}")
    print (f"이미지 크기\t{image_width}x{image_height}")
    print (f"정렬방향\t{orientation}")
    print (f"제조사/모델\t{make}/{model}")
    print (f"초점거리\t{focal_length}")
    print (f"GPS 좌표\t({lat:7f}, {lon:7f}, {alt})")    
    print (f"절대 고도\t{altitude_absolute}") # this can cause error accumulation becasue of round off
    print (f"상대 고도\t{altitude_relative}")
    print (f"드론 자세\tFlightDegree(Y,P,R):{flight_yaw},{flight_pitch},{flight_roll}")
    print (f"짐벌 각도\tGimbalDegree(Y,P,R):{gimbal_yaw},{gimbal_pitch},{gimbal_roll}\n")


if __name__ == "__main__":
    filepaths = get_file_path(directory='data')
    for filepath in filepaths:
        exif_table  = extract_exif(filepath)
        xmp         = extract_xmp(filepath)
        extract_georeference(exif_table, xmp)