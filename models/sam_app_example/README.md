# FastAPI - SAM
이 서비스는 FastAPI를 사용하여 segmentation API를 제공합니다. image frame과 bboxes가 주어지면, masks를 반환합니다.

## 기능
* 요청 및 응답 처리를 위한 FastAPI.
* 데이터 유효성 검사 및 데이터 직렬화/역직렬화를 위한 Pydantic.
* 더 나은 모듈성과 테스트 가능성을 위한 의존성 주입.

## 사용 방법
```shell
!python app.py
```
* API는 http://0.0.0.0:8000 에서 사용할 수 있습니다. 
* 자동 인터랙티브 API 문서는 http://0.0.0.0:8000/docs 에서 접근할 수 있습니다.

## API 엔드포인트
### POST /inference:
* 주어진 입력 데이터에 대해 세그멘테이션을 수행합니다.
* 요청 본문:
  * frame_count (int): 프레임 카운트.
  * bboxes (list[list[float]]): [x_min, y_min, x_max, y_max] 형식의 바운딩 박스 리스트.
* 응답 본문:
  * masks (list[list[list[bool]]]): 2D 마스크 배열의 리스트.
  
## 모델 변경하기 (Object Detection 또는 Tracking 모델로 변경)
* 모델을 Object Detection이나 Tracking 모델로 변경하려면 아래 부분들을 수정해야 합니다:
  * Pydantic Models (interface/request): Request와 Response 클래스를 새 모델의 입력 및 출력 요구 사항에 맞게 수정하세요.
  * Router (api/routers): 라우터에서 요청을 처리하고 응답을 반환하는 로직을 수정하세요. 이에는 새 모델을 호출하고 결과를 처리하는 로직이 포함될 수 있습니다.
  * Service Logic (api/services): 서비스 로직을 수정하여 새 모델의 요구 사항에 맞게 처리하도록 하세요.
  * 전처리 및 후처리 코드: 모델의 입력 및 출력 요구 사항에 따라 전처리 및 후처리 코드를 수정하세요.

## 테스트
API를 테스트하려면 제공된 예제 스크립트를 사용하거나 curl 또는 Postman과 같은 도구를 사용할 수 있습니다.
```python
frame_bytes = cv2_img.tobytes()
frame_count = 1

# Send a POST request to the API
response = requests.post(
    'http://0.0.0.0:8000/sam/inference',
    headers={'Content-Type': 'application/octet-stream'},
    params={'frame_count': frame_count},
    data=frame_bytes
)

# Check for a valid response
if response.status_code == 200:
    result = response.json()
    print(result)
else:
    print(f'Failed to call API: {response.status_code}')
```