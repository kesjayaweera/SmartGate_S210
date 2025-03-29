from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from authlib.integrations.starlette_client import OAuth
from pathlib import Path

root_router = APIRouter()
pages = Jinja2Templates(directory=Path("frontend"))

oauth = OAuth()
oauth.register(
    name="github",
    client_id="Ov23liNZIYmArduFmbdg",
    client_secret="995eccf428c75201e949938f72ec6dba404151b5",
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    refresh_token_url=None,
    client_kwargs={"scope": "user:email"},
)

@root_router.get("/", response_class=HTMLResponse)
async def dashboard(request:Request):
    return pages.TemplateResponse("Index.html", {
        "request":request,
        "title":"Dashboard"
    })

@root_router.get("/login")
async def login(request:Request):
    redirect_uri = request.url_for("auth").replace("localhost", "127.0.0.1")
    return await oauth.github.authorize_redirect(request, redirect_uri)


