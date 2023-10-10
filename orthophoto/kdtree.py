from scipy.spatial import cKDTree

# CSV 파일 읽어오기
def read_csv(file_path):
    data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            values = line.strip().split(',')
            data.append(tuple(map(float, values)))
    return data

# KD 트리 생성 함수
def create_kd_tree(data):
    coordinates = [(row[0], row[1]) for row in data]
    kdtree = cKDTree(coordinates)
    return kdtree

# 파일 경로
file_path = './IMSL_LDL_ETC_jeju.csv'

# CSV 파일에서 데이터 읽어오기
data = read_csv(file_path)

# KD 트리 생성
kdtree = create_kd_tree(data)

# 사용자 입력 받기
user_latitude = float(input("위도를 입력하세요: "))
user_longitude = float(input("경도를 입력하세요: "))

# 입력 좌표와 가장 가까운 이웃 찾기
distance, index = kdtree.query([user_latitude, user_longitude])

# 가장 가까운 이웃의 데이터 가져오기
closest_point = data[index]

# 결과 출력
print(f"입력한 좌표 ({user_latitude}, {user_longitude})에 가장 가까운 값:")
print(f"가장 가까운 좌표: 위도 {closest_point[0]}, 경도 {closest_point[1]}")
print(f"거리: {distance:.4f}")
print(f"가장 가까운 점의 절대고도: {closest_point[2]}")
print(f"가장 가까운 점의 평균해수면: {closest_point[3]}")
print(f"가장 가까운 점의 기준면과의 차이: {closest_point[4]}")