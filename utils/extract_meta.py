import os
import cv2
import exifread

import os
import cv2
import exifread

def parsing_srt_file(lines):
    subtitles = []
    subtitle = None

    for line in lines:
        line = line.strip()
        if not line:  # 빈 줄은 자막의 끝을 나타냅니다.
            if subtitle:
                subtitles.append(subtitle)
                subtitle = None
        else:
            if subtitle is None:
                subtitle = {'index': int(line)}
                subtitle['text'] = []
            else:
                subtitle['text'].append(line)

    return subtitles

def extract_metadata(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"{video_path} 파일을 열 수 없습니다.")
        return

    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"파일명: {video_path}")
    print("프레임 레이트:", frame_rate)
    print("전체 프레임 수:", total_frames)
    print("해상도:", (frame_width, frame_height))

    print("-" * 30)

    cap.release()

    return frame_rate, total_frames, frame_width, frame_height

if __name__ == "__main__":
    folder_path = "./input"  # 폴더 경로 입력
    video_files = [f for f in os.listdir(folder_path) if f.endswith(".MP4")]
    srt_files = [f for f in os.listdir(folder_path) if f.endswith(".SRT")]

    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        frame_rate, total_frames, frame_width, frame_height = extract_metadata(video_path)

        # SRT 파일 읽어오기
        for srt_file in srt_files:
            with open(os.path.join(folder_path, srt_file), 'r', encoding='utf-8') as file:
                lines = file.readlines()

            subtitles = parsing_srt_file(lines)
            
            for subtitle in subtitles:
                if subtitle['index'] >= total_frames:
                    break
                
                print(f"Index: {subtitle['index']}")
                print(f"Start Time: {subtitle.get('start', 'N/A')}")
                print(f"End Time: {subtitle.get('end', 'N/A')}")
                print("Text:")
                for line in subtitle['text']:
                    print(line)
                print()