import cv2
import numpy as np
from skimage.exposure import match_histograms

class Preprocessing:
    def __init__(self):
        pass

    def clahe(self,frame):
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

    def histogram_matched(self, frame,ref):
        return match_histograms(frame, ref, channel_axis=-1)


