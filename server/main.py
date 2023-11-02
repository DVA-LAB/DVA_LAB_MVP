from fastapi import FastAPI, UploadFile, File
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST"],  # 필요한 HTTP 메서드를 지정
    allow_headers=["*"],  # 필요한 헤더를 지정
)

class VideoPath(BaseModel):
    videoPath: str  # This should match the name of the field in the request data

@app.post("/run-test")
async def run_test(video_path: UploadFile = File(...)):
    try:
        # videoPath 필드에서 비디오 경로를 가져옴
        video_path = video_path.filename  # 클라이언트에서 전달한 파일의 이름을 가져옵니다.
        
        # test.py를 실행하고 원하는 작업을 수행합니다.
        # video_path를 test.py에 인자로 전달
        command = ["python", "test.py", video_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            # 테스트 실행이 성공하면 결과를 반환
            return {"message": "Test executed successfully", "result": result.stdout}
        else:
            # 테스트 실행 중 오류 발생 시 오류 메시지 반환
            return {"message": "Test execution failed", "error": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
