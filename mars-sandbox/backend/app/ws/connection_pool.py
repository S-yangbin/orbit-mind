"""
WebSocket connection pool
Manages active WebSocket connections to home-agent nodes
"""

import asyncio
import logging
from typing import Dict, Optional
from websockets.asyncio.server import ServerConnection

logger = logging.getLogger(__name__)


class ConnectionPool:
    """管理所有home-agent的WebSocket连接"""
    
    def __init__(self):
        # node_id -> WebSocket连接
        self._connections: Dict[str, ServerConnection] = {}
        # node_id -> 最后心跳时间
        self._heartbeats: Dict[str, float] = {}
        # 读写锁
        self._lock = asyncio.Lock()
    
    async def register(self, node_id: str, websocket: ServerConnection):
        """注册新的WebSocket连接"""
        async with self._lock:
            # 如果节点已有连接,关闭旧连接
            if node_id in self._connections:
                logger.warning("节点 %s 已有连接,关闭旧连接", node_id)
                old_ws = self._connections[node_id]
                try:
                    await old_ws.close()
                except Exception:
                    pass
            
            self._connections[node_id] = websocket
            self._heartbeats[node_id] = asyncio.get_event_loop().time()
            logger.info("节点 %s 已注册,当前在线节点数: %d", node_id, len(self._connections))
    
    async def unregister(self, node_id: str):
        """注销WebSocket连接"""
        async with self._lock:
            if node_id in self._connections:
                del self._connections[node_id]
                if node_id in self._heartbeats:
                    del self._heartbeats[node_id]
                logger.info("节点 %s 已注销,当前在线节点数: %d", node_id, len(self._connections))
    
    async def get_connection(self, node_id: str) -> Optional[ServerConnection]:
        """获取节点的WebSocket连接"""
        async with self._lock:
            return self._connections.get(node_id)
    
    async def update_heartbeat(self, node_id: str):
        """更新节点心跳时间"""
        async with self._lock:
            if node_id in self._connections:
                self._heartbeats[node_id] = asyncio.get_event_loop().time()
    
    async def get_stale_nodes(self, stale_seconds: float = 180.0) -> list:
        """获取超时的节点列表"""
        current_time = asyncio.get_event_loop().time()
        stale_nodes = []
        
        async with self._lock:
            for node_id, last_heartbeat in self._heartbeats.items():
                if current_time - last_heartbeat > stale_seconds:
                    stale_nodes.append(node_id)
        
        return stale_nodes
    
    async def cleanup_stale_nodes(self, stale_seconds: float = 180.0):
        """清理超时的节点连接"""
        stale_nodes = await self.get_stale_nodes(stale_seconds)

        for node_id in stale_nodes:
            logger.warning("节点 %s 心跳超时(%ds),关闭连接", node_id, stale_seconds)
            # Get connection reference before unregistering to avoid use-after-delete
            async with self._lock:
                ws = self._connections.pop(node_id, None)
                self._heartbeats.pop(node_id, None)
            if ws:
                try:
                    await ws.close()
                except Exception as e:
                    logger.error("关闭超时节点 %s 连接失败: %s", node_id, str(e))
    
    async def get_online_nodes(self) -> list:
        """获取所有在线节点ID"""
        async with self._lock:
            return list(self._connections.keys())
    
    async def is_online(self, node_id: str) -> bool:
        """检查节点是否在线"""
        async with self._lock:
            return node_id in self._connections
    
    async def get_connection_count(self) -> int:
        """获取在线连接数"""
        async with self._lock:
            return len(self._connections)


# 全局连接池实例
pool = ConnectionPool()
