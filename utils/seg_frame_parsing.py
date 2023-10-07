import cv2
import os

# 루트 폴더 경로
root_folder = '/Users/seowoohan/Desktop/Developments/DVA_LAB/DVA_LAB/input'

# 출력 이미지 저장 경로
output_directory = '/Users/seowoohan/Desktop/Developments/DVA_LAB/DVA_LAB/output/Datasets/AD/RAW/'

# 처리할 비디오 파일 확장자
video_extensions = ['.MOV', '.MP4']

# 시간 간격 설정 (40초)
frame_interval = 40

# 루트 폴더 및 하위 폴더 내의 모든 비디오 파일에 대한 루프
for root, _, files in os.walk(root_folder):
    for filename in files:
        if any(filename.endswith(ext) for ext in video_extensions):
            video_file = os.path.join(root, filename)

            # OpenCV 비디오 캡처 객체 생성
            cap = cv2.VideoCapture(video_file)

            frame_number = 0

            while True:
                ret, frame = cap.read()

                # 비디오의 끝에 도달하면 루프 종료
                if not ret:
                    break

                # 20초마다 프레임 저장
                if frame_number % int(frame_interval * cap.get(cv2.CAP_PROP_FPS)) == 0:
                    output_subfolder = os.path.relpath(root, root_folder)  # 루트 폴더 이후의 경로를 가져옴
                    filename_without_extension = os.path.splitext(filename)[0]
                    output_filename = os.path.join(output_directory, output_subfolder, f'{filename_without_extension}_frame_{int(frame_number/int(frame_interval * cap.get(cv2.CAP_PROP_FPS))):05d}.PNG')
                    
                    # 출력 폴더가 없는 경우 생성
                    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

                    cv2.imwrite(output_filename, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # PNG 형식으로 저장

                frame_number += 1

            # 작업 완료 후 객체 해제
            cap.release()

print("모든 비디오 파싱이 완료되었습니다.")