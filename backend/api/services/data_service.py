import os
import cv2
import threading


def parse_video_to_frames(video_path, output_base_folder_path, frame_interval=1):
    """
        비디오 파일을 파싱하여 프레임으로 추출합니다. 
        
        파일명 형식은 '원본파일명_프레임번호.jpg'이며 프레임번호는 제로 패딩된 5자리 숫자 입니다.

        Args
            - video_path (str): 프레임을 파싱할 비디오 파일 경로
            - output_base_folder_path (str): 파싱된 프레임이 저장될 경로
    """

    filename_without_ext = os.path.splitext(os.path.basename(video_path))[0]
    output_folder_path = output_base_folder_path

    # Create a subdirectory for the current video if it doesn't exist
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error opening video file: {filename_without_ext}")
        return

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save frame with padded frame number
        if frame_count % frame_interval == 0:
            padded_frame_number = str(frame_count).zfill(5)
            frame_filename = f"{filename_without_ext}_{padded_frame_number}.jpg"
            cv2.imwrite(os.path.join(output_folder_path, frame_filename), frame)

        frame_count += 1

    cap.release()
    print(f"Completed parsing video: {filename_without_ext}")


def parse_videos_multithreaded(video_folder_path, output_base_folder_path):
    """
        멀티쓰레드를 활용하여 비디오 파일을 프레임으로 추출합니다.

        Args
            - video_folder_path (str): 프레임을 파싱할 비디오 파일 경로
            - output_base_folder_path (str): 파싱된 프레임이 저장될 경로
    """

    threads = []

    # Ensure base output folder exists
    if not os.path.exists(output_base_folder_path):
        os.makedirs(output_base_folder_path)

    # Create a thread for each video file
    for filename in os.listdir(video_folder_path):
        if filename.lower().endswith(
            (".mp4", ".avi", ".mov", ".mkv")
        ):  # Handles both lowercase and uppercase extensions
            video_path = os.path.join(video_folder_path, filename)
            thread = threading.Thread(
                target=parse_video_to_frames, args=(video_path, output_base_folder_path)
            )
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All videos have been processed.")
