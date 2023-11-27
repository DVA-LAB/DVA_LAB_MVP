import uvicorn
from fastapi import FastAPI

from api import routers
from api.services.container import get_container


def create_app() -> FastAPI:
    container = get_container(wire_modules=[routers.inference_router])
    app = FastAPI()
    app.container = container
    app.include_router(routers.inference_router.router)
    return app


app = create_app()

if __name__ == "__main__":
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    uvicorn.run("app:app", reload=True, port=8010, host="0.0.0.0")
    # uvicorn.run("app:app", reload=True, port=8010, host="10.250.109.105")
