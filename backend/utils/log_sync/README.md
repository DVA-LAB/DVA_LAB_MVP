# Sync module
드론 조종기 로그 파일과 SRT 파일을 매칭하는 모듈

## Files
```
adjust_height.py
adjust_log.py
KNGeoid18.dat
README.md
```
### 1. Usage
```python
python adjust_log.py ./csv_srt_path
```
- 디렉토리를 변수로 입력해줘야하며, 디렉토리에는 CSV 파일과 SRT 파일이 위치해야합니다.
- 드론 비행로그인 CSV 파일은 하나만 필요하고, SRT 파일 수는 상관없습니다.
- 입력변수로 설정한 디렉토리에 SRT와 매칭된 CSV 자료가 저장되며, CSV 파일명은 SRT 파일명과 동일합니다.

### 2. Input & output
| Contents | Data                           | etc. |
|:----------|:-------------------------------|:-----|
| Input | CSV & SRT directory            | -    |
| Output | CSV files | -    |
