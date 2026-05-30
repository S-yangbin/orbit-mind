"""mars-sandbox HTTP API 客户端封装"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# 配置文件自动查找路径（按优先级从高到低）
_CONFIG_SEARCH_PATHS = [
    Path("mars-cli.json"),                          # 当前目录
    Path.home() / ".config" / "mars-cli" / "config.json",  # XDG 标准
    Path.home() / ".mars-cli.json",                 # home 目录简写
]


def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """从 JSON 配置文件加载配置

    查找顺序:
      1. config_path 参数指定的路径（如不存在则报错）
      2. 当前目录下的 mars-cli.json
      3. ~/.config/mars-cli/config.json
      4. ~/.mars-cli.json

    配置文件格式示例:
        {
            "url": "http://<your-server-ip>:<port>",
            "api_key": "your-secret-key",
            "default_node": "my-node",
            "default_timeout": 30
        }

    字段说明:
        url             - mars-sandbox 服务端地址（必填）
        api_key         - API 认证密钥（必填）
        default_node    - exec 命令默认目标节点 ID（可选）
        default_timeout - exec 命令默认超时秒数（可选，默认 30）

    Args:
        config_path: 显式指定的配置文件路径，为 None 时自动查找

    Returns:
        解析后的配置字典，未找到配置文件时返回空字典
    """
    if config_path:
        p = Path(config_path)
        if not p.exists():
            print(f"ERROR: 指定的配置文件不存在: {config_path}", file=sys.stderr)
            sys.exit(1)
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: 配置文件 JSON 解析失败: {e}", file=sys.stderr)
            sys.exit(1)

    # 自动查找
    for p in _CONFIG_SEARCH_PATHS:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"ERROR: 配置文件 {p} JSON 解析失败: {e}", file=sys.stderr)
                sys.exit(1)

    return {}


class MarsClient:
    """mars-sandbox 服务端 HTTP API 客户端

    所有与 mars-sandbox 后端的通信都通过此类完成。

    配置获取优先级（从高到低）:
      1. 构造函数显式参数（对应命令行 --url / --api-key）
      2. 环境变量 MARS_SANDBOX_URL / MARS_SANDBOX_API_KEY
      3. JSON 配置文件（自动查找或 --config 指定）

    配置文件路径（自动查找，按优先级）:
      - 当前目录: mars-cli.json
      - XDG 标准: ~/.config/mars-cli/config.json
      - Home 目录: ~/.mars-cli.json
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
        timeout: int = 60,
    ):
        # 加载配置文件作为兜底
        file_cfg = load_config_file(config_path)

        self.base_url = (
            base_url
            or os.environ.get("MARS_SANDBOX_URL")
            or file_cfg.get("url", "")
        ).rstrip("/")
        self.api_key = (
            api_key
            or os.environ.get("MARS_SANDBOX_API_KEY")
            or file_cfg.get("api_key", "")
        )
        self.timeout = timeout

        # 将配置文件中的可选默认值暴露给 CLI 使用
        self.default_node: Optional[str] = file_cfg.get("default_node")
        self.default_timeout: int = file_cfg.get("default_timeout", 30)
        self.config_source = (
            "cli-args" if base_url or api_key
            else "env" if os.environ.get("MARS_SANDBOX_URL")
            else "config-file" if file_cfg
            else "none"
        )

        if not self.base_url:
            print(
                "ERROR: 未配置 mars-sandbox 服务地址。请通过以下任一方式配置:\n"
                "  1. 命令行: mars-cli --url http://... <command>\n"
                "  2. 环境变量: export MARS_SANDBOX_URL=http://<your-server-ip>:<port>\n"
                "  3. 配置文件: 创建 mars-cli.json 写入 {\"url\": \"http://...\", \"api_key\": \"...\"}\n"
                "     支持路径: ./mars-cli.json, ~/.config/mars-cli/config.json, ~/.mars-cli.json",
                file=sys.stderr,
            )
            sys.exit(1)

        if not self.api_key:
            print(
                "ERROR: 未配置 API 密钥。请通过以下任一方式配置:\n"
                "  1. 命令行: mars-cli --api-key xxx <command>\n"
                "  2. 环境变量: export MARS_SANDBOX_API_KEY=your-secret-key\n"
                "  3. 配置文件: 创建 mars-cli.json 写入 {\"api_key\": \"your-secret-key\"}",
                file=sys.stderr,
            )
            sys.exit(1)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            }
        )

    def _url(self, path: str) -> str:
        """拼接完整 URL"""
        return f"{self.base_url}{path}"

    def _handle_response(self, resp: requests.Response) -> Dict[str, Any]:
        """统一处理响应，抛出可读错误"""
        if resp.status_code == 403:
            print("ERROR: 认证失败，API Key 无效或已过期。", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 404:
            detail = resp.json().get("detail", "资源不存在") if resp.headers.get("content-type", "").startswith("application/json") else "资源不存在"
            print(f"ERROR: {detail}", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 504:
            print("ERROR: 命令执行超时，节点响应时间过长。", file=sys.stderr)
            sys.exit(1)
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            print(f"ERROR: 请求失败 (HTTP {resp.status_code}): {detail}", file=sys.stderr)
            sys.exit(1)
        return resp.json()

    # ─── 节点相关 ──────────────────────────────────────────────────────────

    def list_nodes(self, stale: int = 180) -> Dict[str, Any]:
        """获取所有已注册节点列表及其在线状态

        Args:
            stale: 超过该秒数未心跳则判定为离线，默认 180 秒，最小 30 秒

        Returns:
            包含 total, online, offline, nodes 字段的字典
        """
        resp = self.session.get(self._url("/api/nodes"), params={"stale": stale}, timeout=15)
        return self._handle_response(resp)

    def delete_node(self, node_id: str) -> Dict[str, Any]:
        """删除指定节点记录（不删除远程节点上的 agent）

        Args:
            node_id: 目标节点 ID
        """
        resp = self.session.delete(self._url(f"/api/nodes/{node_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 命令执行 ──────────────────────────────────────────────────────────

    def execute_command(
        self,
        node_id: str,
        command: str,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """在指定远程节点上执行 shell 命令

        通过 WebSocket 将命令转发给 home-agent，同步等待执行结果返回。
        节点会进行安全校验（命令黑白名单），危险命令会被拒绝。

        Args:
            node_id: 目标节点 ID，必须在线
            command: 要在远程节点执行的 shell 命令字符串
            timeout: 命令执行超时时间（秒），默认 30，最长建议不超过 300

        Returns:
            包含以下字段的字典:
            - request_id: 本次请求唯一标识
            - exit_code: 命令退出码，0 表示成功
            - stdout: 标准输出内容
            - stderr: 标准错误内容
            - duration_ms: 命令执行耗时（毫秒）
        """
        payload = {
            "node_id": node_id,
            "command": command,
            "timeout": timeout,
        }
        # HTTP 超时需要比命令超时更长，留出网络传输缓冲
        http_timeout = timeout + 15
        resp = self.session.post(
            self._url("/api/commands"),
            json=payload,
            timeout=http_timeout,
        )
        return self._handle_response(resp)

    # ─── 健康检查 ──────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """检查 mars-sandbox 服务是否正常运行

        无需 API Key 即可调用。

        Returns:
            服务健康状态信息
        """
        # 健康检查不需要 API Key
        resp = requests.get(self._url("/health"), timeout=10)
        return self._handle_response(resp)

    # ─── 页面管理（Dashboard 功能）─────────────────────────────────────────

    def list_pages(
        self,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """查询沙箱中托管的页面列表（支持搜索、标签过滤、分页）

        Args:
            q: 搜索关键词，匹配页面标题或描述
            tag: 按标签名称过滤
            category: 按分类过滤
            page: 页码，从 1 开始
            page_size: 每页数量，默认 20，最大 100
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if q:
            params["q"] = q
        if tag:
            params["tag"] = tag
        if category:
            params["category"] = category
        resp = self.session.get(self._url("/api/pages"), params=params, timeout=15)
        return self._handle_response(resp)

    def get_page(self, page_id: int) -> Dict[str, Any]:
        """获取指定页面详情

        Args:
            page_id: 页面数据库 ID
        """
        resp = self.session.get(self._url(f"/api/pages/{page_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 标签管理 ──────────────────────────────────────────────────────────

    def list_tags(self) -> list:
        """获取所有标签列表，每个标签附带关联页面数量"""
        resp = self.session.get(self._url("/api/tags"), timeout=15)
        return self._handle_response(resp)
