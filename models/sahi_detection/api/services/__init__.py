from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import fuse_model, get_model_info, postprocess
from yolox.utils.visualize import plot_tracking
from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracking_utils.timer import Timer

from sahi.models.yolox import YoloxDetectionModel
from sahi.predict import get_sliced_prediction
from sahi import AutoDetectionModel

from .utils import config