from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dataclasses import dataclass
import uuid
import json

@dataclass
class ConnectionManager():
    def __init__(self) -> None:
        self.active_connections: dict = {}
    async def connect(self, ws: WebSocket):
        await ws.accept()
        id = str(uuid.uuid4())
        self.active_connections[id] = ws

        await self.send_message_to(ws, json.dumps({"type ": "connect", "id" : id}))

    def disconnect(self, ws: WebSocket):
        try:
            id = self.find_connection_id(ws)
            if id:
                del self.active_connections[id]
                print(f"client {id} disonnected")
                return id
        except(ValueError, KeyError):
            print("connection not found durring disconnection")
        return None            




    async def send_message_to(self,ws:WebSocket, ms: str):

        try:
            await ws.send_text(ms)
        except Exception as e : 
            print(f"error sending message: {e} in send_message_to() function @ server ")

    def find_connection_id(self, ws:WebSocket):
        for id , conn in self.active_connections.items():
            if conn == ws : 
                return id
        return None



    async def broadcast(self, ms:str):

        conn_copy = list(self.active_connections.values()
                         )
        for conn in conn_copy:
            try:
                await conn.send_text(ms)
            except Exception as e: 
                print(f"error broadcasting : {e}")










app = FastAPI()

connection_manager = ConnectionManager()

@app.get("/")
async def read_root():
    return {"message": "server is running "}


@app.websocket("/messaging")
async def websocket_endpoint(ws:WebSocket):
    # accept connection from the client
    await connection_manager.connect(ws)
    try:
        while True:
            # receive the message from the client 
            data = await ws.receive_text()
            print(f" Received data: {data}")
            # send the message to all the clients 
            await connection_manager.broadcast(data)
    except WebSocketDisconnect:
        # remove the connection from the list of active connections 
        id = connection_manager.disconnect(ws)
        if id: 

            await connection_manager.broadcast(json.dumps({"type" : "disconnected", "id: ": id}))
