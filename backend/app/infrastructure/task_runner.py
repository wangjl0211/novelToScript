"""WebSocket 进度广播管理。"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ProgressBroadcaster:
    """管理项目转换进度的 WebSocket 连接。"""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(project_id, []).append(websocket)

    async def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(project_id, [])
            if websocket in conns:
                conns.remove(websocket)

    async def broadcast(self, project_id: str, data: dict[str, Any]) -> None:
        """向所有订阅者广播进度。"""
        async with self._lock:
            conns = list(self._connections.get(project_id, []))
        dead: list[WebSocket] = []
        payload = json.dumps(data, ensure_ascii=False)
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(project_id, ws)


progress_broadcaster = ProgressBroadcaster()
