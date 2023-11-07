from autologging import logged
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from . import video_router  # noqa
