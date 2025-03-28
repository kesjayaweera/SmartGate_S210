from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

root_router = APIRouter()
pages = Jinja2Templates(directory=Path("frontend"))

@root_router.get("/", response_class=HTMLResponse)
async def dashboard(request:Request):
    return pages.TemplateResponse("Index.html", {
        "request":request,
        "title":"Dashboard"
    })

