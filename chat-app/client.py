import asyncio 
import websockets
import json
import sys

async def client():
    uri = "ws://localhost:8000/messaging"

    async with websockets.connect(uri) as ws :
        print("connected to the server")
        print("Type messages and press Enter. Type 'quit' to exit.")


        # listen for messages from server
        async def listen():
            try:
                while True:
                    message = await ws.recv()
                    print(f"Received : {message}")
            except websockets.exceptions.ConnectionClosed:
                print("connection closed ")

        
        async def send_messages():

            while True:
                try:
                    message = await asyncio.get_event_loop().run_in_executor(

                        None, lambda: input("you: ")
                    )
                    if message.lower() == "quit":
                        break
                    await ws.send(message)
                except Exception as e:
                    print(f"error: {e}")
                    break
        
        await asyncio.gather(listen(),send_messages())

if __name__ == "__main__":
    try:
        asyncio.run(client())
    except KeyboardInterrupt:
        print("\nExiting")