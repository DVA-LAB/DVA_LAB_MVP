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

## Contributors ✨

Thanks go to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
    <tbody>
        <tr>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/swhan0329"><img
                        src="https://avatars.githubusercontent.com/u/46466469?v=4?s=100" width="100px;"
                        alt="SeoWoo Han" /><br /><sub><b>SeoWoo Han</b></sub></a><br /><a
                    title="Maintenance">🚧</a>
                <a href="https://github.com/DVA-LAB/DVA_LAB/commits?author=swhan0329"
                    title="Code">💻</a><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=swhan0329"
                    title="Documentation">📖</a> <a
                    title="Reviewed Pull Requests">👀</a><a 
                    title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a>
            </td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/JunHyungKang"><img
                        src="https://avatars.githubusercontent.com/u/48425469?v=4?s=100" width="100px;"
                        alt="JunHyung Kang" /><br /><sub><b>JunHyung Kang</b></sub></a><br />
                <a href="https://github.com/DVA-LAB/DVA_LAB/commits?author=JunHyungKang"
                    title="Code">💻</a><a 
                    title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=JunHyungKang"
                    title="Documentation">📖</a><a
                    title="Reviewed Pull Requests">👀</a>
            </td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/roytravel"><img
                        src="https://avatars.githubusercontent.com/u/46618353?v=44?s=100" width="100px;"
                        alt="HanEol Lee" /><br /><sub><b>HanEol Lee</b></sub></a><br />
                <a href="https://github.com/DVA-LAB/DVA_LAB/commits?author=roytravel"
                    title="Code">💻</a> <a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=roytravel"
                    title="Documentation">📖</a> <a
                    title="Reviewed Pull Requests">👀</a>
            </td>
          <td align="center" valign="top" width="14.28%"><a href="https://github.com/jiyoung-e"><img
                        src="https://avatars.githubusercontent.com/u/68890429?v=4?s=100" width="100px;"
                        alt="JiYoung Lee" /><br /><sub><b>JiYoung Lee</b></sub></a><br /><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=jiyoung-e"
                    title="Code">💻</a><a 
                    title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=jiyoung-e"
                    title="Documentation">📖</a> <a
                    title="Reviewed Pull Requests">👀</a></td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/roche-MH"><img
                        src="https://avatars.githubusercontent.com/u/53164586?v=4?s=100" width="100px;"
                        alt="MyeongHoon Lim" /><br /><sub><b>MyeongHoon Lim</b></sub></a><br />
                <a href="https://github.com/DVA-LAB/DVA_LAB/commits?author=roche-MH"
                    title="Code">💻</a><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=roche-MH"
                    title="Documentation">📖</a>
                <a title="Reviewed Pull Requests">👀</a>
            </td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/woohyuun"><img
                        src="https://avatars.githubusercontent.com/u/98294094?v=4?s=100" width="100px;"
                        alt="WooHyun Jun" /><br /><sub><b>WooHyun Jun</b></sub></a><br /><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=woohyuun"
                    title="Code">💻</a> <a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=woohyuun"
                    title="Documentation">📖</a> <a
                    title="Reviewed Pull Requests">👀</a></td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/jognsu98"><img
                        src="https://avatars.githubusercontent.com/u/64674244?v=4?s=100" width="100px;"
                        alt="JongSu Choi" /><br /><sub><b>JongSu Choi</b></sub></a><br /><a href="https://github.com/DVA-LAB/DVA_LAB/commits?author=jognsu98"
                    title="Code">💻</a> <a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=jognsu98"
                    title="Documentation">📖</a> <a
                    title="Reviewed Pull Requests">👀</a></td>
        </tr>
        <tr>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/dwjustin"><img
                        src="https://avatars.githubusercontent.com/u/77228085?v=4?s=100" width="100px;"
                        alt="DongWoo Kim" /><br /><sub><b>DongWoo Kim</b></sub></a><br /><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=dwjustin"
                    title="Code">💻</a> <a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=dwjustin"
                    title="Documentation">📖</a> <a
                    title="Reviewed Pull Requests">👀</a></td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/lemonbuilder"><img
                        src="https://avatars.githubusercontent.com/u/103490406?v=4?s=100" width="100px;"
                        alt="HyeMin Park" /><br /><sub><b>HyeMin Park</b></sub></a><br /><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=lemonbuilder"
                    title="Code">💻</a><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=lemonbuilder"
                    title="Documentation">📖</a><a
                    title="Reviewed Pull Requests">👀</a></td>
                      <td align="center" valign="top" width="14.28%"><a href="https://github.com/dkccccc"><img
                        src="https://avatars.githubusercontent.com/u/143378988?v=4?s=100" width="100px;"
                        alt="Dongki Chung" /><br /><sub><b>Dongki Chung</b></sub></a><br /><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=dkccccc"
                    title="Code">💻</a> </td>
        </tr>
    </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://allcontributors.org) specification.
Contributions of any kind are welcome!
