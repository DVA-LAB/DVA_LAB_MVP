import cv2
import os
import threading

def parse_video_to_frames(video_path, output_base_folder_path):
    """
    Parses a single video into frames and saves them in a subdirectory named after the original file.
    Filenames are in the format 'originalfilename_framenumber.jpg', where the frame number is zero-padded to 5 digits.

    Args:
    video_path (str): The path to the video file.
    output_base_folder_path (str): The base path to the folder where the frames will be saved.

    Returns:
    None
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
        padded_frame_number = str(frame_count).zfill(5)
        frame_filename = f"{filename_without_ext}_{padded_frame_number}.jpg"
        cv2.imwrite(os.path.join(output_folder_path, frame_filename), frame)

        frame_count += 1

    cap.release()
    print(f"Completed parsing video: {filename_without_ext}")

def parse_videos_multithreaded(video_folder_path, output_base_folder_path):
    """
    Parses videos in the given folder into frames using multiple threads and saves them
    in a subdirectory named after each original file.

    Args:
    video_folder_path (str): The path to the folder containing the videos.
    output_base_folder_path (str): The base path to the folder where the frames will be saved.

    Returns:
    None
    """
    threads = []

    # Ensure base output folder exists
    if not os.path.exists(output_base_folder_path):
        os.makedirs(output_base_folder_path)

    # Create a thread for each video file
    for filename in os.listdir(video_folder_path):
        if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):  # Handles both lowercase and uppercase extensions
            video_path = os.path.join(video_folder_path, filename)
            thread = threading.Thread(target=parse_video_to_frames, args=(video_path, output_base_folder_path))
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All videos have been processed.")
