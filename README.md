# DVA_LAB
Drone Video Analysis(DVA) project for helping MARC supported by Kakao Impact, MODULABS

## 1. Repository Structure
```
DVA_LAB
│
├── backend
├── models
│ ├── BEV
│ ├── bytetrack
│ ├── efficientAD
│ ├── refiner
│ ├── sahi_detection
│ └── SAM
├── dataset
├── docs
├── frontend
└── README.md
```

## 2. backend
This directory contains the backend logic of the DVA system, including APIs and services for data and model operations.
### api/routers
- `data_router.py`: API routes for handling data-related requests.
- `model_router.py`: API routes for model-related operations.
### services
- `data_service.py`: Services for data manipulation and processing.
- `model_service.py`: Services for interacting with the analysis models.
### utils
- `remove_glare`: 빛반사 제거 (to be updated)
- `log_sync`: This module is for reading metadata and srt file from .MP4, .SRT. (to be updated)
- `visualizing`: This file is for visualizing the result of detection and tracking.
it shows a kind of dashboard at top-left side of frame. especially has the vessel violated?, distance between vessel and dolphin, speed of vessel and so on. (to be updated)

## 3. models
This directory contains different model directories, each operating as a microservice as part of a Microservices Architecture (MSA) to ensure modularity and avoid dependency conflicts. Each model serves a specific analysis purpose:
- `BEV`: Implements a microservice for Bird's Eye View transformations and analysis, providing a top-down perspective of video data.
- `bytetrack`: A microservice for tracking objects in video data, allowing for continuous object identification across frames.
- `efficientAD`: An efficient anomaly detection microservice model designed to identify unusual patterns or anomalies in video data.
- `refiner`: A microservice that refines detection or tracking results, improving the accuracy and reliability of the analysis.
- `sahi_detection`: A dedicated microservice for detection operations, capable of identifying a wide range of objects in various conditions.
- `SAM`: The Specific Application Model microservice for segmentation mask as util function.

Each microservice is self-contained, with its own dedicated environment and dependencies, ensuring that updates or changes to one service do not impact the others, in line with the principles of MSA.

## 4. dataset
The dataset directory is where the video and image datasets are stored for analysis.

## 5. my-react-app
A React application for interactive video analysis.

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
                        alt="MyeongHun Lim" /><br /><sub><b>MyeongHun Lim</b></sub></a><br />
                <a href="https://github.com/DVA-LAB/DVA_LAB/commits?author=roche-MH"
                    title="Code">💻</a><a
                    href="https://github.com/DVA-LAB/DVA_LAB/commits?author=roche-MH"
                    title="Documentation">📖</a>
                <a title="Reviewed Pull Requests">👀</a>
            </td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/woohyuun"><img
                        src="https://avatars.githubusercontent.com/u/98294094?v=4?s=100" width="100px;"
                        alt="WooHyun Jeon" /><br /><sub><b>WooHyun Jeon</b></sub></a><br /><a
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
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/SungHunYang"><img
                        src="https://avatars.githubusercontent.com/u/143378988?v=4?s=100" width="100px;"
                        alt="Sunghun Yang" /><br /><sub><b>Sunghun Yang</b></sub></a><br /><a
                  href="https://github.com/DVA-LAB/DVA_LAB/commits?author=SungHunYang"
                  title="Code">💻</a> </td>
            <td align="center" valign="top" width="14.28%"><a href="https://github.com/dkccccc"><img
                        src="https://avatars.githubusercontent.com/u/89681203?v=4?s=100" width="100px;"
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
