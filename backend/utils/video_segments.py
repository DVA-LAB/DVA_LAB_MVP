from datetime import timedelta
import os
import cv2
# from utils.extract_meta import parsing_srt_file

class VideoSegment:
    def __init__(self, index, start_time, end_time, text, frame):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.frame = frame


def parse_srt_time(time_str):
    """
        SRT 파일의 시간 문자열로부터 초 기준 시간 정보를 반환합니다.

        Args
            - time_str (str): 시간 문자열

        Return
            - 전체 초 (datetime.timedelta)
    """

    time_str = time_str.replace(",", ".")
    time_parts = time_str.split(':')
    hours, minutes, seconds = map(float, time_parts)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return timedelta(seconds=total_seconds)


def make_video_segment(video_filename, srt_filename):
    """
        SRT 파일을 파싱하여 VideoSegment 목록을 생성합니다.

        Args
            - video_filename (str): 비디오 파일이름
            - srt_filename (str): srt 파일이름

        Returns
            - video_segments (list): VideoSegment 객체 목록
    """

    cap = cv2.VideoCapture(video_filename)
    subtitles = parsing_srt_file(srt_filename)

    video_segments = []
    i = 0
    for subtitle in subtitles:
        i += 1
        if i > 10:
            break
        start_time = parse_srt_time(subtitle['start'])
        end_time = parse_srt_time(subtitle['end'])
        text = subtitle['text']

        # 프레임 번호 설정
        cap.set(cv2.CAP_PROP_POS_FRAMES, subtitle['index'])

        # 프레임 읽기
        _, frame = cap.read()

        # VideoSegment 인스턴스 생성
        segment = VideoSegment(len(video_segments) + 1, start_time, end_time, text, frame)
        video_segments.append(segment)

    return video_segments

if __name__ == "__main__":
    folder_path = "../input"  # 폴더 경로 입력
    video_files = [f for f in os.listdir(folder_path) if f.endswith(".MP4")]
    srt_files = [f for f in os.listdir(folder_path) if f.endswith(".SRT")]

    # VideoSegment 목록 생성
    all_segments = []
    
    for video_file, srt_file in zip(video_files, srt_files):
        video_path = os.path.join(folder_path, video_file)
        srt_path = os.path.join(folder_path, srt_file)
        segment = make_video_segment(video_path, srt_path)

        print(f"Index: {segment.index}")
        print(f"Start Time: {segment.start_time}")
        print(f"End Time: {segment.end_time}")
        print(f"Text:\n{segment.text}")
