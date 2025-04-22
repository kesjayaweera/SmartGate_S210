from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from pathlib import Path
from controllers.db_controller import *
from starlette.websockets import WebSocketState
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
    api_base_url="https://api.github.com",
    client_kwargs={"scope": "user:email"},
)

session_initialised = False

async def get_user_from_session(request: Request):
    return request.session.get('user')

async def render_page(template_name: str, title: str, request: Request, extra_context: dict = None):
    user = await get_user_from_session(request)
    context = {"request": request, "user": user, "title": title}
    if extra_context:
        context.update(extra_context)
    return pages.TemplateResponse(template_name, context)

@root_router.get("/")
async def dashboard(request: Request):
    global session_initialised
    if not session_initialised:
        request.session.clear()
        clear_all_users()
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

def get_user_data():
    data = get_user_overview()
    return [{"username": row[0], "role_name": row[1], "status": row[2]} for row in data]

@root_router.get("/data")
async def data(request: Request):
    user_data = get_user_data()
    return await render_page("data.html", "Data", request, {"user_data": user_data})

@root_router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.github.authorize_redirect(request, redirect_uri)

@root_router.get("/auth")
async def auth(request: Request):
    token = await oauth.github.authorize_access_token(request)
    response = await oauth.github.get('user', token=token)
    user = response.json()

    request.session['user'] = {
        "username": user["login"],
        "avatar_url": user["avatar_url"]
    }

    insert_user({"id": user["id"], "login": user["login"], "role_id": 1})
    mark_user_logged_in(user["login"])

    await broadcast_user_overview()
    return RedirectResponse(url="/")

@root_router.get("/dummy-login")
async def dummy_login(request: Request):
    dummy_user = {
        "username": "Dummy",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/1674/1674295.png"
    }

    request.session['user'] = dummy_user
    insert_user({"id": 9999, "login": dummy_user["username"], "role_id": 1})
    mark_user_logged_in(dummy_user["username"])
    
    await broadcast_user_overview()
    return RedirectResponse(url="/")

@root_router.get("/logout")
async def logout(request: Request):
    user = await get_user_from_session(request)
    if user and "username" in user:
        username = user["username"]
        if is_user_logged_in(username):
            mark_user_logged_out(username)
        request.session.clear()
    await broadcast_user_overview()
    return RedirectResponse(url="/")

@root_router.get("/removed")
async def user_has_been_removed(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@root_router.get("/get-username")
async def get_username(user: dict = Depends(get_user_from_session)):
    if user and "username" in user:
        return {"username": user["username"]}
    return {"error": "Not logged in"}

@root_router.get("/get-session-username")
async def get_session_username(request: Request):
    user = await get_user_from_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"username": user["username"]}

@root_router.get("/check-permission")
async def check_permission_api(username: str, perm_name: str):
    allowed = check_permission(username, perm_name)
    return JSONResponse(content={"allowed": allowed})

websocket_state = {}

async def broadcast_data(event: str, data: dict):
    disconnected_clients = []

    for ws in list(websocket_state.keys()):
        try:
            if ws.application_state == WebSocketState.CONNECTED:
                await ws.send_json({"event": event, "data": data})
            else:
                disconnected_clients.append(ws)
        except Exception as e:
            print(f"Failed to send to a client: {e}")
            disconnected_clients.append(ws)

    # Clean up dead connections
    for ws in disconnected_clients:
        websocket_state.pop(ws, None)

async def broadcast_user_overview():
    user_data = fetch_user_data()
    await broadcast_data("user_overview", user_data)

def fetch_user_data():
        return {
            "user_data": get_user_data(),
            "roles": get_all_roles()
        }

async def kick_user(username: str, current_user: str):
    if username == current_user:
        print(f"Skipping User: {current_user}")
        return
    
    for ws, state in list(websocket_state.items()):
        if state.get("username") == username:
            try:
                # Send a redirect event only to the WebSocket corresponding to the user
                await ws.send_json({"event": "redirect", "username": username, "url": "/removed"})
                await ws.close()
                del websocket_state[ws]
                print(f"User {username} has been kicked out and connection closed.")
            except Exception as e:
                print(f"Error kicking user {username}: {e}")

@root_router.post("/remove-user")
async def remove_selected_user(request: Request):
    try:
        # Get the current logged-in user
        current_user = await get_user_from_session(request)
        current_username = current_user["username"]

        # Get the username of the user to be removed
        data = await request.json()
        username_to_remove = data.get("username")

        # Check if the current user is trying to remove themselves
        if username_to_remove == current_username:
            return JSONResponse(
                {"alert": "You cannot remove yourself."},
                status_code=400
            )
        
        remove_user(username_to_remove)
        print(f"User {username_to_remove} removed from database.")

        await kick_user(username_to_remove, current_user)
        await broadcast_user_overview()
        return JSONResponse({"message": f"User {username_to_remove} removed and kicked out!"})
    except Exception as e:
        print(f"Error removing user: {e}")
        return JSONResponse({"error": "An error occurred while removing the user."}, status_code=500)

@root_router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    from controllers.websocket_events import event_registry 
    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            data = message.get("data", {})

            handler = event_registry.get(event)
            if handler:
                result = await handler(websocket, data)
                if result:
                    await websocket.send_json(result)
            else:
                await websocket.send_json({
                    "event": "error",
                    "message": f"Unknown event: {event}"
                })

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")
    except asyncio.CancelledError:
        pass
    finally:
        websocket_state.pop(websocket, None)
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()
        except Exception as e:
            print(f"WebSocket cleanup error: {e}")
