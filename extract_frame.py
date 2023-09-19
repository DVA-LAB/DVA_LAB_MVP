import os
import cv2

def video_to_frame(video_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    count = 0
    cap = cv2.VideoCapture(video_path)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        count += 1
        output_path = os.path.join(output_dir, str(count).zfill(6)+'.jpg')
        cv2.imwrite(output_path, frame)
        print(count, end='\r')


if __name__ == "__main__":
    video_path = 'data/DJI_0009.MP4'
    output_dir = 'data/output'
    video_to_frame(video_path, output_dir)