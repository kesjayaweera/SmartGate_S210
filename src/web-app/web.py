from fastapi import FastAPI
from controllers.main_controller import root_router

app = FastAPI()

app.include_router(root_router)

