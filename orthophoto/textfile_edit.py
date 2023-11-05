# 추출할 레코드를 저장할 빈 리스트 생성
filtered_records = []

# 텍스트 파일 열기
with open('./KNGeoid18.dat', 'r') as file:
    # 파일의 각 라인에 대해 반복
    for line in file:
        # 라인을 탭으로 구분된 필드로 분리
        latitude, longitude, altitude = map(float, line.strip().split('\t'))
        # 높이 값이 16에서 17 사이에 있는 레코드를 추출
        if 33 <= latitude <= 34.5 and 125.5 <= longitude <= 127.5:
            filtered_records.append((latitude, longitude, altitude))

# 추출된 레코드를 파일에 저장 (일련번호, 자리수를 맞추고 공백으로 구분)
with open('./input_jeju.txt', 'w') as output_file:
    for idx, record in enumerate(filtered_records, start=1):
        # 일련번호를 6자리로 포맷팅하고, 나머지 필드의 자리수를 맞추고 공백으로 구분하여 파일에 쓰기
        output_file.write('{:06d} {:.5f} {:.5f} {:.3f}\n'.format(idx, record[0], record[1], record[2]))
        # 또는 f-string을 사용할 수도 있습니다:
        # output_file.write(f'{idx:06d} {record[0]:.5f} {record[1]:.5f} {record[2]:.3f}\n')