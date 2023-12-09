# ByteTrack
## Installation

Step1. Create conda environment
```shell
conda create -n bytetrack python=3.7
```

Step2. Install pytorch and library
``` python
pip install torch==1.13.1+cu117 torchvision==0.14.1+cu117 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu117
pip install -r requirements.txt
```

Step3. Install [pycocotools](https://github.com/cocodataset/cocoapi).

```shell
pip3 install cython; pip3 install 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'
```

Step4. Others
```shell
pip3 install cython_bbox
```

If above doesn't work, you can run following command instead of Step 2.
```shell
git clone https://github.com/ifzhang/ByteTrack.git
cd ByteTrack
pip3 install -r requirements.txt
python3 setup.py develop
```