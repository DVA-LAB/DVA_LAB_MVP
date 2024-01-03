from urllib.request import urlopen
import xmltodict
import json
from haversine import haversine
import pandas as pd


# DT_0023 : moseul-po, DT_0010 : seogwi-po, DT_0020 : seongsan-po, DT_0004 : jeju
khoa_coord = {'DT_0023': [33.214, 126.251], 'DT_0004': [33.527, 126.543],
              'DT_0022': [33.474, 126.927], 'DT_0010': [33.24, 126.561]}


# get geoid height from KNGeoid18 data
# input target point must be two column list type of [latitude, longitude]
def get_geoid_hgt(target_pt):
    """
        국토지리정보원에서 제공하는 KNGeoid18 데이터로부터 geoid의 높이를 구합니다.

        Args
            - target_pt (list): [latitude, longitude]의 두 컬럼으로 구성된 입력 포인트

        Return
            - hgt_geoid (list): geoid의 높이 정보 리스트
    """

    with open('utils/log_sync/KNGeoid18.dat') as geoid_dir:
        geoid_file = geoid_dir.read()
    geoid = [file.split('\t') for file in geoid_file.split('\n')]

    dist_list = []
    for point in geoid[:-1]:
        dist_list.append([haversine(target_pt, [float(coord) for coord in point[:2]]), float(point[2])])

    hgt_geoid = sorted(dist_list, key=lambda x: x[0])[0][-1]

    return hgt_geoid


# get adjacent khoa observation point
# input target point must be two column list type of [latitude, longitude]
def get_obs(target_pt):
    """
        입력 좌표를 국립해양조사원(khoa)의 여러 관측점 중 가장 가까운 관측점과의 거리를 계산합니다.
    
        Args
            - target_pt (list): 위도, 경도 두 컬럼으로 구성된 배열

        Return
            - 여러 관측점 중 가장 가까운 관측점과의 최단 거리 (float)
    """

    dist_obs = {}
    for obs, coord in khoa_coord.items():
        dist_obs[obs] = haversine(coord, target_pt)

    return sorted(dist_obs.items(), key=lambda x: x[1])[0][0]


# get tide level from khoa openapi
# date format : %Y%m%d%H%M%S & string
def get_level(date, obs_code='DT_0023'):
    """
        국립해양조사원(khao)의 OpenAPI를 활용하여 조위를 구합니다.

        Args
            - date (str): 날짜
            - obs_code (str): 관측코드

        Return
            - 특정 시간에서의 조위 값 (int)
    """

    khoa_url = "http://www.khoa.go.kr/api/oceangrid/tideObs/search.do?" + \
               "ServiceKey=JXRQtwmuwRIKOblp9dTWww==" + \
               "&ObsCode=" + obs_code + "&Date=" + date[:8] + "&ResultType=xml"

    resp = urlopen(khoa_url)
    resp_body = resp.read().decode("utf-8")
    xml_parse = xmltodict.parse(resp_body)
    xml_dict = json.loads(json.dumps(xml_parse))

    df_tide = pd.DataFrame(columns=['time', 'tide_level'])
    for idx, case in enumerate(xml_dict['result']['data']):
        df_tide.loc[idx] = [case['record_time'].split(' ')[-1], case['tide_level']]

    q_time = date[8:10] + ':' + date[10:12] + ':' + '00'

    return int(df_tide[df_tide['time'] == q_time]['tide_level'])


# execute main function
# ========== main function ==========
def get_offset(osd_info, date):
    """
        해수면으로부터의 드론 높이를 계산합니다.

        Args
            - osd_info (tuple): (OSD.latitude, OSD.longitude, HOME.latitude, HOME.longitude)로 구성된 정보
            - date (str): 비행 날짜

        Return
            - osd_hgt_offset (float): 해수면으로부터의 드론 높이
    """
    
    osd_lat, osd_lon, home_lat, home_lon = osd_info
    # osd_lat, osd_lon, home_lat, home_lon =  33.2629, 126.1815, 33.2632, 126.1814
    # date = '20231015171233'

    osd_coord = [osd_lat, osd_lon]
    home_coord = [home_lat, home_lon]

    obs_name = get_obs(osd_coord)

    # adjusted height = (compared to home) drone relative height + \
    # (home point absolute height - nearby khoa station absolute height) + \
    # (tide level observation maximum - tide level observed)
    # In order to get absolute height, we used height from ngii
    # assumption : height of sea is identical
    osd_hgt_offset = ((get_geoid_hgt(home_coord) - get_geoid_hgt(khoa_coord[obs_name])) + \
                     (400 - get_level(date, obs_name)) / 100.)

    return osd_hgt_offset