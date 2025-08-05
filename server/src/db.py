from sqlalchemy import MetaData, Table, Column, String
from databases import Database
import sqlalchemy


DATABASE_URL = "sqlite:///./chat.db"
metadata = MetaData()

database = Database(DATABASE_URL)


users = Table(
    "users",
    metadata,
    Column("username", String, primary_key = True),
    Column("created_at", String),
)

# Active sessions table to track who is currently online
active_sessions = Table(
    "active_sessions",
    metadata,
    Column("session_id", String, primary_key = True),
    Column("username", String),
    Column("connected_at", String),
)

rooms = Table(
    "rooms",
    metadata,
    Column("name" , String, primary_key = True)
)

room_membership = Table(
    "room_membership",
    metadata,
    Column('room_name', String),
    Column("username", String),

)

room_chat_history = Table(
    "room_chat_history",
    metadata,
    Column("room_name", String),
    Column("full_history", String),

)

engine = sqlalchemy.create_engine(DATABASE_URL)

# Drop all tables and recreate with new schema
metadata.drop_all(engine)
metadata.create_all(engine)