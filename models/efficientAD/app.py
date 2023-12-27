import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # GPU 0번만 사용하도록 설정

from fastapi import FastAPI
import uvicorn
from models.efficientAD.api import routers

def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(routers.inference_router.router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, port=8003, host="0.0.0.0")
