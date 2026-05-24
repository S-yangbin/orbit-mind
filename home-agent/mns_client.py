"""
MNS 客户端封装
封装阿里云轻量消息队列（原 MNS）的收发操作
"""

import json
import logging
from typing import Optional, Tuple

from mns.account import Account
from mns.mns_exception import MNSExceptionBase
from mns.queue import Message

logger = logging.getLogger(__name__)


class MNSClient:
    """MNS 队列客户端"""
    
    def __init__(
        self,
        endpoint: str,
        access_key_id: str,
        access_key_secret: str,
        queue_name: str,
    ):
        """
        初始化 MNS 客户端
        
        Args:
            endpoint: MNS 服务端点
            access_key_id: 阿里云 AK
            access_key_secret: 阿里云 SK
            queue_name: 队列名称
        """
        self.queue_name = queue_name
        self.account = Account(endpoint, access_key_id, access_key_secret, "")
        self.queue = self.account.get_queue(queue_name)
        # 不使用 Base64 编码，直接传输 JSON 字符串
        self.queue.set_encoding(False)
        
        logger.info("MNS 客户端初始化完成: endpoint=%s, queue=%s", endpoint, queue_name)
    
    def send_message(self, message_body: str) -> str:
        """
        发送消息到队列
        
        Args:
            message_body: 消息体（JSON 字符串）
            
        Returns:
            message_id
        """
        try:
            msg = Message(message_body)
            result = self.queue.send_message(msg)
            logger.debug(
                "消息发送成功: message_id=%s", result.message_id
            )
            return result.message_id
        except MNSExceptionBase as e:
            logger.error("消息发送失败: %s", str(e))
            raise
    
    def receive_message(self, wait_seconds: int = 30) -> Optional[Tuple[str, str]]:
        """
        长轮询接收消息
        
        Args:
            wait_seconds: 长轮询等待时间（秒）
            
        Returns:
            (receipt_handle, message_body) 或 None（队列空时）
        """
        try:
            recv_msg = self.queue.receive_message_with_str_body(wait_seconds)
            logger.debug(
                "收到消息: message_id=%s, receipt_handle=%s",
                recv_msg.message_id, recv_msg.receipt_handle,
            )
            return recv_msg.receipt_handle, recv_msg.message_body
        except MNSExceptionBase as e:
            if hasattr(e, "type") and e.type == "MessageNotExist":
                return None
            logger.error("接收消息异常: %s", str(e))
            raise
    
    def delete_message(self, receipt_handle: str) -> None:
        """删除消息"""
        try:
            self.queue.delete_message(receipt_handle)
            logger.debug("消息删除成功: receipt_handle=%s", receipt_handle)
        except MNSExceptionBase as e:
            logger.error("消息删除失败: %s", str(e))
            raise
    
    def resend_and_delete(
        self, receipt_handle: str, message_body: str
    ) -> str:
        """
        将消息重新发回队列后删除原消息
        用于处理非本端消息（单队列模式）
        
        Args:
            receipt_handle: 原消息的 receipt_handle
            message_body: 消息体
            
        Returns:
            新消息的 message_id
        """
        # 先发送新消息
        new_msg_id = self.send_message(message_body)
        # 再删除原消息
        self.delete_message(receipt_handle)
        logger.debug(
            "消息 re-send 完成: new_message_id=%s", new_msg_id
        )
        return new_msg_id
