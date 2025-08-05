from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dataclasses import dataclass
import uuid, json
from contextlib import asynccontextmanager
from .connection_manager import ConnectionManager
from .chat_service import ChatService
from .db import database , users , rooms, room_membership, active_sessions
 









mngr = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan) 
chat = ChatService()

@app.get("/")
async def read_root():
    return {"message": "server is running "}


@app.websocket("/messaging")
async def websocket_endpoint(ws:WebSocket):
    # accept connection from the client
    client_id = await mngr.connect(ws)
    await mngr.send(client_id, json.dumps({
        "type": "welcome",
        "id" : client_id
    }))

    try:
        init = json.loads(await ws.receive_text())
        username = init.get("username", f"anon-{client_id[:4]}")
        login_result = await chat.login_user(client_id, username)
        
        if not login_result["success"]:
            # Login failed, send error and close connection
            await mngr.send(client_id, json.dumps({
                "type": "error",
                "message": login_result["error"]
            }))
            await mngr.disconnect(client_id)
            return
        
        # Login successful, send confirmation
        account_status = login_result.get("account_status", "existing")
        status_msg = "Account created!" if account_status == "created" else "Welcome back!"
        
        await mngr.send(client_id, json.dumps({
            "type": "login_success",
            "username": username,
            "message": status_msg
        }))

        # broadcast updated user list 
        users = await chat.get_user_list()
        await mngr.broadcast_all(json.dumps({
            "type":"user_list",
            "users": users
        }))
        while True: 
            msg = json.loads(await ws.receive_text())
            if msg['type'] == "join":
                members = await chat.join_room(client_id, msg["room"])
                await mngr.send(client_id, json.dumps({
                    "type":"room_info",
                    "rooms": msg['room'],
                    "members": members
                }))
            elif msg['type'] == "list":
                room_list = await chat.get_room_list()
                await mngr.send(client_id, json.dumps({
                    "type": "room_list",
                    "rooms": room_list
                }))
            elif msg['type'] == "who":
                members = await chat.group_fetch_all_members(msg["room"])
                await mngr.send(client_id, json.dumps({
                    "type": "room_info",
                    "rooms": msg["room"],
                    "members": members
                }))
            elif msg['type'] == "part":
                await chat.leave_room(client_id, msg["room"])
                await mngr.send(client_id, json.dumps({
                    "type": "msg",
                    "from": "system",
                    "target": "system", 
                    "body": f"Left room: {msg['room']}"
                }))
            elif msg['type'] == "msg":
                payload = chat.build_msg(username, msg['target'], msg['body'])

                #to room
                if await database.fetch_one(rooms.select().where(rooms.c.name == msg['target'])):
                    rows = await database.fetch_all(
                        room_membership.select().where(
                            room_membership.c.room_name == msg['target']
                        )
                    )
                    # Send to all active sessions of users in the room
                    for row in rows:
                        target_username = row['username']
                        # Find active session for this username
                        session = await database.fetch_one(
                            active_sessions.select().where(active_sessions.c.username == target_username)
                        )
                        if session:
                            await mngr.send(session['session_id'], payload)
                else:
                    # to user (private message)
                    target_session = await database.fetch_one(
                        active_sessions.select().where(active_sessions.c.username == msg['target'])
                    )
                    if target_session: 
                        await mngr.send(target_session['session_id'], payload)
                    else:
                        await mngr.send(client_id, json.dumps({
                            "type": "msg",
                            "from": "system",
                            "target": "system",
                            "body": f"User '{msg['target']}' not online"
                        }))


    except WebSocketDisconnect:
        username = await chat.logout_user(client_id)
        await mngr.disconnect(client_id)
        if username:
            users = await chat.get_user_list()
            await mngr.broadcast_all(json.dumps({
                "type": "user_list",
                "users": users
            }))