from fastapi import APIRouter, Request, Depends
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
    api_base_url="https://api.github.com",  # Add this line
    client_kwargs={"scope": "user:email"},
)

# Dependency function to fetch user from session
async def get_user_from_session(request: Request):
    return request.session.get('user', None)

@root_router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(get_user_from_session)):
    return pages.TemplateResponse("Index.html", {
        "request": request,
        "title": "Dashboard",
        "user": user 
    })

@root_router.get("/gates", response_class=HTMLResponse)
async def gates(request: Request, user: dict = Depends(get_user_from_session)):
    return pages.TemplateResponse("gates.html", {
        "request": request,
        "title": "Gates",
        "user": user 
    })

@root_router.get("/login")
async def login(request:Request):
    redirect_uri = request.url_for("auth")
    return await oauth.github.authorize_redirect(request, redirect_uri)

@root_router.get("/auth")
async def auth(request: Request):
    token = await oauth.github.authorize_access_token(request)
    response = await oauth.github.get('user', token=token)
    
    # Parse the JSON response
    user = response.json()
    #print(user)
    # Store the user information in the request state for later use
    request.session['user'] = {
        "username": user["login"],  # GitHub's username
        "avatar_url": user["avatar_url"]  # GitHub's avatar URL
    }

    # Redirect to dashboard after successful login
    return RedirectResponse(url="/")

@root_router.get("/logout")
async def logout(request: Request):
    # Remove user info from the request state to log the user out
    request.session.clear()

    # Redirect to the homepage or login page
    return RedirectResponse(url="/")


