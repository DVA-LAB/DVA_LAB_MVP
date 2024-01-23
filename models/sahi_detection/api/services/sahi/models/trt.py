import logging
from typing import Any, List, Optional

import numpy as np

from sahi.models.base import DetectionModel
from sahi.prediction import ObjectPrediction
from sahi.utils.compatibility import fix_full_shape_list, fix_shift_amount_list

logger = logging.getLogger(__name__)

import tensorrt as trt
#import pycuda.autoinit
import pycuda.driver as cuda
import cv2


class TensorRTDetectionModel(DetectionModel):
    def load_model(self):
        """
        Detection model is initialized and set to self.model.
        """

        try:
            with open(self.model_path, "rb") as f:
                serialized_engine = f.read()

            self.set_model(serialized_engine)
        except Exception as e:
            raise TypeError("model_path is not a valid TensorRT model path: ", e)

    def set_model(self, serialized_engine: Any):
        """
        Sets the underlying TensorRT model.
        Args:
            model: Any
                A TensorRT model
        """
        logger = trt.Logger(trt.Logger.WARNING)
        logger.min_severity = trt.Logger.Severity.ERROR
        runtime = trt.Runtime(logger)
        trt.init_libnvinfer_plugins(logger,'')
        engine = runtime.deserialize_cuda_engine(serialized_engine)
        self.imgsz = engine.get_binding_shape(0)[2:]
        self.context = engine.create_execution_context()
        self.inputs, self.outputs, self.bindings = [], [], []
        self.stream = cuda.Stream()
        for binding in engine:
            self._size = trt.volume(engine.get_binding_shape(binding))
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            host_mem = cuda.pagelocked_empty(self._size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            self.bindings.append(int(device_mem))
            if engine.binding_is_input(binding):
                self.inputs.append({'host': host_mem, 'device': device_mem})
            else:
                self.outputs.append({'host': host_mem, 'device': device_mem})


    def _preproc(self,image, input_size, mean, std, swap=(2, 0, 1)):
        if len(image.shape) == 3:
            padded_img = np.ones((self.imgsz[0], self.imgsz[1], 3)) * 114.0
        else:
            padded_img = np.ones(input_size) * 114.0

        img = np.array(image)
        r = min(input_size[0] / img.shape[0], input_size[1] / img.shape[1])
        resized_img = cv2.resize(
            img,
            (int(img.shape[1] * r), int(img.shape[0] * r)),
            interpolation=cv2.INTER_LINEAR,
        ).astype(np.float32)
        padded_img[: int(img.shape[0] * r),: int(img.shape[1] * r)] = resized_img
        padded_img = resized_img
        padded_img = padded_img[:, :, ::-1]
        padded_img /= 255.0
        if mean is not None:
            padded_img -= mean
        if std is not None:
            padded_img /= std
        padded_img = padded_img.transpose(swap)
        padded_img = np.ascontiguousarray(padded_img, dtype=np.float32)
        return padded_img, r

    def perform_inference(self, image: np.ndarray):
        """
        Prediction is performed using self.model and the prediction result is set to self._original_predictions.
        Args:
            image: np.ndarray
                A numpy array that contains the image to be predicted. 3 channel image should be in RGB order.
        """
        image , self._ratio = self._preproc(image, self.slice_size, None, None)
        self.inputs[0]['host'] = np.ravel(image)
        for inp in self.inputs:
            cuda.memcpy_htod_async(inp['device'], inp['host'], self.stream)
        self.context.execute_async_v2(
            bindings=self.bindings,
            stream_handle=self.stream.handle
        )
        for out in self.outputs:
            cuda.memcpy_dtoh_async(out['host'], out['device'], self.stream)
        self.stream.synchronize()

        self._original_predictions = [out['host'] for out in self.outputs]

    @property
    def num_categories(self):
        """
        Returns number of categories
        """
        return len(self.category_mapping)

    def _nms(self, boxes, scores, nms_thr):
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)

            inds = np.where(ovr <= nms_thr)[0]
            order = order[inds +1]
        return keep


    def _multiclass_nms(self, boxes, scores, nms_thr, score_thr):
        final_dets = []
        num_classes = scores.shape[1]
        for cls_ind in range(num_classes):
            cls_scores = scores[:, cls_ind]
            valid_score_mask = cls_scores > score_thr
            if valid_score_mask.sum() == 0:
                continue
            else:
                valid_scores = cls_scores[valid_score_mask]
                valid_boxes = boxes[valid_score_mask]
                keep = self._nms(valid_boxes, valid_scores, nms_thr)
                if len(keep) > 0:
                    cls_inds = np.ones((len(keep), 1)) * cls_ind
                    dets = np.concatenate(
                        [valid_boxes[keep], valid_scores[keep, None], cls_inds], 1
                    )
                    final_dets.append(dets)
        if len(final_dets) == 0:
            return None
        return np.concatenate(final_dets, 0)

    def postprocess(self,predictions, ratio):
        boxes = predictions[:, :4]
        scores = predictions[:, 4:5] * predictions[:, 5:]
        boxes_xyxy = np.ones_like(boxes)
        boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.
        boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.
        boxes_xyxy[:, 2] = boxes[:, 0] - boxes[:, 2] / 2.
        boxes_xyxy[:, 3] = boxes[:, 1] - boxes[:, 3] / 2.
        boxes_xyxy /= ratio
        dets = self._multiclass_nms(boxes_xyxy, scores, nms_thr=0.45, score_thr=0.1)
        return dets

    def _create_object_prediction_list_from_original_predictions(
        self,
        shift_amount_list: Optional[List[List[int]]] = [[0, 0]],
        full_shape_list: Optional[List[List[int]]] = None,
    ):
        """
        self._original_predictions is converted to a list of prediction.ObjectPrediction and set to
        self._object_prediction_list_per_image.
        Args:
            shift_amount_list: list of list
                To shift the box and mask predictions from sliced image to full sized image, should
                be in the form of List[[shift_x, shift_y],[shift_x, shift_y],...]
            full_shape_list: list of list
                Size of the full image after shifting, should be in the form of
                List[[height, width],[height, width],...]
        """
        original_predictions = self._original_predictions
        ratio = self._ratio
        dets = []

        shift_amount_list = fix_shift_amount_list(shift_amount_list)
        full_shape_list = fix_full_shape_list(full_shape_list)

        # handle all predictions
        object_prediction_list_per_image = []
        num, final_boxes, final_scores, final_cls_inds = original_predictions
        final_boxes = np.reshape(final_boxes / ratio, (-1, 4))
        dets.append(np.concatenate([final_boxes[:num[0]], np.array(final_scores)[:num[0]].reshape(-1, 1), np.array(final_cls_inds)[:num[0]].reshape(-1, 1)], axis=-1))

        for image_ind, value in enumerate(dets):
            shift_amount = shift_amount_list[image_ind]
            full_shape = None if full_shape_list is None else full_shape_list[image_ind]
            object_prediction_list = []

            for prediction in value:
                x1 = prediction[0]
                y1 = prediction[1]
                x2 = prediction[2]
                y2 = prediction[3]
                bbox = [x1, y1, x2, y2]
                score = prediction[4]
                category_id = int(prediction[5])
                category_name = self.category_mapping[category_id]

                # fix negative box coords
                bbox[0] = max(0, bbox[0])
                bbox[1] = max(0, bbox[1])
                bbox[2] = max(0, bbox[2])
                bbox[3] = max(0, bbox[3])

                if full_shape is not None:
                    bbox[0] = min(full_shape[1], bbox[0])
                    bbox[1] = min(full_shape[0], bbox[1])
                    bbox[2] = min(full_shape[1], bbox[2])
                    bbox[3] = min(full_shape[0], bbox[3])

                object_prediction = ObjectPrediction(
                    bbox=bbox,
                    category_id=category_id,
                    score=score,
                    bool_mask=None,
                    category_name=category_name,
                    shift_amount=shift_amount,
                    full_shape=full_shape,
                )
                object_prediction_list.append(object_prediction)
            object_prediction_list_per_image.append(object_prediction_list)

        self._object_prediction_list_per_image = object_prediction_list_per_image
