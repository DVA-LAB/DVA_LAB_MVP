import tqdm
import cv2
import numpy as np
import argparse
from typing import Union
import torch

class RGLARE:
    def __init__(self, video_path: str, queue_len: int, save:bool=True,
                 gamma:bool=False):
        self.cap = cv2.VideoCapture(video_path)
        self.out = None
        self.frame_size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                          int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        self.total_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.queue_len = queue_len
        self.frame_queue = []
        self.queue_full = False
        self.frame_count = 0
        self.frame_queue_done = 0
        self.gamma = gamma
        self.device = ('cuda:0' if torch.cuda.is_available() else 'cpu')
        if self.device == 'cuda:0':
            self.weight = self.get_gpu_weight()
        else:
            self.weight = self.get_weight()
        if save:
            self.video_save(video_path)

    def get_weight(self) -> np.ndarray:
        '''
        frame weight 생성하는 함수이며,
        1을 기준으로 frame개수 만큼 -0.1해서 첫 프레임이 가중치가 제일 높음
        '''
        weight=[1]
        for _ in range(self.queue_len-1):
            weight.append(weight[-1]-0.1)
        return np.array(weight)[:,None,None,None]

    def get_gpu_weight(self) -> torch.Tensor:
        weight=[1]
        for _ in range(self.queue_len-1):
            weight.append(weight[-1]-0.1)
        return torch.Tensor(weight)[:,None,None,None].to(self.device)

    def video_save(self, video_path) -> None:
        '''
        Video 저장을 위한 함수이며,
        Input으로 받은 Video의 코덱의 정수표현, FPS,사이즈들을 가지고 Writer 정의
        저장 경로는 result.mp4로 static
        '''
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        save_path = video_path.replace(video_path[-4:], '_result'+ video_path[-4:])
        self.out = cv2.VideoWriter(save_path, fourcc, fps, self.frame_size)

    def gamma_correction(self, frame:np.ndarray, alpha:float=0.8) -> np.ndarray:
        '''
        frame 영상의 밝기 변화를 위한 함수이며,
        인풋으로 받은 frame에 대해서 alpha 값을 통해 감마 보정됨
        보정된 이미지 return
        '''
        gamma_corrected = np.power(frame[:,:,2],alpha)
        return gamma_corrected

    def gamma_tensor_correction(self, frame, alpha:float=0.8):
        gamma_corrected = torch.pow(frame[:,:,2],alpha)
        return gamma_corrected

    def video_gpu(self):
        with tqdm.tqdm(total=self.total_frame, desc="GPU Remove Light") as pbar:
            while self.frame_count < self.total_frame+self.queue_len:
                ret, frame = self.cap.read()

                if not ret:
                    self.frame_queue_done+=1
                    hsv_frame=None
                    if self.frame_queue_done == self.queue_len:
                        break
                else:
                    frame = cv2.resize(frame, (1920,1920))
                    frame = cv2.medianBlur(frame,3)
                    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                if self.queue_full:
                    if hsv_frame is None:
                        fused_frame, _ = torch.min(
                            torch.stack(self.frame_queue, dim=0) *
                            self.weight[:len(self.frame_queue),:,:,:],
                            dim=0
                        )
                    else:
                        tensor_frame = torch.tensor(hsv_frame/255.0).permute(2, 0, 1).to(self.device)
                        self.frame_queue.append(tensor_frame)
                        fused_frame, _ = torch.min(
                            torch.stack(self.frame_queue, dim=0),
                            dim=0
                        )
                    out_frame = self.frame_queue.pop(0)

                    if self.gamma is True:
                        out_frame[:,:,2] = self.gamma_tensor_correction(fused_frame)
                    else:
                        out_frame[:,:,2] = fused_frame[:,:,2]

                    out_frame = torch.clamp(out_frame * 255.0, 0, 255).type(torch.uint8)
                else:
                    tensor_frame = torch.tensor(hsv_frame/255.0).permute(2,0,1).to(self.device)
                    self.frame_queue.append(tensor_frame)
                    if len(self.frame_queue) == self.queue_len - 1:
                        self.queue_full = True
                    continue

                out_frame = out_frame.clone().detach().permute(1,2,0).cpu().numpy().astype(np.uint8)
                out_frame = cv2.cvtColor(out_frame, cv2.COLOR_HSV2BGR)
                out_frame = cv2.resize(out_frame, self.frame_size)
                self.out.write(out_frame)
                pbar.update()
                self.frame_count+=1

    def frame_gpu(self) -> Union[np.ndarray]:
        if self.queue_full:
            ret, frame = self.cap.read()
            if ret is None:
                if len(self.frame_queue) == 0:
                    return None
                fused_frame, _ = torch.min(
                    torch.stack(self.frame_queue) * self.weight[:len(self.frame_queue),:,:,:],
                    axis=0)
            else:
                frame = cv2.resize(frame,(1920,1920))
                frame = cv2.medianBlur(frame,3)
                hsv_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
                tensor_frame = torch.tensor(hsv_frame / 255.0).permute(2, 0, 1).to(self.device)
                self.frame_queue.append(tensor_frame)
                fused_frame, _ = torch.min(
                    torch.stack(self.frame_queue) * self.weight,
                    axis=0)
            out_frame = self.frame_queue.pop(0)

            if self.gamma is True:
                out_frame[:,:,2] = self.gamma_tensor_correction(fused_frame)
            else:
                out_frame[:,:,2] = fused_frame[:,:,2]

            out_frame = torch.clamp(out_frame * 255.0, 0, 255)

            output_frame = out_frame.clone().detach().permute(1, 2, 0).cpu().numpy().astype(np.uint8)
            output_frame = cv2.cvtColor(output_frame.astype('uint8'), cv2.COLOR_HSV2BGR)
            output_frame = cv2.resize(output_frame, self.frame_size)
            return output_frame
        else:
            while len(self.frame_queue) != self.queue_len-1:
                ret, frame = self.cap.read()
                hsv_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
                tensor_frame = torch.tensor(hsv_frame / 255.0).permute(2, 0, 1).to(self.device)
                self.frame_queue.append(tensor_frame)
            self.queue_full=True
            return self.frame_gpu()

    def video_cpu(self):
        '''
        영상 전체를 반복하며 전처리된 Video를 저장하는 함수
        '''
        with tqdm.tqdm(total=self.total_frame, desc="Remove Light") as pbar:
            while self.frame_count < self.total_frame+self.queue_len:
                ret, frame = self.cap.read()
                if not ret:
                    self.frame_queue_done+=1
                    hsv_frame=None
                    if self.frame_queue_done == self.queue_len:
                        break
                else:
                    frame = cv2.medianBlur(frame,3)
                    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                if self.queue_full:
                    if hsv_frame is None:
                        fused_frame = np.min(
                            np.stack(self.frame_queue,axis=0) * self.weight[:len(self.frame_queue),:,:,:],
                            axis=0)
                    else:
                        self.frame_queue.append(hsv_frame/255.0)
                        fused_frame = np.min(
                            np.stack(self.frame_queue, axis=0) * self.weight,
                            axis=0)
                    out_frame = self.frame_queue.pop(0)
                    if self.gamma is True:
                        out_frame[:,:,2] = self.gamma_correction(fused_frame)
                    else:
                        out_frame[:,:,2] = fused_frame[:,:,2]
                    out_frame = np.clip(out_frame * 255.0, 0, 255)
                    out_frame = cv2.cvtColor(out_frame.astype('uint8'), cv2.COLOR_HSV2BGR)
                else:
                    self.frame_queue.append(hsv_frame/255.0)
                    if len(self.frame_queue) == self.queue_len-1:
                        self.queue_full=True
                    continue
                self.out.write(out_frame)
                pbar.update()
        self.cap.release()
        self.out.release()

    def frame_cpu(self) ->Union[np.ndarray]:
        '''
        초기 함수 호출시 Frame queue에 선언된 Queue len만큼 이미지를 삽입하고,
        전처리 진행 후 첫 Frame부터 순차적으로 반환
        영상 모두 반환했다면 None값 반환
        '''
        if self.queue_full:
            ret, frame = self.cap.read()
            if ret is None:
                if len(self.frame_queue) == 0:
                    return None
                fused_frame = np.min(
                    np.stack(self.frame_queue) * self.weight[:len(self.frame_queue),:,:,:],
                    axis=0)
            else:
                frame = cv2.medianBlur(frame,3)
                hsv_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
                self.frame_queue.append(hsv_frame/255.0)
                fused_frame = np.min(
                    np.stack(self.frame_queue) * self.weight,
                    axis=0)
            out_frame = self.frame_queue.pop(0)

            if self.gamma is True:
                out_frame[:,:,2] = self.gamma_correction(fused_frame)
            else:
                out_frame[:,:,2] = fused_frame[:,:,2]

            out_frame = np.clip(out_frame * 255.0, 0, 255)
            out_frame = cv2.cvtColor(out_frame.astype('uint8'), cv2.COLOR_HSV2BGR)
            return out_frame
        else:
            while len(self.frame_queue) != self.queue_len-1:
                ret, frame = self.cap.read()
                hsv_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
                self.frame_queue.append(hsv_frame/255.0)
            self.queue_full=True
            return self.f_run()
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='--ql : queue length ex) 4 '
                                                 '--save : save video ex) True'
                                                 '--video : video path '
                                                 '--gamma : gamma stretching ex) True')
    parser.add_argument('--ql',default=4, type=int, required=True)
    parser.add_argument('--save',default=True, type=bool, required=True)
    parser.add_argument('--video', default=None, type=str, required=True)
    parser.add_argument('--gamma', default=False, type=bool, required=True)
    args = parser.parse_args()
    main = RGLARE(args.video, args.ql, args.save, args.gamma)
    main.video_gpu()
