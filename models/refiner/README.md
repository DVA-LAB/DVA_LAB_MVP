# Refiner
COCO format의 bbox label의 정제를 위한 모듈

## 1. 작동 원리
* 주어진 COCO label (bboxes)를 사용하여 SAM으로 segment를 구한 후, 해당 mask에 가장 fit한 horizontal bbox로 수정함

## 2. 예시 사용 (api 이용)
```python
import requests

url = 'http://localhost:8000/refinement'  # 동일 서버에서 app.py를 실행시켜놓은 경우

# 보낼 데이터
data = {
    "img_path": "/mnt/coco_form/train",
    "json_file": "/mnt/coco_form/train.json"
}

# POST 요청 보내기
response = requests.post(url, json=data)

# 응답 출력
print(response.status_code)
print(response.json())
```

## 2. 코드 사용
```python
from api.services import Refiner

refiner = Refiner("cuda")

imgs_path = "/mnt/coco_form/train"
json_path = "/mnt/coco_form/train.json"
updated_data = refiner.do_refine(json_path, imgs_path)
# refiner.save_update(updated_data, "refined_train.json")  # 저장이 필요한 경우
```



