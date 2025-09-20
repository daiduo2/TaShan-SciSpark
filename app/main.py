import time
from app.api.urls import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)