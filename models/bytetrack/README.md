# ByteTrack
## Installation
### 1. Installing on the host machine
Step1. Install ByteTrack.
```shell
git clone https://github.com/ifzhang/ByteTrack.git
cd ByteTrack
pip3 install -r requirements.txt
python3 setup.py develop
```

Step2. Install [pycocotools](https://github.com/cocodataset/cocoapi).

```shell
pip3 install cython; pip3 install 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'
```

Step3. Others
```shell
pip3 install cython_bbox
```
### 2. Docker build
```shell
docker build -t bytetrack:latest .

# Startup sample
mkdir -p pretrained && \
mkdir -p YOLOX_outputs && \
xhost +local: && \
docker run --gpus all -it --rm \
-v $PWD/pretrained:/workspace/ByteTrack/pretrained \
-v $PWD/datasets:/workspace/ByteTrack/datasets \
-v $PWD/YOLOX_outputs:/workspace/ByteTrack/YOLOX_outputs \
-v /tmp/.X11-unix/:/tmp/.X11-unix:rw \
--device /dev/video0:/dev/video0:mwr \
--net=host \
-e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
-e DISPLAY=$DISPLAY \
--privileged \
bytetrack:latest
```