# OBSS SAHI Tool
# Code written by Fatih C Akyon, 2020.

import logging
from typing import Any, Dict, List, Optional
import importlib
import numpy as np

from sahi.models.base import DetectionModel
from sahi.prediction import ObjectPrediction

import torch

from yolox.utils.boxes import postprocess
from yolox.utils import fuse_model
from yolox.data.data_augment import ValTransform

logger = logging.getLogger(__name__)


class YoloxDetectionModel(DetectionModel):

    def check_dependencies(self) -> None:
        # check_requirements(["torch", "yolov5"])
        pass # 임시 주석 dependency 정보 없음

    def load_model(self):
        """
        Detection model is initialized and set to self.model.
        """
        current_exp = importlib.import_module(self.config_path)
        exp = current_exp.Exp()
        model = exp.get_model()
        model.cuda()
        model.eval()

        self.model = model
        ckpt = torch.load(self.model_path, map_location="cpu")
        self.model.load_state_dict(ckpt["model"])
        # model = yolov5.load(self.model_path, device=self.device)
        self.set_model(self.model)
        # logger.info("\tFusing model...")
        self.model = fuse_model(self.model)

    def set_model(self, model: Any):
        """
        Sets the underlying YOLOX model.
        Args:
            model: Any
                A YOLOX model
        """
        # set category_mapping
        if not self.category_mapping:
            category_mapping = {str(ind): category_name for ind, category_name in enumerate(self.category_names)}
            self.category_mapping = category_mapping

    def perform_inference(self, image: np.ndarray, image_size: int = None):
        """
        Prediction is performed using self.model and the prediction result is set to self._original_predictions.
        Args:
            image: np.ndarray
                A numpy array that contains the image to be predicted. 3 channel image should be in RGB order.
        """

        # Confirm model is loaded
        if self.model is None:
            raise ValueError("Model is not loaded, load it by calling .load_model()")
        # self._original_predictions = prediction_result
        preproc = ValTransform()
        if image_size is not None:
            tensor_img, _ = preproc(image, None, image_size)
        elif self.image_size is not None:
            tensor_img, _ = preproc(image, None, self.image_size)
        else:
            tensor_img, _ = preproc(image, None, (256,256))
        
        tensor_img = torch.from_numpy(tensor_img).unsqueeze(0)
        tensor_img = tensor_img.float()
        tensor_img = tensor_img.cuda()

        with torch.no_grad():
            prediction_result = self.model(tensor_img)
            print(prediction_result)
            prediction_result = postprocess(
                    prediction_result, len(self.classes), self.confidence_threshold,
                    self.nms_threshold, class_agnostic=True
                )
        
        if (prediction_result[0] is not None):
            prediction_result = prediction_result[0].cpu()
            bboxes = prediction_result[:,0:4]
            if image_size is not None:
                bboxes /= min(image_size[0] / image.shape[0], image_size[1] / image.shape[1])
            elif self.image_size is not None:
                bboxes /= min(self.image_size[0] / image.shape[0], self.image_size[1] / image.shape[1])
            else:
                bboxes /= min(256 / image.shape[0], 256 / image.shape[1])

            prediction_result[:,0:4] = bboxes

        self._original_predictions = prediction_result

    @property
    def num_categories(self):
        """
        Returns number of categories
        """
        return len(self.model.names)

    @property
    def has_mask(self):
        """
        Returns if model output contains segmentation mask
        """
        import yolov5
        from packaging import version

        if version.parse(yolov5.__version__) < version.parse("6.2.0"):
            return False
        else:
            return False  # fix when yolov5 supports segmentation models

    @property
    def category_names(self):
        # if check_package_minimum_version("yolov5", "6.2.0"):
        #     return list(self.model.names.values())
        # else:
        #     return self.model.names
        return self.classes

    # overrides fuc - parameter 
    def _create_object_prediction_list_from_original_predictions(
        self,
        image: np.ndarray,
        shift_amount_list: Optional[List[List[int]]] = [[0, 0]],
        full_shape_list: Optional[List[List[int]]] = None,
        image_size: int = None
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
        bboxes=[]
        bbclasses=[]
        scores=[]

        if isinstance(shift_amount_list[0], int):
            shift_amount_list = [shift_amount_list]
        if full_shape_list is not None and isinstance(full_shape_list[0], int):
            full_shape_list = [full_shape_list]
        
        if(original_predictions[0] is not None):
            bboxes = original_predictions[:,0:4]
            bbclasses = original_predictions[:, 6]
            scores = original_predictions[:, 4] * original_predictions[:, 5]        

        shift_amount = shift_amount_list[0]
        full_shape = None if full_shape_list is None else full_shape_list[0]

        object_prediction_list_per_image = []
        object_prediction_list = []

        for ind in range(len(bboxes)):
              box = bboxes[ind]
              cls_id = int(bbclasses[ind])
              score = scores[ind]
              if score < self.confidence_threshold:
                continue
              
              x0 = int(box[0])
              y0 = int(box[1])
              x1 = int(box[2])
              y1 = int(box[3])

              bbox = [x0,y0,x1,y1]

              object_prediction = ObjectPrediction(
                bbox = bbox,
                category_id=cls_id,
                bool_mask=None,
                category_name=self.category_mapping[str(cls_id)],
                shift_amount=shift_amount,
                score=score,
                full_shape=full_shape,
            )
              object_prediction_list.append(object_prediction)
        
        object_prediction_list_per_image = [object_prediction_list]
        self._object_prediction_list_per_image = object_prediction_list_per_image