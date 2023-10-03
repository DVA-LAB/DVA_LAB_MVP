# Dataset
선박 및 돌고래 데이터 셋

## 1. Huggingface competition dataset (based on DOTA)
* original link: https://huggingface.co/datasets/datadrivenscience/ship-detection
### Preprocessing
  * 객체가 이미지 전체 넓이 대비 0.5~1% 비율이 되도록 사이즈 조정 후 random crop 수행
  * random crop한 이미지에 이미지 전체 넓이 대비 0.05% 미만 사이즈의 선박 존재시 해당 이미지는 제외 
### sample image
![sample_1](dataset/sample_img/dota_1.png)
![sample_2](dataset/sample_img/dota_2.png)

### data 구성
```commandline

```



