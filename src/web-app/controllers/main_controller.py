from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from pathlib import Path
from controllers.db_controller import insert_user, check_permission, get_user_overview
import json
import asyncio

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

connected_users = set()
websocket_connections = set()

# Dependency function to fetch user from session
async def get_user_from_session(request: Request):
    return request.session.get('user', None)

# Function to handle rendering templates with common context
async def render_page(template_name: str, title: str, request: Request, extra_context: dict = None):
    user = await get_user_from_session(request)
    context = {
        "request": request,
        "user": user,
        "title": title,
    }
    if extra_context:
        context.update(extra_context)
    return pages.TemplateResponse(template_name, context)

# Session initialization flag
session_initialised = False

# New / route for clearing user when / root is opened
@root_router.get("/")
async def dashboard(request: Request):
    global session_initialised
    if not session_initialised:
        request.session.clear()
        session_initialised = True
    return await render_page("Index.html", "Dashboard", request)

@root_router.get("/gates")
async def gates(request: Request):
    return await render_page("gates.html", "Gates", request)

@root_router.get("/about")
async def about(request: Request):
    return await render_page("about.html", "About", request)

@root_router.get("/alerts")
async def alerts(request: Request):
    return await render_page("alerts.html", "Alerts", request)

# New /data route
@root_router.get("/data")
async def data(request: Request):
    data = get_user_overview()  # Fetch user data from the database
    user_data = [{"username": row[0], "role_name": row[1]} for row in data]  # Format the data
    return await render_page("data.html", "Data", request, {"user_data": user_data})

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

    # Store the user information in database for web privileges 
    insert_user({
        "id": user["id"], # Getting user id from user = response.json()
        "login": user["login"], # Getting user login from user = response.json()
        "role_id": 1, # Setting user to user by default
    })

    # Redirect to dashboard after successful login
    return RedirectResponse(url="/")

# add dummy user authentication
@root_router.get("/dummy-login")
async def dummy_login(request: Request):
    dummy_user = {
        "username": "Dummy",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/1674/1674295.png"
    }

    request.session['user'] = dummy_user

    # Store the user information in database for web privileges 
    insert_user({
        "id": 9999, 
        "login": dummy_user["username"], 
        "role_id": 1, 
    })

    return RedirectResponse(url="/")

@root_router.get("/logout")
async def logout(request: Request):
    # Remove user info from the request state to log the user out
    request.session.clear()
    # Redirect to the homepage or login page
    return RedirectResponse(url="/")

@root_router.get("/get-username")
async def get_username(user: dict = Depends(get_user_from_session)):
    # print(user)  # Debugging: See the actual structure
    if user and "username" in user:
        return {"username": user["username"]}
    return {"error": "Not logged in"}   

@root_router.get("/check-permission")
async def check_permission_api(username: str, perm_name: str):
    has_permission = check_permission(username, perm_name)
    return JSONResponse(content={"allowed": has_permission})

@root_router.websocket("/ws/user-overview")
async def websocket_user_overview(websocket: WebSocket):
    await websocket.accept()
    previous_data = None

    try:
        while True:
            data = get_user_overview()  # Get from DB
            user_data = [{"username": row[0], "role_name": row[1]} for row in data]

            # Convert to JSON string for easy comparison
            current_data_json = json.dumps(user_data, sort_keys=True)

            if current_data_json != previous_data:
                await websocket.send_json(user_data)
                previous_data = current_data_json

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")
    except asyncio.CancelledError:
        pass
    finally:
        await websocket.close()

# Use get_username to check if the user is logged in
@root_router.websocket("/ws/user-status")
async def websocket_user_status(websocket: WebSocket):
    pass
