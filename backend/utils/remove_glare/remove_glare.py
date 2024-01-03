import tqdm
import cv2
import numpy as np
import argparse
from typing import Union
import torch

class RGLARE:
    """
        빛반사 제거를 목적으로 합니다. 
    """
    def __init__(self, video_path: str, save_path: str, queue_len: int, save:bool=True,
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
            self.video_save(save_path)

    def get_weight(self) -> np.ndarray:
        """
            빛반사에 적용할 프레임 별 가중치를 계산합니다.

            프레임 별 가중치는 첫 프레임을 가중치 1을 기준으로 프레임 개수만큼 0.1씩 감소시킵니다.
        
            첫 프레임이 가중치가 제일 높습니다.

            Return
                - weight (np.ndarray): 프레임 별 가중치가 담긴 배열
        """

        weight=[1]
        for _ in range(self.queue_len-1):
            weight.append(weight[-1]-0.1)
        return np.array(weight)[:,None,None,None]

    def get_gpu_weight(self) -> torch.Tensor:
        """
            GPU를 기반으로 빛반사에 적용할 프레임 별 가중치를 계산합니다.

            프레임 별 가중치는 첫 프레임을 가중치 1을 기준으로 프레임 개수만큼 0.1씩 감소시킵니다.
        
            첫 프레임이 가중치가 제일 높습니다.

            Return
                - weight (torch.Tensor): 프레임 별 가중치가 담긴 배열
        """

        weight=[1]
        for _ in range(self.queue_len-1):
            weight.append(weight[-1]-0.1)
        return torch.Tensor(weight)[:,None,None,None].to(self.device)

    def video_save(self, save_path) -> None:
        """
            비디오를 저장합니다.

            Args
                - save_path (str): 비디오가 저장될 경로
        """

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        # save_path = video_path.replace(video_path[-4:], '_result'+ video_path[-4:])
        self.out = cv2.VideoWriter(save_path, fourcc, fps, self.frame_size)

    def gamma_correction(self, frame:np.ndarray, alpha:float=0.8) -> np.ndarray:
        """
            프레임에서 영상의 밝기 변화를 주기 위해 입력으로 받은 프레임에 alpha 값을 적용해 감마 보정이 적용된 이미지를 반환합니다.
            
            Args
                - frame (np.ndarray): 감마 보정을 적용할 프레임
                - alpha (float): Alpha 값

            Return
                - gamma_corrected (np.ndarray): 감마 보정이 적용된 이미지
        """

        gamma_corrected = np.power(frame[:,:,2],alpha)
        return gamma_corrected

    def gamma_tensor_correction(self, frame, alpha:float=0.8):
        gamma_corrected = torch.pow(frame[:,:,2],alpha)
        return gamma_corrected

    def video_gpu(self):
        """
            GPU를 사용해 빛반사가 제거된 비디오를 생성합니다.
        """

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
        self.cap.release()
        self.out.release()

    def frame_gpu(self) -> Union[np.ndarray]:
        """ 
            GPU를 사용해 빛반사가 제거된 프레임을 생성합니다.
        
            Return
                output_frame (np.ndarray): 빛반사가 제거된 프레임
        """

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
        ''' CPU를 사용해 빛반사가 제거된 비디오를 생성합니다. '''
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

    def frame_cpu(self) -> Union[np.ndarray]:
        '''
            CPU를 사용해 빛반사가 제거된 프레임을 생성합니다.

            초기 함수 호출시 frame queue에 선언된 queue 길이만큼 이미지를 삽입 후, 
            
            전처리 진행한 다음 첫 frame부터 순차적으로 반환합니다. 
            
            영상 모두 반환했다면 None을 반환합니다.

            Return
                - out_frame (np.ndarray): 빛반사가 제거된 프레임
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