from fastapi import APIRouter

root_router = APIRouter()

@root_router.get("/")
def read_root():
    return {"Hello":"World"}