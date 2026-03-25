"""WebRTC signaling service for peer-to-peer audio/video communication"""
import json
import uuid
from typing import Optional, Dict, Any, Set
from datetime import datetime

from app.utils.log_helper import get_logger

logger = get_logger("services.webrtc")


class WebRTCConnection:
    """Represents a WebRTC connection between users"""

    def __init__(
        self,
        connection_id: str,
        session_id: str,
        host_user_id: int,
        guest_user_id: Optional[int] = None
    ):
        self.connection_id = connection_id
        self.session_id = session_id
        self.host_user_id = host_user_id
        self.guest_user_id = guest_user_id
        self.host_offer: Optional[Dict] = None
        self.guest_offer: Optional[Dict] = None
        self.host_answer: Optional[Dict] = None
        self.guest_answer: Optional[Dict] = None
        self.host_ice_candidates: list[Dict] = []
        self.guest_ice_candidates: list[Dict] = []
        self.status: str = "pending"  # pending, connected, disconnected, failed
        self.created_at = datetime.now()
        self.connected_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert connection to dictionary"""
        return {
            "connection_id": self.connection_id,
            "session_id": self.session_id,
            "host_user_id": self.host_user_id,
            "guest_user_id": self.guest_user_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "connected_at": self.connected_at.isoformat() if self.connected_at else None
        }


class WebRTCService:
    """Service for managing WebRTC signaling"""

    def __init__(self):
        # Store connections: {connection_id: WebRTCConnection}
        self.connections: Dict[str, WebRTCConnection] = {}
        # Store session connections: {session_id: connection_id}
        self.session_connections: Dict[str, str] = {}

    def create_connection(
        self,
        session_id: str,
        host_user_id: int,
        guest_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new WebRTC connection

        Args:
            session_id: Interview session ID
            host_user_id: Host user ID (interviewer)
            guest_user_id: Guest user ID (candidate), None for self-conference

        Returns:
            Dict containing connection details
        """
        # Check if connection already exists for session
        if session_id in self.session_connections:
            existing_conn_id = self.session_connections[session_id]
            if existing_conn_id in self.connections:
                conn = self.connections[existing_conn_id]
                logger.info(
                    f"Returning existing connection {existing_conn_id} "
                    f"for session {session_id}"
                )
                return {
                    "success": True,
                    "connection_id": conn.connection_id,
                    "session_id": conn.session_id,
                    "status": conn.status,
                    "host_user_id": conn.host_user_id,
                    "guest_user_id": conn.guest_user_id
                }

        # Create new connection
        connection_id = str(uuid.uuid4())
        connection = WebRTCConnection(
            connection_id,
            session_id,
            host_user_id,
            guest_user_id
        )

        self.connections[connection_id] = connection
        self.session_connections[session_id] = connection_id

        logger.info(
            f"Created WebRTC connection {connection_id} for session {session_id}"
        )

        return {
            "success": True,
            "connection_id": connection_id,
            "session_id": session_id,
            "status": connection.status,
            "host_user_id": host_user_id,
            "guest_user_id": guest_user_id
        }

    def get_connection(self, connection_id: str) -> Optional[WebRTCConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    def get_connection_by_session(self, session_id: str) -> Optional[WebRTCConnection]:
        """Get connection by session ID"""
        connection_id = self.session_connections.get(session_id)
        if connection_id:
            return self.connections.get(connection_id)
        return None

    def set_host_offer(
        self,
        connection_id: str,
        offer: Dict
    ) -> Dict[str, Any]:
        """Set SDP offer from host"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.host_offer = offer
        conn.status = "offer_sent"
        logger.info(f"Host offer set for connection {connection_id}")

        return {"success": True, "connection_id": connection_id}

    def set_guest_offer(
        self,
        connection_id: str,
        offer: Dict
    ) -> Dict[str, Any]:
        """Set SDP offer from guest"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.guest_offer = offer
        conn.status = "offer_received"
        logger.info(f"Guest offer set for connection {connection_id}")

        return {"success": True, "connection_id": connection_id}

    def set_host_answer(
        self,
        connection_id: str,
        answer: Dict
    ) -> Dict[str, Any]:
        """Set SDP answer from host"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.host_answer = answer
        self._check_connection_status(conn)
        logger.info(f"Host answer set for connection {connection_id}")

        return {"success": True, "connection_id": connection_id}

    def set_guest_answer(
        self,
        connection_id: str,
        answer: Dict
    ) -> Dict[str, Any]:
        """Set SDP answer from guest"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.guest_answer = answer
        self._check_connection_status(conn)
        logger.info(f"Guest answer set for connection {connection_id}")

        return {"success": True, "connection_id": connection_id}

    def add_host_ice_candidate(
        self,
        connection_id: str,
        candidate: Dict
    ) -> Dict[str, Any]:
        """Add ICE candidate from host"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.host_ice_candidates.append(candidate)
        logger.debug(f"Host ICE candidate added for connection {connection_id}")

        return {"success": True, "connection_id": connection_id}

    def add_guest_ice_candidate(
        self,
        connection_id: str,
        candidate: Dict
    ) -> Dict[str, Any]:
        """Add ICE candidate from guest"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.guest_ice_candidates.append(candidate)
        logger.debug(f"Guest ICE candidate added for connection {connection_id}")

        return {"success": True, "connection_id": connection_id}

    def get_host_ice_candidates(
        self,
        connection_id: str
    ) -> list[Dict]:
        """Get all ICE candidates from host"""
        conn = self.connections.get(connection_id)
        if conn:
            return conn.host_ice_candidates
        return []

    def get_guest_ice_candidates(
        self,
        connection_id: str
    ) -> list[Dict]:
        """Get all ICE candidates from guest"""
        conn = self.connections.get(connection_id)
        if conn:
            return conn.guest_ice_candidates
        return []

    def get_offer_for_guest(
        self,
        connection_id: str
    ) -> Optional[Dict]:
        """Get host's offer for guest"""
        conn = self.connections.get(connection_id)
        if conn:
            return conn.host_offer
        return None

    def get_offer_for_host(
        self,
        connection_id: str
    ) -> Optional[Dict]:
        """Get guest's offer for host"""
        conn = self.connections.get(connection_id)
        if conn:
            return conn.guest_offer
        return None

    def get_answer_for_guest(
        self,
        connection_id: str
    ) -> Optional[Dict]:
        """Get host's answer for guest"""
        conn = self.connections.get(connection_id)
        if conn:
            return conn.host_answer
        return None

    def get_answer_for_host(
        self,
        connection_id: str
    ) -> Optional[Dict]:
        """Get guest's answer for host"""
        conn = self.connections.get(connection_id)
        if conn:
            return conn.guest_answer
        return None

    def close_connection(
        self,
        connection_id: str
    ) -> Dict[str, Any]:
        """Close a WebRTC connection"""
        conn = self.connections.get(connection_id)
        if not conn:
            return {
                "success": False,
                "error": "Connection not found"
            }

        conn.status = "disconnected"
        session_id = conn.session_id

        # Remove from session mapping
        if session_id in self.session_connections:
            del self.session_connections[session_id]

        logger.info(f"Closed WebRTC connection {connection_id}")

        return {
            "success": True,
            "connection_id": connection_id,
            "status": "disconnected"
        }

    def _check_connection_status(self, conn: WebRTCConnection):
        """Check if connection is fully established"""
        # For self-conference (no guest), check host offer/answer
        if conn.guest_user_id is None:
            if conn.host_offer and conn.host_answer:
                conn.status = "connected"
                if not conn.connected_at:
                    conn.connected_at = datetime.now()
                logger.info(f"Self-conference connected: {conn.connection_id}")
            return

        # For two-way connection, check all offers/answers
        if (conn.host_offer and conn.guest_offer and
            conn.host_answer and conn.guest_answer):
            conn.status = "connected"
            if not conn.connected_at:
                conn.connected_at = datetime.now()
            logger.info(f"Connection fully established: {conn.connection_id}")

    def get_connection_info(
        self,
        connection_id: str
    ) -> Optional[Dict]:
        """Get detailed connection info"""
        conn = self.connections.get(connection_id)
        if conn:
            return {
                "connection_id": conn.connection_id,
                "session_id": conn.session_id,
                "host_user_id": conn.host_user_id,
                "guest_user_id": conn.guest_user_id,
                "status": conn.status,
                "created_at": conn.created_at.isoformat(),
                "connected_at": conn.connected_at.isoformat() if conn.connected_at else None,
                "has_host_offer": conn.host_offer is not None,
                "has_guest_offer": conn.guest_offer is not None,
                "has_host_answer": conn.host_answer is not None,
                "has_guest_answer": conn.guest_answer is not None,
                "host_ice_candidates_count": len(conn.host_ice_candidates),
                "guest_ice_candidates_count": len(conn.guest_ice_candidates)
            }
        return None

    def cleanup_old_connections(self, max_age_hours: int = 24):
        """Clean up old inactive connections"""
        import time
        current_time = datetime.now()

        to_remove = []
        for conn_id, conn in self.connections.items():
            if conn.status == "disconnected":
                age = current_time - conn.created_at
                if age.total_seconds() > max_age_hours * 3600:
                    to_remove.append(conn_id)

        for conn_id in to_remove:
            del self.connections[conn_id]
            logger.info(f"Cleaned up old connection: {conn_id}")


# Global WebRTC service instance
webrtc_service = WebRTCService()
