from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from controllers.main_controller import root_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="wwwroot"), name="static")

app.include_router(root_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
