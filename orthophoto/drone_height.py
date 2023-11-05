
from scipy.spatial import cKDTree
import requests

# CSV 파일 읽기
 # 위도, 경도, LDL-IMSL, LDL-LMSL, LMSL-IMSL, CSV 파일 읽어오기 "LDL(수준(조위)기준면), IMSL(인천만평균해수면), LMSL(지역평균해수면)"
 # ex) 34.50000,125.50000,1.840,1.840, 0.000
def read_csv_comma(file_path):
    data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            values = line.strip().split(',')
            data.append(tuple(map(float, values)))
    return data

def read_csv_tab(file_path):
    data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            values = line.strip().split('\t')
            data.append(tuple(map(float, values)))
    return data

#obscode 파일 읽기
def read_csv_tab_obscode(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split('\t')
            obs_code = parts[0]
            name = parts[1]
            latitude = float(parts[2])
            longitude = float(parts[3])
            data.append((latitude, longitude, obs_code, name))
    return data

# KD 트리 생성 함수
def create_kd_tree(data):
    coordinates = [(row[0], row[1]) for row in data]
    kdtree = cKDTree(coordinates)
    return kdtree


# API를 이용해 조위값 가져오는 함수 #time은 분단위로 내림
def get_tide_level(ObsCode, date, time):

    # API 요청을 보낼 주소
    api_url = "http://www.khoa.go.kr/api/oceangrid/tideObs/search.do"

    # API 키
    api_key = "YmHupI3Nga4UvQn7gONpA=="

    # 요청 파라미터 설정
    obs_code = ObsCode
    date = date
    result_type = "json"
    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}" #요청할 때 날짜형식과 결괏값의 날짜 형식이 달라서 결과 찾을 날짜 형식으로 변환

    #print(f"날짜 확인 포맷: {formatted_date}") ##값 확인

    # API 요청 보내기
    response = requests.get(api_url, params={"ServiceKey": api_key, "ObsCode": obs_code, "Date": date, "ResultType": result_type})

    # API 응답 확인
    if response.status_code == 200:
        # JSON 형태로 응답을 받아옴
        data = response.json()
        # 원하는 데이터 추출
        # print(data)

        target_time = formatted_date + " " + time  # 가져오고자 하는 특정 시간
        print(f"요청 조위의 시간: {target_time}")
        tide_levels = data["result"]["data"]

        for record in tide_levels:
            if record["record_time"] == target_time:
                tide_level = record["tide_level"]
                #print(f"특정 시간 {target_time}의 조위 값: {tide_level}")
                break
        else:
            print(f"특정 시간 {target_time}의 조위 값이 없습니다.")

    else:
        print("API 요청 실패")
    
    return tide_level
    

def drone_height_withabsaltitude(latitude, longitude, absolutaltitude, date, time, tag):

    latitude= float(latitude)
    longitude= float(longitude)
    # 높이 보정을 위한 해수면의 차이 값을 읽어옴CSV 파일에서 데이터 읽어오기 file_sealand_difference
    d_data = read_csv_comma("C:\dkc_dev\co_dva_lab\DVA_LAB\orthophoto\IMSL_LDL_ETC_jeju.csv")

    # "IMSL_LDL_ETC_jeju.csv" 경위도 범위의 유효성을 검사하기 위해 최대 최소값 찾기
    latitude_max = max(d_data, key=lambda x: x[0])[0]
    latitude_min = min(d_data, key=lambda x: x[0])[0]
    longitude_max = max(d_data, key=lambda x: x[1])[1]
    longitude_min = min(d_data, key=lambda x: x[1])[1]

    # print(f"Latitude 최대값: {latitude_max}")
    # print(f"Latitude 최소값: {latitude_min}")
    # print(f"Longitude 최대값: {longitude_max}")
    # print(f"Longitude 최소값: {longitude_min}")

    if not (latitude_min <= latitude <= latitude_max and
        longitude_min <= longitude <= longitude_max):
        print("입력된 경위도 정보가 제주도 부근이 아닙니다. 해당 함수는 부근에 한합니다.")
        print("따라서 해수면의 차이는 보정되지 않고 조위값에 따른 보정만 적용됩니다.")
        IMSL_LDL = 0
        LMSL_LDL = 0
        IMSL_LMSL = 0
        print(f"IMSL_LDL: {IMSL_LDL}")

    else:
    # KD 트리 생성
        kdtree = create_kd_tree(d_data)
        distance, index = kdtree.query([latitude, longitude])
        closest_point = d_data[index]
        IMSL_LDL =closest_point[2]
        LMSL_LDL =closest_point[3]
        IMSL_LMSL =closest_point[3]
        print(f"Latitude(위도): {latitude}, Longitude(경도): {longitude}, Absolut Altitude: {absolutaltitude}m")
        print("IMSL(인천만평균해수면) - LDL(기본수준면): ", closest_point[2])
        print("LMSL(지역별평균해수면) - LDL(기본수준면): ", closest_point[3])
        print("IMSL(인천만평균해수면) - LMSL(지역별평균해수면): ", closest_point[4])

    
    # 조위값을 보정하기 위해서 CSV 파일에서 조위관측소 목록을 읽고 해당하는 obscode를 찾고, API로 조위값을 가져옴
    o_data = read_csv_tab_obscode("C:\dkc_dev\co_dva_lab\DVA_LAB\orthophoto\obscode_list.csv")
    kdtree = create_kd_tree(o_data)
    distance, index = kdtree.query([latitude, longitude])
    closest_point = o_data[index]
    ObsCode =closest_point[2]
    name =closest_point[3]
    print(f"ObsCode: {ObsCode}, name: {name}")

    tide_level = get_tide_level(ObsCode, date, time)
    print(f"조위값(m): {float(tide_level)*0.01}m")

    #태그가 S, E 에 따라서 고도를 계산하는 방식이 달라짐
    if(tag == "S"):
        # 드론의 높이(Height) =  절대고도(Absolute Altitude) - (조위 - (인천만의평균해수면(IMSL) - 기본수준면(LDL)))
        height = float(absolutaltitude) - (float(tide_level)*0.01 - float(IMSL_LDL))

    else:
        #지오이드고를 읽어서 절대높이를 조정하는 코드
        g_data = read_csv_tab("C:\dkc_dev\co_dva_lab\DVA_LAB\orthophoto\KNGeoid18.csv")
        kdtree = create_kd_tree(g_data)
        distance, index = kdtree.query([latitude, longitude])
        g_closest_point = g_data[index]
        geoid_height = g_closest_point[2]
        print("지오이드고: ", geoid_height)

        # 드론의 높이(Height) =  (절대고도(Absolute Altitude) - 지오이드고) - (조위 - (인천만의평균해수면(IMSL) - 기본수준면(LDL)))
        height = (float(absolutaltitude) - float(geoid_height)) - (float(tide_level)*0.01 - float(IMSL_LDL))

    return height

if __name__ == "__main__":

    #file_sealand_difference = "./IMSL_LDL_ETC_jeju.csv"
    #이미지 메타(exif/xmp)에서 정보를 추출하거나, SRT/드론로그 정보에서 해당 정보를 전달받아서 사용하면됨
    date = "20230518"
    time = "00:15:00" 
    latitude = "33.45194"
    longitude = "126.59222"
    absolutaltitude = "100"
    tag = "S" #S=Sea(평균해수면기준 높이(정표고)), E=Ellipsoid(타원체고) 입력되는 높이의 기준면이 평균해수면인지, 타원체인지 구분하는 태그
    height = drone_height_withabsaltitude(latitude, longitude, absolutaltitude, date, time, tag)
    print("drone height : ", height)
    

