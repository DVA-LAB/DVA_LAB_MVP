# Sahi와 Detection Model을 연결

## In/Out 명세

- Input: Request 시 받은 파싱된 이미지 폴더, 모델 결과를 저장할 csv 경로
- output: 직접적인 request에 대한 응답 구현 필요 - 내부적으로는 csv 파일에 결과물 저장

## 메인 모델

- yolov5 

```markdown
```bash
# 명령 예시
# sliced image save mode
curl -X POST "http://112.216.237.124:8001/sahi/inference" -H "Content-Type: application/json" -d '{"img_path": "/home/dva3/workspace_temp/output/test/test01", "csv_path": "./test.csv", "sliced_path":"./test_sliced"}'

# No save mode
curl -X POST "http://112.216.237.124:8001/sahi/inference" -H "Content-Type: application/json" -d '{"det_result_path": "/home/dva3/API/DVA_LAB/models/bytetrack_jy/example.txt", "result_path": "./test.txt"}'
```

## 기능
* 돌고래 / 선박 탐지 및 추적
* sahi slicing에 의한 small object 탐지 성능 향상
* Input : 1024 size로 slicing 된 frame( 30 / 5 ) 경로
* Output : frame_number, class_id, x, y, w, h, confi_score

## Benchmark
| Model | Size | mAP<br/>0.5 | FPS<br/>(original) | FPS<br/>(tensorrt) | Params<br/><sup> (M)|
| :----------------------------------------------------------- | ---- | :----------------------- | --------------------------------------- | ---------------------------------------- | -------------------- |
| **YOLOv8-s** | 1024  |    84.99  | 1.6 | 0      | 11.2    | 
| **YOLOv8-m** | 1024  |   86.75    | 0.87       | 0     | 25.9     |
| **YOLOv8-l** | 1024  |     87.74      | 0.45       | 0        | 43.7     | 
 
