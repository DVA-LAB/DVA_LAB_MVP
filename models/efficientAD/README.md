# FastAPI - Anomaly Segmentation
이 이상 탐지 세그먼테이션 모델은 주어진 프레임 경로에서 이상을 식별하고 세그먼트하는 데에 사용됩니다.

## 기능
* 요청 및 응답 처리를 위한 FastAPI.
* 데이터 유효성 검사 및 데이터 직렬화/역직렬화를 위한 Pydantic.
* 더 나은 모듈성과 테스트 가능성을 위한 의존성 주입.

## API 참조 (이상 탐지 추론)
* 함수: anomaly_inference
* 설명: 제공된 프레임 경로를 처리하여 이상을 감지하고 세그먼트합니다.
* 입력: request_body: 분석할 프레임 경로를 포함한 SegRequest 인스턴스.
* 출력 (TBA): res_img, res_boxes, res_scores


## 사용 예시
```shell
!python app.py
```

## 시작하기
1) api/services/ 경로에서 pip install -e . 명령어를 실행합니다. 
2) 추가로 필요한 requirements.txt로 설치합니다.
3) SegRequest 인스턴스로 anomaly_inference 함수를 호출합니다.
4) 반환된 res_img, res_boxes, res_scores를 필요에 따라 처리합니다.
```python
import requests
import json

# API 엔드포인트 설정
url = "http://localhost:8000/anomaly/inference"  # 'localhost:8000' 부분은 실제 서버 주소로 변경해야 합니다.

# SegRequest에 맞게 데이터 준비
data = {
    "frame_path": "your_frame_path_here"  # 'your_frame_path_here'를 실제 프레임 경로로 대체하세요.
}

# POST 요청 보내기
response = requests.post(url, json=data)

# 응답 출력
print("Status Code:", response.status_code)
print("Response Body:", response.json())
```

## 예시 결과
TBA
