from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uuid, json


class ConnectionManager():
    def __init__(self) -> None:
       
       self.connections: dict[str, WebSocket] = {}


    async def connect(self, ws: WebSocket):
        # handles all the connections and returns an id so it can be used in the main loop 
        # this will be when the client is  connecting to the endpoint
        await ws.accept()
        client_id = str(uuid.uuid4())
        self.connections[client_id] = ws
        return client_id 

    async def disconnect(self, client_id):
        self.connections.pop(client_id, None)



    async def send(self, client_id:str, payload:str):
        # send a message to any specific socket
        ws = self.connections.get(client_id)
        if ws: 
            await ws.send_text(payload)


    async def broadcast_all(self, payload:str):
        for ws in list(self.connections.values()):
            try: 
                await ws.send_text(payload)
            except Exception as e:
                print(f"error in broadcasting to everyone {e}") 
