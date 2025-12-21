"""
WebSocket Connection Manager

Handles real-time communication with frontend clients.
"""

from typing import Dict, List, Set
from fastapi import WebSocket
import json


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Map case_id -> set of connected WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, case_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        if case_id not in self.active_connections:
            self.active_connections[case_id] = set()
        self.active_connections[case_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, case_id: str):
        """Remove a WebSocket connection."""
        if case_id in self.active_connections:
            self.active_connections[case_id].discard(websocket)
            if not self.active_connections[case_id]:
                del self.active_connections[case_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        await websocket.send_json(message)
    
    async def broadcast(self, case_id: str, message: dict):
        """Broadcast a message to all clients watching a case."""
        if case_id not in self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections[case_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.active_connections[case_id].discard(ws)
    
    async def broadcast_all(self, message: dict):
        """Broadcast a message to all connected clients."""
        for case_id in self.active_connections:
            await self.broadcast(case_id, message)
    
    def get_connection_count(self, case_id: str = None) -> int:
        """Get number of active connections."""
        if case_id:
            return len(self.active_connections.get(case_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())

