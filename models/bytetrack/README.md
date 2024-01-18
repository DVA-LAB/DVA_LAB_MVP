# ByteTrack - Object Tracking
본 객체추적 모델은 객체탐지 모델과 이상탐지 모델의 결과를 앙상블하여 객체추적을 수행합니다.

## 기능
* 입력받은 bbox를 기반으로 객체추적을 수행 후 결과 bbox를 생성합니다.
* BEV 시각화를 위한 bbox를 bev_points.csv 파일에 저장합니다.
* 다수 돌고래의 bbox를 결합하여 하나의 bbox로 생성한 뒤 bev_points.csv 파일에 저장합니다.

## API 참조
* 함수: inference (api.routers.inference_router.py)
* 설명: 객체추적을 위해 객체탐지와 이상탐지 결과가 결합된 bbox를 입력받고 tracking을 수행 후 생성된 결과 bbox 경로를 반환합니다.
* 입력: request_body: 객체추적 입력 파일과 출력 파일 경로를 포함하는 TrackingRequest 인스턴스.
* 출력: result_path: 객체추적 결과 bbox가 저장된 경로

## 사용 예시
```shell
!python app.py
```

## 설치
```bash
pip install -r requirements.txt
```

만약 위 과정이 수행되지 않을 경우 Step2 대신 아래 절차를 통해 환경을 구성하세요.
```shell
git clone https://github.com/ifzhang/ByteTrack.git
cd ByteTrack
pip3 install -r requirements.txt
python3 setup.py develop
```


## 시작하기
1) TrackingRequest 인스턴스로 inference 함수를 호출합니다.
2) 반환된 result_path를 필요에 따라 처리합니다.


```python
import requests
import json

# API 엔드포인트 설정
url = "http://localhost:8004/bytetrack/track"  # 'localhost:8004' 부분은 실제 서버 주소로 변경해야 합니다.

# TrackingRequest에 맞춰 데이터 준비
data = {
    "det_result_path": "<input_bbox_path>",
    "result_path": "<output_bbox_path>",
}

# POST 요청 보내기
response = requests.post(url, json=data)

# 응답 출력
print("Status Code:", response.status_code)
print("Response Body:", response.json())
```