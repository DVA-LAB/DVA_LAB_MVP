import requests

# API 요청을 보낼 주소
api_url = "http://www.khoa.go.kr/api/oceangrid/tideObs/search.do"

# API 키
api_key = "YmHupI3Nga4UvQn7gONpA=="

# 요청 파라미터 설정
obs_code = "DT_0001"
date = "20231017"
result_type = "json"

# API 요청 보내기
response = requests.get(api_url, params={"ServiceKey": api_key, "ObsCode": obs_code, "Date": date, "ResultType": result_type})

# API 응답 확인
if response.status_code == 200:
    # JSON 형태로 응답을 받아옴
    data = response.json()
    print(data)
    # 원하는 데이터 추출
    target_time = "2023-10-17 00:15:00"  # 가져오고자 하는 특정 시간
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

