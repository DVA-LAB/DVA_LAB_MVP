
from scipy.spatial import cKDTree
import requests

# CSV 파일 읽기
 # 위도, 경도, LDL-IMSL, LDL-LMSL, LMSL-IMSL, CSV 파일 읽어오기 "LDL(수준(조위)기준면), IMSL(인천만평균해수면), LMSL(지역평균해수면)"
 # ex) 34.50000,125.50000,1.840,1.840, 0.000
def read_csv(file_path):
    data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            values = line.strip().split(',')
            data.append(tuple(map(float, values)))
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

    # API 요청 보내기
    response = requests.get(api_url, params={"ServiceKey": api_key, "ObsCode": obs_code, "Date": date, "ResultType": result_type})

    # API 응답 확인
    if response.status_code == 200:
        # JSON 형태로 응답을 받아옴
        data = response.json()
        # 원하는 데이터 추출
        # print(data)

        target_time = formatted_date + " " + time  # 가져오고자 하는 특정 시간
        tide_levels = data["result"]["data"]

        for record in tide_levels:
            if record["record_time"] == target_time:
                tide_level = record["tide_level"]
                print(f"특정 시간 {target_time}의 조위 값: {tide_level}")
                break
        else:
            print(f"특정 시간 {target_time}의 조위 값이 없습니다.")

    else:
        print("API 요청 실패")
    
    return tide_level
    

def drone_height(file_path, latitude, longitude, absolutaltitude, date, time, ObsCode):
  
  # CSV 파일에서 데이터 읽어오기
  data = read_csv(file_path)

  # KD 트리 생성
  kdtree = create_kd_tree(data)
  distance, index = kdtree.query([latitude, longitude])
  closest_point = data[index]

  tide_level = get_tide_level(ObsCode, date, time)

  # 드론의 높이(Height) =  절대고도(Absolute Altitude) - (조위 - (평균해수면 - 기본수준면))
  height = float(absolutaltitude) - (float(tide_level) - float(closest_point[2]))

  return height

if __name__ == "__main__":

    file_path = "./IMSL_LDL_ETC_jeju.csv"
    ObsCode = "DT_0001"
    date = "20231017"
    time = "00:15:00"
    latitude = "37.45194"
    longitude = "126.59222"
    absolutaltitude = "100"
    height = drone_height(file_path, latitude, longitude, absolutaltitude, date, time, ObsCode)
    print("drone height : ", height)
    

