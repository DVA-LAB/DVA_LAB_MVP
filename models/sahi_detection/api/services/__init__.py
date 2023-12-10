import sys
import os
# 현재 init 파일이 위치한 디렉토리 경로를 가져와서 sys.path에 추가
package_root = os.path.dirname(os.path.abspath(__file__))

# 패키지의 루트 경로를 sys.path에 추가합니다.
sys.path.append(package_root)
from yolox.data.data_augment import preproc
from yolox.exp import get_exp
from yolox.utils import fuse_model, get_model_info, postprocess
from yolox.utils.visualize import plot_tracking
from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracking_utils.timer import Timer

from .sahi.models.yolox import YoloxDetectionModel
from .sahi.predict import get_sliced_prediction
from .sahi import AutoDetectionModel

from .utils import config

# sys.path에서 패키지 루트 경로를 제거
sys.path.remove(package_root)