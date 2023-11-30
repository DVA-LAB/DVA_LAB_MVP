from fastapi import FastAPI
import uvicorn
from api import routers
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Specifies the origins that are allowed, adjust as needed
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    
    app.include_router(routers.video_router.router)
    app.include_router(routers.model_router.router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, port=8000, host="0.0.0.0")
