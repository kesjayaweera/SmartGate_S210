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

routes = [
    # (route, html file, title)
    ("/", "Index.html", "Dashboard"),
    ("/gates", "gates.html", "Gates"),
    ("/about", "about.html", "About"),
    ("/alerts", "alerts.html", "Alerts")
]

# Dependency function to fetch user from session
async def get_user_from_session(request: Request):
    return request.session.get('user', None)

def render_template_with_user(template_name: str, title: str):
    async def view(request: Request, user: dict = Depends(get_user_from_session)):
        return pages.TemplateResponse(template_name, {
            "request": request,
            "title": title,
            "user": user
        })
    return view

for path, template, title in routes:
    root_router.add_api_route(
        path,
        render_template_with_user(template, title),
        response_class=HTMLResponse
    )

# New /data route
@root_router.get("/data")
async def data(request: Request, user: dict = Depends(get_user_from_session)):
    data = get_user_overview()  # Fetch user data from the database
    user_data = [{"username": row[0], "role_name": row[1]} for row in data]  # Format the data
    return pages.TemplateResponse("data.html", {
        "request": request, 
        "user_data": user_data, 
        "user": user, 
        "title": "Data"
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
                print("Sending data to client:", user_data)  # Log the data being sent
                await websocket.send_json(user_data)
                previous_data = current_data_json

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")
    except asyncio.CancelledError:
        print("WebSocket task cancelled")
        # Handle any cleanup if necessary
    finally:
        await websocket.close()

# Use get_username to check if the user is logged in
@root_router.websocket("/ws/user-status")
async def websocket_user_status(websocket: WebSocket):
    pass
