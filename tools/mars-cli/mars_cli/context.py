"""全局上下文：保存 MarsClient 实例，供所有子命令模块使用"""

from .client import MarsClient

_client: MarsClient = None  # type: ignore


def set_client(client: MarsClient):
    global _client
    _client = client


def get_client() -> MarsClient:
    if _client is None:
        raise RuntimeError("MarsClient 未初始化")
    return _client
