from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from pathlib import Path
from controllers.db_controller import *
from starlette.websockets import WebSocketState
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
import plotly.graph_objects as go

# ------------------------
# Router and OAuth Setup
# -----------------------
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

# --------------------------------------------
# Global Classes for Pushing or Sending Data
# --------------------------------------------
class GateData(BaseModel):
    gate_no: int
    gate_status: str

class updateGateData(BaseModel):
    gate_no: int
    new_status: str

# -------------------
# Global Variables
# -------------------
session_initialised = False
websocket_state = {}

# ------------------------------------
# Decorator Functions (if necessary)
# ------------------------------------
# def auto_broadcast_user_overview(func):
#     async def wrapper(*args, **kwargs):
#         response = await func(*args, **kwargs)
#         await broadcast_user_overview()
#         return response
#     return wrapper

# -------------------
# Helper Functions
# ------------------
async def get_user_from_session(request: Request):
    return request.session.get('user')

def get_alert_data():
    data = get_all_alerts()
    return [
        {       
            "alert_no": row[0],
            "alert_desc": row[1],
            "alert_level": row[2],
            "date_and_time": row[3].isoformat() if isinstance(row[3], datetime) else row[3]
        }
        for row in data
    ]

def get_user_data():
    data = get_user_overview()
    return [
        {
            "username": row[0], 
            "role_name": row[1], 
            "status": row[2]
        } 
        for row in data
    ]

async def render_page(template_name: str, title: str, request: Request, extra_context: dict = None):
    user = await get_user_from_session(request)
    context = {"request": request, "user": user, "title": title}
    if extra_context:
        context.update(extra_context)
    return pages.TemplateResponse(template_name, context)

# -------------
# Web Routes
# -------------
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
    alert_data = get_alert_data()
    return await render_page("alerts.html", "Alerts", request, {"alert_data": alert_data})

@root_router.get("/users")
async def data(request: Request):
    user_data = get_user_data()
    return await render_page("users.html", "Users", request, {"user_data": user_data})

@root_router.get("/stats")
async def stats(request: Request):
    return await render_page("stats.html", "Stats", request)

@root_router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.github.authorize_redirect(request, redirect_uri)

@root_router.get("/health")
async def health(request: Request):
    try:
        # Example: Check database connectivity
        db_status = check_db_connection()  # Replace with your actual DB check logic
        if not db_status:
            return JSONResponse(content={"status": "unhealthy", "reason": "Database unavailable"}, status_code=500)
        return JSONResponse(content={"web-status": "ok", "db-status": "ok"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "unhealthy", "reason": str(e)}, status_code=500)

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
    return RedirectResponse(url="/gates")

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
    return RedirectResponse(url="/gates")

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


@root_router.get("/test")
async def test_endpoint(request: Request):
    """Test endpoint that logs origin IP, waits 30s, then sends gate open request back"""
    client_ip = request.client.host
    
    # Log the request
    print(f"[+] Test endpoint accessed from IP: {client_ip}")
    print(f"[+] Connection test successful! Starting 30-second timer...")
    
    # Start background task to send gate open request after 30 seconds
    import asyncio
    asyncio.create_task(send_gate_open_after_delay(client_ip))
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "test endpoint working - gate will open in 30 seconds",
            "client_ip": client_ip,
            "timestamp": datetime.now().isoformat()
        }
    )

async def send_gate_open_after_delay(smartgate_ip: str):
    """Wait 30 seconds then send gate open request to SmartGate device"""
    import asyncio
    import httpx
    
    print(f"[+] Waiting 30 seconds before sending gate open request...")
    
    # Countdown timer
    for i in range(30, 0, -1):
        print(f"[+] Sending gate open request in {i} seconds...", end='\r')
        await asyncio.sleep(1)
    
    print(f"\n[+] Sending gate open request to SmartGate device...")
    print(f"[+] Target IP: {smartgate_ip}:8000")
    
    try:
        # Send POST request to SmartGate device
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"http://{smartgate_ip}:8000/",
                json={"command": "OPEN_DOOR"},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"[+] SUCCESS: Gate open command sent to SmartGate!")
                print(f"[+] Response: {response.text}")
            else:
                print(f"[-] FAILED: SmartGate returned HTTP {response.status_code}")
                print(f"[-] Response: {response.text}")
                
    except httpx.ConnectError:
        print(f"[-] FAILED: Could not connect to SmartGate at {smartgate_ip}:8000")
        print(f"[-] Make sure the SmartGate device is running and accessible")
    except httpx.TimeoutException:
        print(f"[-] FAILED: SmartGate connection timeout (10 seconds)")
    except Exception as e:
        print(f"[-] FAILED: Unexpected error: {str(e)}")

# ---------------------------------
# Broadcasting Live Data Functions
# ---------------------------------

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

def fetch_user_data():
        return {
            "user_data": get_user_data(),
            "roles": get_all_roles()
        }

def fetch_alerts_data():
    return {
        "alert_data": get_alert_data()
    }

async def broadcast_alert_data():
    alert_data = fetch_alerts_data()
    await broadcast_data("alert_data", alert_data)

async def broadcast_user_overview():
    user_data = fetch_user_data()
    await broadcast_data("user_overview", user_data)

# --------------------
# WebSocket Functions
# -------------------
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

# -------------------
# Post Routes
# -------------------
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

@root_router.post("/add_gate_data")
async def push_data_from_gate_to_db(gate_data: GateData):
    gate_no = gate_data.gate_no
    gate_status = gate_data.gate_status
    
    # Call the function to add gate data
    add_gate(gate_no, gate_status)
    
    return JSONResponse({"message": f"Gate {gate_no} status {gate_status} added successfully"})

# add data to database for opening and closing gates
@root_router.post("/update_gate_data")
async def update_gate_data(payload: updateGateData):
    update_gate_status(payload.gate_no, payload.new_status)
    return JSONResponse({"message": f"Gate {payload.gate_no} status {payload.new_status} updated successfully"})

# -------------------
# WebSocket Route
# ------------------
@root_router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    from controllers.websocket_events import event_registry 
    await websocket.accept()

    # -------------------------------------
    # Send Up to Date Data to Web Socket
    # -------------------------------------
    # Send alert data immediately on connect
    alert_handler = event_registry.get("alert_data")
    if alert_handler:
        result = await alert_handler(websocket, {})
        if result:
            await websocket.send_json(result)

    # ----------------------------------------------
    # Send Data to WebSocket After Event Recieved
    # ----------------------------------------------
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
