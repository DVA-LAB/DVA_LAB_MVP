from autologging import logged
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from . import data_router, model_router , result_router # noqa
