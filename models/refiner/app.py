import uvicorn
from fastapi import FastAPI

from models.refiner.api import routers


def create_app() -> FastAPI:
    """
        FastAPI를 실행하기 위한 app을 생성하고 미들웨어와 라우터를 설정한 다음 app을 반환합니다.

        Return
            - app (fastapi.FastAPI)
    """
    app = FastAPI()
    app.include_router(routers.inference_router.router)
    return app


app = create_app()

if __name__ == "__main__":
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    uvicorn.run("app:app", reload=True, port=8005, host="0.0.0.0")
