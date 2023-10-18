# [Remove  Glare](https://github.com/DVA-LAB/DVA_LAB/tree/master/utils/remove_glare#remove_glare)

빛 반사 제거를 위한 클래스

## [1. 예시 사용](https://github.com/DVA-LAB/DVA_LAB/tree/master/utils/remove_glare#remove_glare#1-예시-사용)

**Retrun Frame**


```python
#args.video : Video 파일 경로 			  Type : str
#args.ql 	: Queue의 길이 3~4가 적당함 	Type : int
#args.save 	: Video 저장 여부 			  Type : bool
#args.gamma : 감마 스트레칭 사용 여부 	  Type : bool

from remove_glare import RGLARE

main = RGLARE(args.video, args.ql, args.save, args.gamma)
# Video 종료시 retrun None
frame = main.f_run()
if frame is not None:
	cv2.imwrite('Remove.jpg', frame)
```

**Save Video**

```python
# output video result.mp4로 저장
python remove_glare.py --ql 4 --save True --video {video_path} --gamma True

or

from remove_glare import RGLARE

main = RGLARE(args.video, args.ql, args.save, args.gamma)
main.t_run()
```



## [2. 참고사항](https://github.com/DVA-LAB/DVA_LAB/tree/master/models/segment#2-참고사항)

- 다수의 이미지를 Queue에 넣어서 fusion된 값을 활용하기 때문에 단일 이미지 적용 불가능
- gamma_st는 감마 스트레칭으로 이미지를 밝게 해줌

