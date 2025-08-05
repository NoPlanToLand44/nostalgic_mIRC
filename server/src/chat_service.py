from .db import database, users, rooms, room_membership, active_sessions
from datetime import datetime
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
class ChatService():

    
    async def login_user(self, session_id: str, username: str) -> dict:
        try:
            # Check if user account exists
            existing_user = await database.fetch_one(users.select().where(users.c.username == username))
            
            if not existing_user:
                # Create new account
                await database.execute(users.insert().values(
                    username=username, 
                    created_at=datetime.now().isoformat()
                ))
                account_status = "created"
            else:
                account_status = "existing"
            
            # Create active session
            await database.execute(active_sessions.insert().values(
                session_id=session_id,
                username=username,
                connected_at=datetime.now().isoformat()
            ))
            
            return {"success": True, "account_status": account_status}
            
        except Exception as e:
            return {"success": False, "error": f"Login failed: {str(e)}"}

    async def logout_user(self, session_id: str):
        # Get username from session before deleting
        session = await database.fetch_one(active_sessions.select().where(active_sessions.c.session_id == session_id))
        if session:
            username = session['username']
            # Remove active session (but keep user account)
            await database.execute(active_sessions.delete().where(active_sessions.c.session_id == session_id))
            # Remove user from all rooms for this session only
            await database.execute(room_membership.delete().where(room_membership.c.username == username))
            return username
        return None

    async def get_user_list(self) -> list[str]:
        # Get only currently active users
        rows = await database.fetch_all(active_sessions.select())
        return [r["username"] for r in rows]


    async def create_room(self, room_name:str):
        #  create one if it doesnt exist
        if not await database.fetch_one(rooms.select().where(rooms.c.name == room_name)):
            await database.execute(rooms.insert().values(name=room_name))

    async def join_room(self, session_id: str, room_name: str) -> list[str]:
        # Get username from session
        session = await database.fetch_one(active_sessions.select().where(active_sessions.c.session_id == session_id))
        if not session:
            return []
            
        username = session['username']
        await self.create_room(room_name)
        
        # Check if user already in room
        existing = await database.fetch_one(
            room_membership.select().where(
                (room_membership.c.room_name == room_name) &
                (room_membership.c.username == username)
            )
        )
        
        if not existing:
            await database.execute(
                room_membership.insert().values(room_name=room_name, username=username)
            )
        
        return await self.group_fetch_all_members(room_name)

    
    async def group_fetch_all_members(self, room_name: str) -> list[str]: 
        membs = await database.fetch_all(
            room_membership.select().where(
                room_membership.c.room_name == room_name
            )
        )
        # Return usernames directly since we now store usernames in room_membership
        return [m['username'] for m in membs] 


    def build_msg(self, from_username: str, target: str, body: str) -> str:
        return json.dumps({
            "type": "msg",
            "from": from_username,
            "target": target, 
            "body" : body
        })
    
    async def get_room_list(self) -> list[str]:
        rows = await database.fetch_all(rooms.select())
        return [r["name"] for r in rows]
    
    async def leave_room(self, session_id: str, room_name: str):
        # Get username from session
        session = await database.fetch_one(active_sessions.select().where(active_sessions.c.session_id == session_id))
        if session:
            username = session['username']
            await database.execute(
                room_membership.delete().where(
                    (room_membership.c.room_name == room_name) & 
                    (room_membership.c.username == username)
                )
            )
   