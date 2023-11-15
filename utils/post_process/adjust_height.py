import sys
from urllib.request import urlopen
import xmltodict
import json
from haversine import haversine
import pandas as pd


# DT_0023 : 모슬포, DT_0010 : 서귀포, DT_0020 : 성산포, DT_0004 : 제주
khoa_coord = {'DT_0023': [33.214, 126.251], 'DT_0004': [33.527, 126.543],
              'DT_0022': [33.474, 126.927], 'DT_0010': [33.24, 126.561]}


# get geoid height from KNGeoid18 data
# input target point must be two column list type of [latitude, longitude]
def get_geoid_hgt(target_pt):
    with open('./KNGeoid18.dat') as geoid_dir:
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
    dist_obs = {}
    for obs, coord in khoa_coord.items():
        dist_obs[obs] = haversine(coord, target_pt)

    return sorted(dist_obs.items(), key=lambda x: x[1])[0][0]


# get tide level from khoa openapi
# date format : %Y%m%d%H%M%S & string
def get_level(date, obs_code='DT_0023'):
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
def main(argv):
    # get argument
    args = argv
    if len(args) != 6:
        print("[ERROR] Insufficient argument")

    osd_coord = [float(args[0]), float(args[1])]
    # osd_coord = [33.2629, 126.1815]
    osd_hgt = float(args[2])
    # osd_hgt = 19.87
    home_coord = [float(args[3]), float(args[4])]
    # home_coord = [33.2632, 126.1814]
    date = str(args[5])
    # date = '20231015171233'

    obs_name = get_obs(osd_coord)

    # 보정된 고도 : (홈 포인트 기준) 드론 상대 고도 + (홈포인트 절대 고도 - 인근 조위관측소 절대 고도) + (조위 관측 최댓값 - 관측 조위)
    # 절대 고도 산출을 위해 국토지리정보원 지오이드고 사용
    # 가정 : 드론 & 조위관측소 바다 높이는 동일
    osd_hgt_adjust = osd_hgt + ((get_geoid_hgt(home_coord) - get_geoid_hgt(khoa_coord[obs_name])) + \
                                (400 - get_level(date, obs_name)) / 100.)
    print("Adjusted height : ", osd_hgt_adjust)

    return osd_hgt_adjust


if __name__ == "__main__":
    main(sys.argv[1:])