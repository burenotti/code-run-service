from fastapi import FastAPI

from service.api import router

app = FastAPI()

app.include_router(router)
