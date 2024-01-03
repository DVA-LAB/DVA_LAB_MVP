import cv2
import numpy as np
from skimage.exposure import match_histograms

class Preprocessing:
    """ 이미지 전처리를 목적으로 하는 클래스입니다. """

    def __init__(self):
        pass

    def clahe(self, frame):
        """
            프레임에 대비를 향상시키기 위해 CLAHE 전처리를 적용한 프레임을 반환합니다.

            Args
                - frame (np.ndarray): CLAHE 전처리를 적용할 프레임
            
            Return
                - image_clahe (np.ndarray): CLAHE 전처리가 적용된 프레임
        """

        #Converting the image to YCrCb
        image_space = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        #Creating CLAHE
        clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(8,8))
        #Applying Histogram Equalization on the original image of the Y channel
        image_space[:,:,0] = clahe.apply(image_space[:,:,0])
        #convert the YUV image to RGB format
        image_clahe = cv2.cvtColor(image_space, cv2.COLOR_YUV2BGR)

        return image_clahe

    def stretching(self, frame):
        """
            프레임의 명암 분포를 넓게하는 스트레칭을 적용합니다.

            Args
                - frame (np.ndarray): 명암 분포를 넓게 만들 원본 프레임
        
            Return
                - image_st (np.ndarray): 프레임의 명암이 넓게 분포한 이미지
        """

        # Converting the image to YCrCb
        image_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        # Loop over the Y channel and apply Min-Max Contrasting
        min = np.min(image_yuv[:,:,0])
        max = np.max(image_yuv[:,:,0])

        for i in range(frame.shape[0]):
            for j in range(frame.shape[1]):
                image_yuv[:,:,0][i,j] = 255*(image_yuv[:,:,0][i,j]-min) / (max-min)
        # convert the YUV image back to RGB format
        image_st = cv2.cvtColor(image_yuv,cv2.COLOR_YUV2BGR)
        return image_st

    def histogram_matched(self, frame, ref):
        """
            누적 히스토그램이 다른 이미지의 누적 히스토그램과 일치하도록 프레임을 조절합니다.

            Args
                - frame (np.ndarray): 히스토그램 매칭을 수행할 소스 프레임
                - ref   (np.ndarray): 히스토그램 매칭을 수행할 타겟 프레임

            Return
                - ?
        """

        return match_histograms(frame, ref, channel_axis=-1)


