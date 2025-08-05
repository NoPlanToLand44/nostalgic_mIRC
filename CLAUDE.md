# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
python -m venv .venv
pip install fastapi uvicorn websockets uuid asyncio
```

### Running the Application
```bash
# Start the server (from project root)
uvicorn server.src.server:app --host 0.0.0.0 --port 8000 --reload

# Start a client (from project root)
python chat-app\client.py

# Or run client with custom host
python chat-app\client.py <hostname>
```

### Docker Commands
```bash
# Build and run with Docker Compose
docker-compose up --build

# The server will be available on port 8000
```

## Architecture

This is a mIRC-style chat application replica built with FastAPI and WebSocket connections. Like classic IRC clients, it supports real-time messaging, channel/room joining, and multi-user conversations. The system consists of three main layers:

### Server Architecture (`server/src/`)
- **server.py**: Main FastAPI application with WebSocket endpoint `/messaging` and database lifecycle management
- **connection_manager.py**: Manages WebSocket connections with unique client IDs, handles broadcasting and individual messaging
- **chat_service.py**: Core chat logic including user registration, room management, and message routing
- **db.py**: SQLAlchemy database schema with tables for users, rooms, room membership, and chat history

### Client Architecture (`chat-app/`)
- **client.py**: Async WebSocket client with concurrent message listening and sending capabilities

### Data Flow
1. Clients connect via WebSocket to `/messaging` endpoint
2. Connection Manager assigns unique UUID and manages the connection
3. Chat Service handles user registration and room operations
4. Messages are routed either to specific users (direct messages) or room members (room messages)
5. Database stores user sessions, room memberships, and chat history

### Database Schema
- `users`: Maps client IDs to usernames
- `rooms`: Stores room names
- `room_membership`: Many-to-many relationship between users and rooms
- `room_chat_history`: Stores chat history per room (defined but not actively used)

### IRC-Style Features
- **Channels/Rooms**: Users can join rooms using `/join <room_name>` command
- **Direct Messages**: Private messaging between users
- **User Lists**: Real-time display of active users
- **Persistent Connections**: WebSocket-based persistent connections like classic IRC

### Message Types
- `welcome`: Server sends client ID on connection (similar to IRC MOTD)
- `join`: Client joins a channel/room (IRC JOIN command equivalent)
- `msg`: Chat message (to user or channel)
- `user_list`: Broadcast of active users (IRC WHO command equivalent)
- `room_info`: Channel membership information

### Client Commands
- `/join <room_name>`: Join a channel/room
- Direct input prompts for message targets (room or user)
- `quit`: Disconnect from server

The application uses SQLite for persistence and supports multiple concurrent connections with real-time message broadcasting, replicating the core functionality of classic IRC clients like mIRC.