## 드론 절대고도(Absolute Altitude) 추출 및 해수면 높이 계산

### 전제 조건
- 드론 스틸사진의 절대고도(Absolute Altitude)를 기반으로합니다.
- 절대고도는 평균해수면 기준의 정표고를 사용하며 드론의 기종에 따라 타원체를 기준으로 하는 경우도 있습니다.

### 사용되는 데이터 및 API
1. **드론 스틸사진 데이터**: IMSL_LDL_ETC_jeju.csv 파일을 사용합니다. 이 파일은 다음과 같은 형식으로 구성되어 있습니다:

2. **조위값 API**: [해양수산부 바다누리 해양정보서비스](http://www.khoa.go.kr/oceangrid/khoa/takepart/openapi/openApiObsTideRealDataInfo.do)를 사용하여 특정 날짜에 해당하는 조위값을 가져옵니다.

3. **지오이드고 데이터**: [국토지리정보원 수직기준전환 서비스](https://map.ngii.go.kr/ms/mesrInfo/geoidIntro.do)에서 "KNGeoid18.dat" 파일을 다운로드하여 사용합니다.

### 코드 작성 순서

1. **드론 스틸사진 데이터 추출**
- IMSL_LDL_ETC_jeju.csv 파일에서 위도, 경도, IMSL-LDL, LMSL-LDL, IMSL-LMSL 값을 읽어옵니다.

2. **조위값 가져오기**
- [해양수산부 바다누리 해양정보서비스 API](http://www.khoa.go.kr/oceangrid/khoa/takepart/openapi/openApiObsTideRealDataInfo.do)를 사용하여 특정 날짜에 해당하는 조위값을 가져옵니다.

3. **지오이드고 데이터 활용 (DJI 기종인 경우)**
- [국토지리정보원 수직기준전환 서비스](https://map.ngii.go.kr/ms/mesrInfo/geoidIntro.do)에서 "KNGeoid18.dat" 파일을 다운로드하여 촬영 위치의 지오이드고를 가져옵니다.

4. **높이 계산**
- 조위값과 기준면의 차이를 이용하여 드론과 해수면과의 높이를 계산합니다.
- `드론의 높이(Height) = 절대고도(Absolute Altitude) - (조위 - (평균해수면 - 기본수준면))`

### 참고사항
- 원래 LMSL-LDL에 IMSL-LMSL 값을 더하면 IMSL-LDL이 나와야 하지만 일부 데이터에서는 이러한 값이 나오지 않을 수 있습니다. 이 프로젝트에서는 차이가 크지 않아 큰 문제가 되지 않습니다.
- 데이터의 범위는 제주도 주변 바다를 대상으로 했으며 (위도 33~34.5, 경도 125~127.5) 전국을 대상으로 한다면 데이터를 다시 만들거나 전국단위 gri, grd 파일을 사용해야 합니다.
- 위의 코드 및 API 사용에 앞서 필요한 인증과 권한을 확보하고 사용할 것을 권장합니다.

이렇게 작성된 README 파일은 프로젝트의 사용 방법과 필요한 데이터 및 API 사용법에 대한 상세한 안내를 제공합니다. 필요한 경우 코드 블록과 함께 사용 예제를 추가하여 더 자세한 정보를 제공할 수도 있습니다.