import cv2
import os
from typing import List, Tuple
from tqdm import tqdm

# Constants
ROOT_FOLDER = '/home/dva-mlops/developments/utils/input'
OUTPUT_DIRECTORY = '/mnt/sdb/data/20240927_shipspeed/'
VIDEO_EXTENSIONS = ('.MOV', '.MP4', '.mp4')
JPEG_QUALITY = 100

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
    output_subfolder = os.path.relpath(root, ROOT_FOLDER)

    with cv2.VideoCapture(video_file) as cap:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for frame_number in tqdm(range(frame_count), desc=f"처리 중: {filename}", unit="프레임"):
            ret, frame = cap.read()
            if not ret:
                break

            output_filename = os.path.join(OUTPUT_DIRECTORY, output_subfolder, f'frame_{frame_number:06d}.jpg')
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)

            cv2.imwrite(output_filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])

    return frame_number + 1

def main() -> None:
    """메인 함수"""
    video_files = get_video_files(ROOT_FOLDER, VIDEO_EXTENSIONS)
    
    total_frames = 0
    for i, (root, filename) in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] 비디오 처리 시작: {filename}")
        frames_processed = process_video(root, filename)
        total_frames += frames_processed
        print(f"처리 완료: {filename} - {frames_processed}개의 프레임 추출")

    print(f"\n모든 비디오 파싱이 완료되었습니다. 총 {total_frames}개의 프레임이 추출되었습니다.")

if __name__ == "__main__":
    main()
