import cv2
import os
import stat
import subprocess
from typing import List, Tuple
from tqdm import tqdm

# Constants
ROOT_FOLDER = '/home/dva-mlops/developments/utils/input'
OUTPUT_DIRECTORY = '/mnt/sdb/data/'
VIDEO_EXTENSIONS = ('.MP4', '.mp4')
JPEG_QUALITY = 100
DIRECTORY_PERMISSIONS = 0o755  # rwxr-xr-x
FILE_PERMISSIONS = 0o644  # rw-r--r--

def ensure_directory(path: str) -> None:
    """디렉토리가 존재하지 않으면 생성하고 권한을 설정합니다."""
    try:
        os.makedirs(path, mode=DIRECTORY_PERMISSIONS, exist_ok=True)
    except PermissionError:
        print(f"Error: '{path}' 디렉토리를 생성하거나 권한을 설정할 수 없습니다.")
        print("sudo 권한으로 디렉토리를 생성하고 권한을 설정합니다.")
        
        commands = [
            f"sudo mkdir -p {path}",
            f"sudo chown $USER:$USER {path}",
            f"sudo chmod 755 {path}"
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError:
                print(f"Error: '{cmd}' 명령 실행 중 오류가 발생했습니다.")
                exit(1)
        
        print("디렉토리 생성 및 권한 설정이 완료되었습니다.")

def get_video_files(root_folder: str, extensions: Tuple[str, ...]) -> List[Tuple[str, str]]:
    """비디오 파일 목록을 반환합니다."""
    video_files = []
    for root, _, files in os.walk(root_folder):
        for filename in files:
            if filename.endswith(extensions):
                video_files.append((root, filename))
    return video_files

def process_video(root: str, filename: str) -> int:
    """비디오를 프레임 단위로 처리하고 저장합니다. 처리된 프레임 수를 반환합니다."""
    video_file = os.path.join(root, filename)
    video_name = os.path.splitext(filename)[0]
    output_path = os.path.join(OUTPUT_DIRECTORY, video_name)
    
    ensure_directory(output_path)

    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        print(f"Error: 비디오 파일을 열 수 없습니다 - {video_file}")
        return 0

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 0

    try:
        for frame_number in tqdm(range(frame_count), desc=f"처리 중: {filename}", unit="프레임"):
            ret, frame = cap.read()
            if not ret:
                break

            output_filename = os.path.join(output_path, f'frame_{frame_number:06d}.jpg')
            cv2.imwrite(output_filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
            os.chmod(output_filename, FILE_PERMISSIONS)
    finally:
        cap.release()

    return frame_number + 1

def main() -> None:
    """메인 함수"""
    ensure_directory(OUTPUT_DIRECTORY)
    video_files = get_video_files(ROOT_FOLDER, VIDEO_EXTENSIONS)
    
    if not video_files:
        print(f"Error: '{ROOT_FOLDER}'에서 비디오 파일을 찾을 수 없습니다.")
        return

    total_frames = 0
    for i, (root, filename) in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] 비디오 처리 시작: {filename}")
        frames_processed = process_video(root, filename)
        total_frames += frames_processed
        print(f"처리 완료: {filename} - {frames_processed}개의 프레임 추출")

    print(f"\n모든 비디오 파싱이 완료되었습니다. 총 {total_frames}개의 프레임이 추출되었습니다.")

if __name__ == "__main__":
    main()
