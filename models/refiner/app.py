import uvicorn
from fastapi import FastAPI

from api import routers


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(routers.inference_router.router)
    return app


app = create_app()

if __name__ == "__main__":
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    uvicorn.run("app:app", reload=True, port=8005, host="0.0.0.0")
