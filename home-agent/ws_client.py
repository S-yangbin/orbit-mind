"""
WebSocket 客户端
连接 mars-sandbox 服务端,处理节点注册、心跳、命令接收和结果发送
"""

import asyncio
import json
import logging
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from shared.message_protocol import (
    RegisterMessage,
    RegisterAckMessage,
    HeartbeatMessage,
    HeartbeatAckMessage,
    CommandMessage,
    ResultMessage,
    ErrorMessage,
)

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket 客户端,连接 mars-sandbox"""

    def __init__(
        self,
        server_url: str,
        node_id: str,
        node_secret: str,
        heartbeat_interval: int = 60,
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 0,
    ):
        """
        Args:
            server_url: mars-sandbox WebSocket 地址 (如 ws://host:port)
            node_id: 节点标识
            node_secret: 节点密钥
            heartbeat_interval: 心跳间隔（秒）
            reconnect_delay: 初始重连延迟（秒）
            max_reconnect_attempts: 最大重连次数，0 表示无限重试
        """
        self.server_url = server_url.rstrip("/")
        self.node_id = node_id
        self.node_secret = node_secret
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._start_time = time.time()
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_attempt = 0
        
        # 命令处理器回调
        self._command_handler = None
    
    def set_command_handler(self, handler):
        """设置命令处理器回调函数"""
        self._command_handler = handler
    
    def _build_websocket_url(self) -> str:
        """构建 WebSocket 连接 URL"""
        # ws://host:port/ws/agent/{node_id}?secret={node_secret}
        base_path = f"/ws/agent/{self.node_id}"
        params = urlencode({"secret": self.node_secret})
        
        # 判断协议
        if self.server_url.startswith("wss://"):
            return f"wss://{self.server_url[6:]}{base_path}?{params}"
        elif self.server_url.startswith("ws://"):
            return f"ws://{self.server_url[5:]}{base_path}?{params}"
        else:
            return f"ws://{self.server_url}{base_path}?{params}"
    
    async def connect(self) -> bool:
        """
        建立 WebSocket 连接
        
        Returns:
            是否连接成功
        """
        url = self._build_websocket_url()
        
        try:
            logger.info("正在连接 mars-sandbox: %s", self.server_url)
            self.websocket = await websockets.connect(
                url,
                ping_interval=30,  # 每 30 秒发送 ping
                ping_timeout=10,   # ping 超时 10 秒
            )
            logger.info("WebSocket 连接成功")
            self._reconnect_attempt = 0
            return True
        except Exception as e:
            logger.error("WebSocket 连接失败: %s", str(e))
            return False
    
    async def register(self) -> bool:
        """
        发送节点注册消息
        
        Returns:
            是否注册成功
        """
        try:
            register_msg = RegisterMessage(
                node_id=self.node_id,
                hostname=socket.gethostname(),
                ip=self._get_local_ip(),
                platform=f"{platform.system()} {platform.release()}",
                version="1.0.0",
            )
            
            await self.websocket.send(register_msg.to_json())
            logger.info("已发送注册消息")
            
            # 等待注册确认
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            data = json.loads(response)
            
            if data.get("type") == "register_ack":
                ack = RegisterAckMessage.from_dict(data)
                if ack.status == "success":
                    logger.info("节点注册成功: %s", self.node_id)
                    return True
                else:
                    logger.error("节点注册失败: %s", ack.message)
                    return False
            else:
                logger.error("收到非预期的响应: %s", data.get("type"))
                return False
                
        except asyncio.TimeoutError:
            logger.error("注册超时")
            return False
        except Exception as e:
            logger.error("注册异常: %s", str(e))
            return False
    
    async def send_heartbeat(self):
        """发送心跳消息"""
        try:
            uptime = int(time.time() - self._start_time)
            heartbeat_msg = HeartbeatMessage(
                node_id=self.node_id,
                uptime_seconds=uptime,
            )
            
            await self.websocket.send(heartbeat_msg.to_json())
            logger.debug("心跳已发送: uptime=%ds", uptime)
            
        except Exception as e:
            logger.error("发送心跳失败: %s", str(e))
            raise
    
    async def send_result(self, result: ResultMessage):
        """
        发送命令执行结果
        
        Args:
            result: 执行结果消息
        """
        try:
            await self.websocket.send(result.to_json())
            logger.info(
                "结果已发送: request_id=%s, exit_code=%d",
                result.request_id, result.exit_code
            )
        except Exception as e:
            logger.error("发送结果失败: %s", str(e))
            raise
    
    async def send_error(self, error: ErrorMessage):
        """
        发送错误消息
        
        Args:
            error: 错误消息
        """
        try:
            await self.websocket.send(error.to_json())
            logger.warning("错误消息已发送: %s", error.error_code)
        except Exception as e:
            logger.error("发送错误消息失败: %s", str(e))
            raise
    
    async def start_heartbeat_loop(self):
        """启动心跳循环任务"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("心跳循环已启动: interval=%ds", self.heartbeat_interval)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running and self.websocket:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("心跳循环异常: %s", str(e))
                await asyncio.sleep(self.heartbeat_interval)
    
    async def listen(self):
        """
        监听来自服务端的消息
        这是主循环,会一直运行直到连接关闭
        """
        logger.info("开始监听消息...")
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "command":
                        await self._handle_command(data)
                    elif msg_type == "heartbeat_ack":
                        logger.debug("收到心跳确认")
                    elif msg_type == "error":
                        error = ErrorMessage.from_dict(data)
                        logger.error("收到服务端错误: %s - %s", error.error_code, error.message)
                    else:
                        logger.warning("收到未知消息类型: %s", msg_type)
                        
                except json.JSONDecodeError as e:
                    logger.error("消息 JSON 解析失败: %s", str(e))
                except Exception as e:
                    logger.error("处理消息异常: %s", str(e), exc_info=True)
                    
        except ConnectionClosed as e:
            logger.warning("WebSocket 连接关闭: code=%d, reason=%s", e.code, e.reason)
        except Exception as e:
            logger.error("监听消息异常: %s", str(e), exc_info=True)
    
    async def _handle_command(self, data: dict):
        """
        处理命令消息
        
        Args:
            data: 命令消息数据
        """
        try:
            cmd_msg = CommandMessage.from_dict(data)
            logger.info(
                "收到命令: request_id=%s, command=%s, timeout=%ds",
                cmd_msg.request_id, cmd_msg.command, cmd_msg.timeout
            )
            
            if self._command_handler:
                # 异步执行命令处理器
                result = await self._command_handler(cmd_msg)
                
                # 发送结果
                await self.send_result(result)
            else:
                logger.error("未设置命令处理器")
                error = ErrorMessage(
                    error_code="NO_HANDLER",
                    message="命令处理器未设置",
                    request_id=cmd_msg.request_id,
                )
                await self.send_error(error)
                
        except Exception as e:
            logger.error("处理命令异常: %s", str(e), exc_info=True)
            error = ErrorMessage(
                error_code="COMMAND_ERROR",
                message=str(e),
                request_id=data.get("request_id"),
            )
            await self.send_error(error)
    
    async def run_with_reconnect(self):
        """
        运行 WebSocket 客户端,支持自动重连
        这是主入口方法
        """
        self._running = True
        
        while self._running:
            try:
                # 连接
                if not await self.connect():
                    await self._wait_for_reconnect()
                    continue
                
                # 注册
                if not await self.register():
                    await self._wait_for_reconnect()
                    continue
                
                # 启动心跳
                await self.start_heartbeat_loop()
                
                # 监听消息 (阻塞直到连接关闭)
                await self.listen()
                
            except asyncio.CancelledError:
                logger.info("WebSocket 客户端被取消")
                break
            except Exception as e:
                logger.error("WebSocket 运行异常: %s", str(e), exc_info=True)
            
            # 清理
            self._cleanup()
            
            # 重连
            if self._running:
                await self._wait_for_reconnect()
        
        logger.info("WebSocket 客户端已退出")
    
    async def _wait_for_reconnect(self):
        """等待重连,使用指数退避"""
        if self.max_reconnect_attempts > 0 and self._reconnect_attempt >= self.max_reconnect_attempts:
            logger.error("达到最大重连次数 %d,停止重连", self.max_reconnect_attempts)
            self._running = False
            return
        
        delay = self.reconnect_delay * (2 ** self._reconnect_attempt)
        delay = min(delay, 60)  # 最大延迟 60 秒
        
        self._reconnect_attempt += 1
        logger.info(
            "将在 %d 秒后重连 (尝试 %d/%d)...",
            delay,
            self._reconnect_attempt,
            self.max_reconnect_attempts if self.max_reconnect_attempts > 0 else "∞"
        )
        
        await asyncio.sleep(delay)
    
    def _cleanup(self):
        """清理资源"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        if self.websocket:
            try:
                asyncio.get_event_loop().run_until_complete(self.websocket.close())
            except:
                pass
            self.websocket = None
    
    async def close(self):
        """关闭连接"""
        logger.info("正在关闭 WebSocket 客户端...")
        self._running = False
        self._cleanup()
    
    @staticmethod
    def _get_local_ip() -> str:
        """获取本机局域网 IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"
