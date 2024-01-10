from fastapi import FastAPI
import uvicorn
from backend.api import routers
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """
        FastAPI를 실행하기 위한 app을 생성하고 미들웨어와 라우터를 설정한 다음 app을 반환합니다.

        Return
            - app (fastapi.FastAPI)
    """

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routers.data_router.router)
    app.include_router(routers.model_router.router)
    app.include_router(routers.result_router.router)
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, port=8000, host="0.0.0.0")
