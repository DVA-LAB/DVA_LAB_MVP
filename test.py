import os
import re
from PIL import Image
from PIL.ExifTags import TAGS


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


def get_georeferencing(exif_table: str) -> None:
    datetime            = exif_table['DateTime']
    image_width         = exif_table['ExifImageWidth']
    image_height        = exif_table['ExifImageHeight']
    gps_info            = exif_table['GPSInfo']
    make                = exif_table['Make']
    model               = exif_table['Model']
    orientation         = exif_table['Orientation']
    focal_length        = exif_table['FocalLength']
    maker_note          = str(exif_table['MakerNote'])
    
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
    
    pattern_gimbal_degree   = re.compile(r'GimbalDegree\(Y,P,R\):(-?\d+),(-?\d+),(-?\d+)')
    pattern_flight_degree   = re.compile(r'FlightDegree\(Y,P,R\):(-?\d+),(-?\d+),(-?\d+)')
    pattern_flight_speed    = re.compile(r'FlightSpeed\(X,Y,Z\):(-?\d+),(-?\d+),(-?\d+)')
    match_gimbal_degree     = pattern_gimbal_degree.search(maker_note)
    match_flight_degree     = pattern_flight_degree.search(maker_note)
    match_flight_speed      = pattern_flight_speed.search(maker_note)
    
    if match_flight_degree:
        print (f"드론 자세\t{match_flight_degree.group()}")
    if match_flight_degree:
        print (f"짐벌 각도\t{match_gimbal_degree.group()}")
    if match_flight_speed:
        print (f"비행 속도\t{match_flight_speed.group()}")
    
    print('\n')

    
if __name__ == "__main__":
    filepaths = get_file_path(directory='data')
    for filepath in filepaths:
        exif_table = extract_exif(filepath)
        get_georeferencing(exif_table)