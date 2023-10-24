import cv2
import ffmpeg
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from utils.remove_glare.remove_glare import RGLARE


class TempRGLARE(RGLARE):
    def f_run(self):
        ret, frame = self.cap.read()
        if len(self.frame_queue) == self.queue_len - 1:
            if ret is None:
                if len(self.frame_queue) == 0:
                    return None
                fused_frame = np.min(
                    np.stack(self.frame_queue)
                    * self.weight[: len(self.frame_queue), :, :, :],
                    axis=0,
                )
            else:
                frame = cv2.medianBlur(frame, 3)
                hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                self.frame_queue.append(hsv_frame / 255.0)
                fused_frame = np.min(np.stack(self.frame_queue) * self.weight, axis=0)
            out_frame = self.frame_queue.popleft()

            if self.gamma is True:
                out_frame[:, :, 2] = self.gamma_correction(fused_frame)
            else:
                out_frame[:, :, 2] = fused_frame[:, :, 2]

            out_frame = np.clip(out_frame * 255.0, 0, 255)
            out_frame = cv2.cvtColor(out_frame.astype("uint8"), cv2.COLOR_HSV2BGR)
            return out_frame
        else:
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            self.frame_queue.append(hsv_frame / 255.0)
            return frame


class VideoDataset(Dataset):
    def __init__(self, video_path, transform=None):
        self.video_path = video_path
        self.pre_processor = TempRGLARE(video_path, queue_len=4, save=False, gamma=True)
        self.transform = transform

    def __len__(self):
        return self.pre_processor.total_frame

    def __getitem__(self, idx):
        if self.transform:
            return self.transform(self.pre_processor.f_run())
        else:
            return self.pre_processor.f_run()
