# 특정시간에 해수면 위에 떠 있는 드론의 정확한 높이 값을 추출하기 위한 코드

# 전제 조건
 # 드론 스틸사진의 절대고도(Absolute Altitude)를 이용한다.
 # 절대고도(Absolute Altitude)는 일반적인 평균해수면 기준의 정표고이지만,
 # 드론의 기종에 따라서 실제는 타원체를 기준으로 하는 경우도 있다.


# 01. 드론 스틸사진에서 절대고도(Absolute Altitude), 촬영 시간 등 필요한 메타 데이터를 추출한다.


# 02. 절대고도(Absolute Altitude)가 평균해수면을 기준일 경우
 # 02-1. 사진이 촬영된 시간의 조위값을 가져온다(해양수산부 바다누리 해양정보서비스).
  # http://www.khoa.go.kr/oceangrid/khoa/takepart/openapi/openApiObsTideRealDataInfo.do
 # 02-2. 사진이 촬영된 위치(좌표)의 평균해수면과 기본수준면(조위기준)의 차이 값을 가져온다.(국토지리정보원 육상/해상 높이 연계 서비스)
  # https://map.ngii.go.kr/ms/mesrInfo/geoidIntro.do "파일 입력 기능으로 텍스트 파일 다운로드"
 # 02-3. 조위값과 기준면의 차이를 이용해서 드론과 해수면과의 높이를 구한다. 
 # 드론의 높이(Height) =  절대고도(Absolute Altitude) - (조위 - (평균해수면 - 기존수준면))



# 03. 절대고도(Absolute Altitude)가 타원체고 일 경우(DJI 기종)
 # 03-1. "KNGeoid18.dat"에서 촬영 위치(좌표)의 지오이드고를 가져온다(국토지리정보원 수직기준전환 서비스에서 다운로드).
  # https://map.ngii.go.kr/ms/mesrInfo/geoidIntro.do 
##이후의 과정은 02.의 순서를 그대로 따른다.

# 04. 최종으로 계산한 드론과 해수면의 높이차이를 반환한다.

