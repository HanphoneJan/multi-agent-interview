"""WebSocket connection manager"""
import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # Store active connections: {session_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        # Store last heartbeat time: {session_id: {user_id: datetime}}
        self.last_heartbeat: Dict[str, Dict[int, float]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: int):
        """Connect a new WebSocket"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}

        self.active_connections[session_id][user_id] = websocket
        print(f"✅ User {user_id} connected to session {session_id}")

    async def disconnect(self, session_id: str, user_id: int):
        """Disconnect a WebSocket"""
        if session_id in self.active_connections:
            if user_id in self.active_connections[session_id]:
                del self.active_connections[session_id][user_id]
                print(f"❌ User {user_id} disconnected from session {session_id}")

            if session_id in self.last_heartbeat:
                if user_id in self.last_heartbeat[session_id]:
                    del self.last_heartbeat[session_id][user_id]

            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

            if session_id in self.last_heartbeat and not self.last_heartbeat[session_id]:
                del self.last_heartbeat[session_id]

    async def send_message(self, message: dict, session_id: str, user_id: int):
        """Send a message to a specific user in a session"""
        if session_id in self.active_connections:
            if user_id in self.active_connections[session_id]:
                websocket = self.active_connections[session_id][user_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"❌ Error sending message to user {user_id}: {e}")

    async def broadcast(self, message: dict, session_id: str):
        """Broadcast a message to all users in a session"""
        if session_id in self.active_connections:
            for user_id, websocket in self.active_connections[session_id].items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"❌ Error broadcasting to user {user_id}: {e}")

    async def send_progress(
        self,
        session_id: str,
        user_id: int,
        stage: str,
        progress: float,
        message: str
    ):
        """Send progress update to user"""
        await self.send_message(
            {
                "type": "progress",
                "stage": stage,
                "progress": progress,
                "message": message,
            },
            session_id,
            user_id
        )

    async def send_error(
        self,
        session_id: str,
        user_id: int,
        error: str,
        error_code: str | None = None,
        suggestion: str | None = None
    ):
        """Send error message to user"""
        await self.send_message(
            {
                "type": "error",
                "error": error,
                "error_code": error_code,
                "suggestion": suggestion,
            },
            session_id,
            user_id
        )

    async def send_question(
        self,
        session_id: str,
        user_id: int,
        question: str,
        question_id: int,
        order: int
    ):
        """Send question to user"""
        await self.send_message(
            {
                "type": "question",
                "question": question,
                "question_id": question_id,
                "order": order,
            },
            session_id,
            user_id
        )

    def update_heartbeat(self, session_id: str, user_id: int):
        """Update heartbeat timestamp for a connection"""
        if session_id in self.last_heartbeat:
            self.last_heartbeat[session_id][user_id] = asyncio.get_event_loop().time()

    async def check_inactive_connections(self, timeout: float = 60.0):
        """Check for inactive connections and disconnect them"""
        current_time = asyncio.get_event_loop().time()

        # Collect inactive connections
        inactive = []
        for session_id, users in self.last_heartbeat.items():
            for user_id, last_time in users.items():
                if current_time - last_time > timeout:
                    inactive.append((session_id, user_id))

        # Disconnect inactive connections
        for session_id, user_id in inactive:
            if session_id in self.active_connections and user_id in self.active_connections[session_id]:
                try:
                    await self.active_connections[session_id][user_id].close(
                        code=status.WS_1000_NORMAL_CLOSURE,
                        reason="Connection timeout"
                    )
                    await self.disconnect(session_id, user_id)
                    print(f"⚠️ Disconnected inactive user {user_id} from session {session_id}")
                except Exception as e:
                    print(f"❌ Error disconnecting inactive connection: {e}")

    async def send_pong(self, session_id: str, user_id: int):
        """Send pong response to ping"""
        await self.send_message(
            {"type": "pong"},
            session_id,
            user_id
        )

    async def send_stream_start(self, session_id: str, user_id: int):
        """Send stream start message"""
        await self.send_message(
            {"type": "stream_start"},
            session_id,
            user_id
        )

    async def send_stream_chunk(self, session_id: str, user_id: int, chunk: str):
        """Send a stream chunk"""
        await self.send_message(
            {
                "type": "stream_chunk",
                "chunk": chunk,
            },
            session_id,
            user_id
        )

    async def send_stream_end(self, session_id: str, user_id: int, full_message: str):
        """Send stream end message"""
        await self.send_message(
            {
                "type": "stream_end",
                "full_message": full_message,
            },
            session_id,
            user_id
        )


# Global connection manager
manager = ConnectionManager()
