from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
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
async def dashboard(request: Request):
    # Access user data from request.state if logged in
    user = getattr(request.state, 'user', None)

    return pages.TemplateResponse("Index.html", {
        "request": request,
        "title": "Dashboard",
        "user": user  # Pass the user data to the template
    })

@root_router.get("/login")
async def login(request:Request):
    redirect_uri = request.url_for("auth")
    return await oauth.github.authorize_redirect(request, redirect_uri)

@root_router.get("/auth")
async def auth(request: Request):
    token = await oauth.github.authorize_access_token(request)
    user = await oauth.github.parse_id_token(request, token)
    
    # Store the user information in the request state for later use
    request.state.user = {
        "username": user["login"],  # GitHub's username
        "avatar_url": user["avatar_url"]  # GitHub's avatar URL
    }

    # Redirect to dashboard after successful login
    return RedirectResponse(url="/")

@root_router.get("/logout")
async def logout(request: Request):
    # Remove user info from the request state to log the user out
    request.state.user = None

    # Redirect to the homepage or login page
    return RedirectResponse(url="/")


