# About

Shpinx를 이용해 파이썬 코드 내 docstring을 자동으로 문서화합니다.

## 1. Installation
* Documentation 생성을 위해 아래 절차 수행
* 추후 문서 생성을 위해 문서화 대상 파이썬 모듈 내 라이브러리 설치 필요

``` shell
cd DVA_LAb
conda create -n <name> python=3.7
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
pip install -r docs/requirements.txt
```
<br>

## 2. Configuration
* sphinx 모듈 설정은 `docs/conf.py`에서 수행
* 옵션은 shpinx [공식 문서](https://www.sphinx-doc.org/en/master/usage/configuration.html)에서 확인 가능 

```python
import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../backend'))
sys.path.insert(0, os.path.abspath('../models'))

extensions = ['recommonmark',
              'sphinx.ext.todo',
              'sphinx.ext.viewcode',
              'sphinx.ext.autodoc',
              'sphinx.ext.intersphinx']

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

master_doc = 'index'

templates_path = ['_templates']
exclude_patterns = ['_build', 
                    'Thumbs.db', 
                    '.DS_Store', 
                    'pull_request_template.md']

language = 'ko'

add_module_names = True

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
```
<br>

## 3. Build
``` bash
sphinx-apidoc -f -e -M -o docs . models/sahi_detection/* models/bytetrack/api/services/* models/BEV/api/services/Orthophoto_Maps/* models/refiner/api/services/FastSAM/*
make clean (optional)
make html
```

- shpinx-apidoc은 전체 모듈을 문서화하는 sphinx 소스 자동 생성 도구 ([공식문서 참조](https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html))
- `sphinx-apidoc -f -e -M -o docs .` 이후 값은 제외할 디렉터리 리스트
- 생성된 html 파일은 `docs/_build/html/` 경로에서 확인 가능