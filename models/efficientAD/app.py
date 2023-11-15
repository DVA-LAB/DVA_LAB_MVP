from fastapi import FastAPI
import uvicorn
from api import routers


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(routers.inference_router.router)
    return app


app = create_app()

if __name__ == "__main__":
    # uvicorn.run("app:app", reload=True, port=8009, host="0.0.0.0")
    uvicorn.run("app:app", reload=True, port=8009, host="10.250.109.105")
