from autologging import logged
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, BackgroundTasks, Response, status

from . import inference_router # noqa