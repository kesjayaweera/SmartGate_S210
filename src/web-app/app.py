from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from controllers.main_controller import root_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="wwwroot"), name="static")

app.include_router(root_router)

if __name__ == "__main__":
    # Running the uvicorn as a webserver
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
