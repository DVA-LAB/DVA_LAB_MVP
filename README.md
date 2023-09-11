# DVA_LAB
Drone Video Analysis(DVA) project for helping MARC supported by Kakao Impact, MODULABS

## Files
```
ㄴinput
ㄴutils
  ㄴextract_meta.py
  ㄴvideo_segments.py
main.py
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

#### 3. main.py
Merge the other classes and pre, postprocessing
TODO: Divide classes into folders or other py files.
