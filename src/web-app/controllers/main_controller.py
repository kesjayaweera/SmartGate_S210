from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from pathlib import Path
from controllers.db_controller import *
from starlette.websockets import WebSocketState, WebSocket
from starlette.requests import Request
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

    # Mark user as logged in
    mark_user_logged_in(user["login"])

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
    if user and "username" in user:
        mark_user_logged_out(user["username"])
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

# This is used to track the current state of data 
# that is sent to the websocket connection
websocket_state = {}

async def send_user_overview(websocket: WebSocket, event: str):
    # Retrieve user data from DB
    data = get_user_overview()
    user_data = [{"username": row[0], "role_name": row[1], "status": row[2]} for row in data]

    # Convert to JSON string for easy comparison
    current_data_json = json.dumps(user_data, sort_keys=True)

    # Get previous data for this specific WebSocket connection
    previous_data = websocket_state.get(websocket, None)

    # If the data has changed, send the new data and update the stored state
    if current_data_json != previous_data:
        websocket_state[websocket] = current_data_json
        return {
            "event": event,
            "data": user_data
        }
    
    return None

# A default handler for unknown events
async def handle_unknown_event(websocket: WebSocket, event: str):
    print(f"Unknown event: {event}")

event_handler = {
    "user_overview": send_user_overview,
}

@root_router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_json()
            event = message.get('event')

            # Dynamically call the appropriate handler based on the event
            handler = event_handler.get(event, handle_unknown_event)

            # Just call the handler 
            result = await handler(websocket, event)

            if result:
                await websocket.send_json(result)

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")
    except asyncio.CancelledError:
        pass
    finally:
        # Clean up state when the connection closes
        if websocket in websocket_state:
            del websocket_state[websocket]
        try:
            # Check if the WebSocket is still connected before attempting to close
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()  # Close the connection once
        except RuntimeError:
            # Ignore the error if WebSocket is already closed due to Ctrl+C
            print("WebSocket already closed.")
        except WebSocketDisconnect:
            # If the disconnect happens during shutdown, handle it gracefully
            print("WebSocket was disconnected during shutdown.")
