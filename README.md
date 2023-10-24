# DVA_LAB
Drone Video Analysis(DVA) project for helping MARC supported by Kakao Impact, MODULABS

## Files
```
ㄴinput
ㄴutils
  ㄴseg_frame_parsing.py
  ㄴtracking_frame_parsing.py
  ㄴextract_meta.py
  ㄴvideo_segments.py
main.py
data.py
README.md
```
### 1. input
This folder is for reading videos or images.

### 2. utils
This folder is for handling many things such as reading metadata, making video segments etc.

#### 2-1. extract_meta.py
This file is for reading metadata and srt file from .MP4, .SRT.
Input .MP4 and .SRT file should be located in "./input".

```python extract_meta.py```

#### 2-2. video_segments.py
This file is for making video segments struct including frame and metadata.
Input .MP4 and .SRT file should be located in "./input".

```python video_segments.py```

#### 2-3. transform_coordinate.py
This file is for getting 3D world coordinate from 2D image coordinate.


### 3. main.py
Merge the other classes and pre, postprocessing
TODO: Divide classes into folders or other py files.

### 4. data.py
`VideoDataset` 클래스는 PyTorch의 `Dataset` 클래스를 상속받아 비디오 데이터를 로드하고 빛반사 전처리 후 frame단위로 인덱싱합니다.
```python
# dataloader 사용법
from torch.utils.data import DataLoader

dataset = VideoDataset('input/test.MOV')
frame_loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
```


### 5. visualize.py
This file is for visualizing the result of detection and tracking.
it shows a kind of dashboard at top-left side of frame. especially has the vessel violated?, distance between vessel and dolphin, speed of vessel and so on.