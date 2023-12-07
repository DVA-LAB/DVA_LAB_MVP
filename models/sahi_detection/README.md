# Sahi와 Detection Model을 연결

## In/Out 명세

- Input: Request 시 받은 파싱된 이미지 폴더, 모델 결과를 저장할 csv 경로
- output: 직접적인 request에 대한 응답 구현 필요 - 내부적으로는 csv 파일에 결과물 저장

## 메인 모델

- yolov5 

```markdown
```bash
# 명령 예시
curl -X POST "http://112.216.237.124:8000/sahi/inference" -H "Content-Type: application/json" -d '{"img_path": "/home/dva3/workspace/output/test/test01", "csv_path": "./test.csv"}'