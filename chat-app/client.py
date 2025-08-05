import asyncio 
import websockets
import json
import sys
import os


async def client():
    host = sys.argv[1] if len(sys.argv)>1 else "localhost"
    uri = f"ws://{host}:8000/messaging"
    current_room = None
    
    async with websockets.connect(uri) as ws :
        print("connected to the server")
        
        # Username registration loop
        while True:
            username = input("enter your username: ")
            await ws.send(json.dumps({
                "username": username
            }))
            
            # Wait for login response
            response = json.loads(await ws.recv())
            if response.get("type") == "error":
                print(f"Error: {response.get('message')}")
                continue
            elif response.get("type") == "login_success":
                print(f"{response.get('message', 'Logged in')} - {response.get('username')}")
                break
            elif response.get("type") == "welcome":
                # Skip welcome message, wait for login response
                response = json.loads(await ws.recv())
                if response.get("type") == "error":
                    print(f"Error: {response.get('message')}")
                    continue
                elif response.get("type") == "login_success":
                    print(f"{response.get('message', 'Logged in')} - {response.get('username')}")
                    break
        
        print("Type messages and press Enter. Type 'quit' to exit.")
        print("Commands: /join <room>, /list, /who <room>, /part, /help")
        


        # listen for messages from server
        async def listen():
            nonlocal current_room
            try:
                while True:
                    message = await ws.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "room_info":
                        current_room = data.get("rooms")
                        print(f"\n*** Joined room: {current_room} ***")
                        print(f"Members: {', '.join(data.get('members', []))}")
                    elif data.get("type") == "msg":
                        print(f"\n[{data.get('target', 'unknown')}] {data.get('from', 'unknown')}: {data.get('body', '')}")
                    elif data.get("type") == "user_list":
                        print(f"\n*** Active users: {', '.join(data.get('users', []))} ***")
                    elif data.get("type") == "room_list":
                        print(f"\n*** Available rooms: {', '.join(data.get('rooms', []))} ***")
                    else:
                        print(f"Received: {message}")
            except websockets.exceptions.ConnectionClosed:
                print("connection closed ")

        
        async def send_messages():
            nonlocal current_room
            
            while True:
                try:
                    prompt = f"[{current_room}]> " if current_room else "you> "
                    message = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: input(prompt)
                    )
                    
                    if message.lower() == "quit":
                        break
                    elif message.startswith("/join "):
                        room_name = message[6:].strip()
                        await ws.send(json.dumps({
                            "type": "join",
                            "room": room_name
                        }))
                    elif message.startswith("/list"):
                        await ws.send(json.dumps({
                            "type": "list"
                        }))
                    elif message.startswith("/who "):
                        room_name = message[5:].strip()
                        await ws.send(json.dumps({
                            "type": "who",
                            "room": room_name
                        }))
                    elif message.startswith("/part"):
                        if current_room:
                            await ws.send(json.dumps({
                                "type": "part",
                                "room": current_room
                            }))
                            current_room = None
                        else:
                            print("You are not in any room")
                    elif message.startswith("/help"):
                        print("Commands:")
                        print("/join <room> - Join a room")
                        print("/list - List available rooms")
                        print("/who <room> - List members in a room")
                        print("/part - Leave current room")
                        print("/pm <user> <message> - Send private message")
                        print("quit - Exit the chat")
                    elif message.startswith("/pm "):
                        parts = message[4:].split(' ', 1)
                        if len(parts) == 2:
                            target_user, msg_body = parts
                            await ws.send(json.dumps({
                                "type": "msg",
                                "target": target_user.strip(),
                                "body": msg_body
                            }))
                        else:
                            print("Usage: /pm <username> <message>")
                    elif message and not message.startswith("/"):
                        if current_room:
                            await ws.send(json.dumps({
                                "type": "msg",
                                "target": current_room,
                                "body": message
                            }))
                        else:
                            print("You need to join a room first or use /pm <user> <message>")
                    elif message.startswith("/"):
                        print("Unknown command. Type /help for available commands")
                        
                except Exception as e:
                    print(f"error: {e}")
                    break
        
        await asyncio.gather(listen(),send_messages())

if __name__ == "__main__":
    try:
        asyncio.run(client())
    except KeyboardInterrupt:
        print("\nExiting")