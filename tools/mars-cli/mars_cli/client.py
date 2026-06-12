"""mars-sandbox HTTP API 客户端封装

支持所有 mars-sandbox 后端接口，包括节点管理、命令执行、留言板、
餐饮计划、页面管理、视频学习、云盘、标签、扫描等。

认证方式:
  1. API Key (X-API-Key header) — 适用于 nodes/pages/tags/commands
  2. Cookie Session (登录获取 mars_session cookie) — 适用于 board/meals/videos/drive
  当提供 username/password 时，自动在需要 cookie 认证的操作前登录。

配置获取优先级（从高到低）:
  1. 构造函数显式参数（对应命令行 --url / --api-key）
  2. 环境变量 MARS_SANDBOX_URL / MARS_SANDBOX_API_KEY / MARS_SANDBOX_USERNAME / MARS_SANDBOX_PASSWORD
  3. JSON 配置文件（自动查找或 --config 指定）
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# 配置文件自动查找路径（按优先级从高到低）
_CONFIG_SEARCH_PATHS = [
    Path("mars-cli.json"),
    Path.home() / ".config" / "mars-cli" / "config.json",
    Path.home() / ".mars-cli.json",
]


def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """从 JSON 配置文件加载配置

    配置文件格式示例:
        {
            "url": "http://<server-ip>:<port>",
            "api_key": "your-api-key",
            "username": "admin",
            "password": "your-password",
            "default_node": "home-server-01",
            "default_timeout": 30
        }
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

    for p in _CONFIG_SEARCH_PATHS:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"ERROR: 配置文件 {p} JSON 解析失败: {e}", file=sys.stderr)
                sys.exit(1)

    return {}


class _SafeSession:
    """包装 requests.Session，捕获网络异常并输出友好错误信息。"""

    def __init__(self, session: requests.Session, base_url: str):
        self._session = session
        self._base_url = base_url

    def _wrap(self, method_name: str):
        def method(*args, **kwargs):
            try:
                return getattr(self._session, method_name)(*args, **kwargs)
            except requests.ConnectionError:
                print(f"ERROR: 无法连接到 {self._base_url}，请检查服务地址和网络。", file=sys.stderr)
                sys.exit(1)
            except requests.Timeout:
                print(f"ERROR: 请求超时，服务器响应过慢。", file=sys.stderr)
                sys.exit(1)
            except requests.RequestException as e:
                print(f"ERROR: 请求失败: {e}", file=sys.stderr)
                sys.exit(1)
        return method

    def get(self, *a, **kw): return self._wrap("get")(*a, **kw)
    def post(self, *a, **kw): return self._wrap("post")(*a, **kw)
    def put(self, *a, **kw): return self._wrap("put")(*a, **kw)
    def delete(self, *a, **kw): return self._wrap("delete")(*a, **kw)
    def patch(self, *a, **kw): return self._wrap("patch")(*a, **kw)

    @property
    def headers(self): return self._session.headers

    @property
    def cookies(self): return self._session.cookies


class MarsClient:
    """mars-sandbox HTTP API 客户端，封装所有后端接口调用。

    认证说明:
      - API Key: 通过 X-API-Key header，适用于 nodes/pages/tags/commands
      - Cookie: 通过 /api/auth/login 登录获取 mars_session cookie，适用于 board/meals/videos/drive
      - 当提供 username+password 时，需要 cookie 的操作会自动触发登录
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        config_path: Optional[str] = None,
        timeout: int = 60,
    ):
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
        self.username = (
            username
            or os.environ.get("MARS_SANDBOX_USERNAME")
            or file_cfg.get("username", "")
        )
        self.password = (
            password
            or os.environ.get("MARS_SANDBOX_PASSWORD")
            or file_cfg.get("password", "")
        )
        self.timeout = timeout

        self.default_node: Optional[str] = file_cfg.get("default_node")
        self.default_timeout: int = file_cfg.get("default_timeout", 30)

        if not self.base_url:
            print(
                "ERROR: 未配置 mars-sandbox 服务地址。请通过以下任一方式配置:\n"
                "  1. 命令行: mars-cli --url http://... <command>\n"
                "  2. 环境变量: export MARS_SANDBOX_URL=http://<ip>:<port>\n"
                "  3. 配置文件: mars-cli.json → {\"url\": \"http://...\"}",
                file=sys.stderr,
            )
            sys.exit(1)

        if not self.api_key and not (self.username and self.password):
            print(
                "ERROR: 未配置认证信息。请配置 API Key 或 用户名密码:\n"
                "  API Key:  export MARS_SANDBOX_API_KEY=your-key\n"
                "  用户名密码: export MARS_SANDBOX_USERNAME=admin && export MARS_SANDBOX_PASSWORD=xxx\n"
                "  配置文件: mars-cli.json → {\"api_key\": \"...\"} 或 {\"username\": \"...\", \"password\": \"...\"}",
                file=sys.stderr,
            )
            sys.exit(1)

        raw_session = requests.Session()
        raw_session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": self.api_key or "",
        })
        self.session = _SafeSession(raw_session, self.base_url)
        self._logged_in = False

    # ─── 内部工具方法 ───────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, resp: requests.Response) -> Any:
        """统一处理 HTTP 响应，错误时打印可读信息并退出。"""
        if resp.status_code == 403:
            print("ERROR: 认证失败，API Key 无效或已过期。", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 401:
            print("ERROR: 未认证，请先登录或检查 API Key。", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 404:
            try:
                detail = resp.json().get("detail", "资源不存在")
            except Exception:
                detail = "资源不存在"
            print(f"ERROR: {detail}", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 504:
            print("ERROR: 命令执行超时。", file=sys.stderr)
            sys.exit(1)
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            print(f"ERROR: 请求失败 (HTTP {resp.status_code}): {detail}", file=sys.stderr)
            sys.exit(1)
        if resp.status_code == 204 or not resp.content:
            return {}
        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            return resp.json()
        return {"data": resp.text}

    def _ensure_auth(self):
        """确保已获取 cookie 认证（用于 board/meals/videos/drive 等接口）。
        如果配置了 username+password 且尚未登录，则自动调用 /api/auth/login。"""
        if self._logged_in:
            return
        if not self.username or not self.password:
            return
        resp = self.session.post(
            self._url("/api/auth/login"),
            json={"username": self.username, "password": self.password},
            timeout=15,
        )
        if resp.ok:
            data = resp.json()
            if data.get("success"):
                self._logged_in = True
                return
        print("ERROR: 登录失败，请检查用户名和密码。", file=sys.stderr)
        sys.exit(1)

    # ─── 健康检查 ────────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """GET /health — 检查 mars-sandbox 服务是否正常运行（无需认证）。"""
        try:
            resp = requests.get(self._url("/health"), timeout=10)
        except requests.ConnectionError:
            print(f"ERROR: 无法连接到 {self.base_url}，请检查服务地址和网络。", file=sys.stderr)
            sys.exit(1)
        except requests.RequestException as e:
            print(f"ERROR: 请求失败: {e}", file=sys.stderr)
            sys.exit(1)
        return self._handle_response(resp)

    # ─── 节点管理 ────────────────────────────────────────────────────────────

    def list_nodes(self, stale: int = 180) -> Dict[str, Any]:
        """GET /api/nodes — 获取所有节点及其在线状态。"""
        resp = self.session.get(self._url("/api/nodes"), params={"stale": stale}, timeout=15)
        return self._handle_response(resp)

    def delete_node(self, node_id: str) -> Dict[str, Any]:
        """DELETE /api/nodes/{node_id} — 删除指定节点。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/nodes/{node_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 命令执行 ────────────────────────────────────────────────────────────

    def execute_command(self, node_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """POST /api/commands — 在远程节点执行 shell 命令并等待结果。"""
        payload = {"node_id": node_id, "command": command, "timeout": timeout}
        resp = self.session.post(self._url("/api/commands"), json=payload, timeout=timeout + 15)
        return self._handle_response(resp)

    # ─── 页面管理 ────────────────────────────────────────────────────────────

    def list_pages(self, q: Optional[str] = None, tag: Optional[str] = None,
                   category: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """GET /api/pages — 查询页面列表，支持搜索、标签、分类过滤和分页。"""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if q: params["q"] = q
        if tag: params["tag"] = tag
        if category: params["category"] = category
        resp = self.session.get(self._url("/api/pages"), params=params, timeout=15)
        return self._handle_response(resp)

    def get_page(self, page_id: int) -> Dict[str, Any]:
        """GET /api/pages/{id} — 获取指定页面详情。"""
        resp = self.session.get(self._url(f"/api/pages/{page_id}"), timeout=15)
        return self._handle_response(resp)

    def update_page(self, page_id: int, title: Optional[str] = None,
                    description: Optional[str] = None, tags: Optional[List[str]] = None,
                    category: Optional[str] = None) -> Dict[str, Any]:
        """PUT /api/pages/{id} — 更新页面元数据。"""
        body: Dict[str, Any] = {}
        if title is not None: body["title"] = title
        if description is not None: body["description"] = description
        if tags is not None: body["tags"] = tags
        if category is not None: body["category"] = category
        resp = self.session.put(self._url(f"/api/pages/{page_id}"), json=body, timeout=15)
        return self._handle_response(resp)

    def delete_page(self, page_id: int) -> Dict[str, Any]:
        """DELETE /api/pages/{id} — 删除页面记录（不删除文件）。"""
        resp = self.session.delete(self._url(f"/api/pages/{page_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 标签管理 ────────────────────────────────────────────────────────────

    def list_tags(self) -> Any:
        """GET /api/tags — 获取所有标签列表。"""
        resp = self.session.get(self._url("/api/tags"), timeout=15)
        return self._handle_response(resp)

    def create_tag(self, name: str) -> Dict[str, Any]:
        """POST /api/tags — 创建新标签。"""
        resp = self.session.post(self._url("/api/tags"), json={"name": name}, timeout=15)
        return self._handle_response(resp)

    def update_tag(self, tag_id: int, name: str) -> Dict[str, Any]:
        """PUT /api/tags/{id} — 重命名标签。"""
        resp = self.session.put(self._url(f"/api/tags/{tag_id}"), json={"name": name}, timeout=15)
        return self._handle_response(resp)

    def delete_tag(self, tag_id: int) -> Dict[str, Any]:
        """DELETE /api/tags/{id} — 删除标签。"""
        resp = self.session.delete(self._url(f"/api/tags/{tag_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 留言板 ──────────────────────────────────────────────────────────────

    def board_list(self) -> Dict[str, Any]:
        """GET /api/board/messages — 获取所有留言（置顶优先）。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/board/messages"), timeout=15)
        return self._handle_response(resp)

    def board_create(self, content: str, author: str = "", color: str = "yellow",
                     expires_at: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/board/messages — 创建留言。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"content": content, "author": author, "color": color}
        if expires_at: body["expires_at"] = expires_at
        resp = self.session.post(self._url("/api/board/messages"), json=body, timeout=15)
        return self._handle_response(resp)

    def board_update(self, message_id: int, **kwargs) -> Dict[str, Any]:
        """PUT /api/board/messages/{id} — 更新留言。"""
        self._ensure_auth()
        body = {k: v for k, v in kwargs.items() if v is not None}
        resp = self.session.put(self._url(f"/api/board/messages/{message_id}"), json=body, timeout=15)
        return self._handle_response(resp)

    def board_delete(self, message_id: int) -> Dict[str, Any]:
        """DELETE /api/board/messages/{id} — 删除留言。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/board/messages/{message_id}"), timeout=15)
        return self._handle_response(resp)

    def board_toggle_pin(self, message_id: int) -> Dict[str, Any]:
        """PUT /api/board/messages/{id}/pin — 切换置顶状态。"""
        self._ensure_auth()
        resp = self.session.put(self._url(f"/api/board/messages/{message_id}/pin"), timeout=15)
        return self._handle_response(resp)

    # ─── 餐饮：家庭成员 ──────────────────────────────────────────────────────

    def meals_list_members(self) -> Dict[str, Any]:
        """GET /api/meals/members — 获取所有家庭成员。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/meals/members"), timeout=15)
        return self._handle_response(resp)

    def meals_create_member(self, name: str, avatar: str = "🧑", board_color: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/meals/members — 添加家庭成员。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"name": name, "avatar": avatar}
        if board_color: body["board_color"] = board_color
        resp = self.session.post(self._url("/api/meals/members"), json=body, timeout=15)
        return self._handle_response(resp)

    def meals_update_member(self, member_id: int, **kwargs) -> Dict[str, Any]:
        """PUT /api/meals/members/{id} — 更新家庭成员。"""
        self._ensure_auth()
        body = {k: v for k, v in kwargs.items() if v is not None}
        resp = self.session.put(self._url(f"/api/meals/members/{member_id}"), json=body, timeout=15)
        return self._handle_response(resp)

    def meals_delete_member(self, member_id: int) -> Dict[str, Any]:
        """DELETE /api/meals/members/{id} — 删除家庭成员。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/meals/members/{member_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 餐饮：菜品 ──────────────────────────────────────────────────────────

    def meals_list_dishes(self, page: int = 1, page_size: int = 20,
                          keyword: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """GET /api/meals/dishes — 查询菜品列表。"""
        self._ensure_auth()
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if keyword: params["keyword"] = keyword
        if category: params["category"] = category
        resp = self.session.get(self._url("/api/meals/dishes"), params=params, timeout=15)
        return self._handle_response(resp)

    def meals_get_dish(self, dish_id: int) -> Dict[str, Any]:
        """GET /api/meals/dishes/{id} — 获取单个菜品详情。"""
        self._ensure_auth()
        resp = self.session.get(self._url(f"/api/meals/dishes/{dish_id}"), timeout=15)
        return self._handle_response(resp)

    def meals_create_dish(self, name: str, category: str = "荤菜",
                          ingredients: Optional[List[str]] = None, recipe: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/meals/dishes — 创建菜品。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"name": name, "category": category}
        if ingredients: body["ingredients"] = ingredients
        if recipe: body["recipe"] = recipe
        resp = self.session.post(self._url("/api/meals/dishes"), json=body, timeout=15)
        return self._handle_response(resp)

    def meals_delete_dish(self, dish_id: int) -> Dict[str, Any]:
        """DELETE /api/meals/dishes/{id}（注意：后端未实现此接口，会返回 404）。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/meals/dishes/{dish_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 餐饮：菜单计划 ──────────────────────────────────────────────────────

    def meals_current_plan(self) -> Dict[str, Any]:
        """GET /api/meals/plan/current — 获取当前菜单（前4周+后4周）。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/meals/plan/current"), timeout=15)
        return self._handle_response(resp)

    def meals_generate_plan(self, week_start_date: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/meals/plan/generate — AI 生成月度周末菜单。"""
        self._ensure_auth()
        body: Dict[str, Any] = {}
        if week_start_date: body["week_start_date"] = week_start_date
        resp = self.session.post(self._url("/api/meals/plan/generate"), json=body, timeout=120)
        return self._handle_response(resp)

    def meals_confirm_plan(self) -> Dict[str, Any]:
        """POST /api/meals/plan/confirm — 确认本周菜单。"""
        self._ensure_auth()
        resp = self.session.post(self._url("/api/meals/plan/confirm"), timeout=15)
        return self._handle_response(resp)

    def meals_add_plan_item(self, date: str, meal_type: str, dish_id: int) -> Dict[str, Any]:
        """POST /api/meals/plan/items — 手动添加菜品到本周菜单。"""
        self._ensure_auth()
        body = {"date": date, "meal_type": meal_type, "dish_id": dish_id}
        resp = self.session.post(self._url("/api/meals/plan/items"), json=body, timeout=15)
        return self._handle_response(resp)

    def meals_replace_plan_item(self, item_id: int, dish_id: int) -> Dict[str, Any]:
        """PUT /api/meals/plan/items/{id} — 替换菜单中的菜品。"""
        self._ensure_auth()
        resp = self.session.put(self._url(f"/api/meals/plan/items/{item_id}"),
                                json={"dish_id": dish_id}, timeout=15)
        return self._handle_response(resp)

    def meals_remove_plan_item(self, item_id: int) -> Dict[str, Any]:
        """DELETE /api/meals/plan/items/{id} — 移除菜单项。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/meals/plan/items/{item_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 餐饮：用餐记录 ──────────────────────────────────────────────────────

    def meals_list_logs(self, page: int = 1, page_size: int = 20,
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """GET /api/meals/history — 查询用餐记录列表。"""
        self._ensure_auth()
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if start_date: params["start_date"] = start_date
        if end_date: params["end_date"] = end_date
        resp = self.session.get(self._url("/api/meals/history"), params=params, timeout=15)
        return self._handle_response(resp)

    def meals_history_stats(self, days: int = 14) -> Dict[str, Any]:
        """GET /api/meals/history/stats — 获取用餐统计。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/meals/history/stats"), params={"days": days}, timeout=15)
        return self._handle_response(resp)

    def meals_create_log(self, date: str, meal_type: str, dishes: List[Dict],
                         image_path: str = "", rating: Optional[int] = None,
                         note: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/meals/history — 创建用餐记录。"""
        self._ensure_auth()
        body: Dict[str, Any] = {
            "date": date, "meal_type": meal_type,
            "dishes": dishes, "image_path": image_path,
        }
        if rating is not None: body["rating"] = rating
        if note: body["note"] = note
        resp = self.session.post(self._url("/api/meals/history"), json=body, timeout=15)
        return self._handle_response(resp)

    # ─── 餐饮：偏好 ──────────────────────────────────────────────────────────

    def meals_preferences(self) -> Any:
        """GET /api/meals/preferences — 获取所有成员的菜品偏好。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/meals/preferences"), timeout=15)
        return self._handle_response(resp)

    def meals_dish_liked_by(self, dish_id: int) -> Dict[str, Any]:
        """GET /api/meals/preferences/dish/{id} — 查看谁喜欢某道菜。"""
        self._ensure_auth()
        resp = self.session.get(self._url(f"/api/meals/preferences/dish/{dish_id}"), timeout=15)
        return self._handle_response(resp)

    # ─── 视频管理 ────────────────────────────────────────────────────────────

    def videos_list(self, q: Optional[str] = None, status: Optional[str] = None,
                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """GET /api/videos — 查询视频列表。"""
        self._ensure_auth()
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if q: params["q"] = q
        if status: params["status"] = status
        resp = self.session.get(self._url("/api/videos"), params=params, timeout=15)
        return self._handle_response(resp)

    def videos_get(self, video_id: int) -> Dict[str, Any]:
        """GET /api/videos/{id} — 获取视频详情（含分段、笔记、进度）。"""
        self._ensure_auth()
        resp = self.session.get(self._url(f"/api/videos/{video_id}"), timeout=15)
        return self._handle_response(resp)

    def videos_process(self, video_id: int) -> Dict[str, Any]:
        """POST /api/videos/{id}/process — 触发视频处理（音频提取+ASR+分段分析）。"""
        self._ensure_auth()
        resp = self.session.post(self._url(f"/api/videos/{video_id}/process"), timeout=15)
        return self._handle_response(resp)

    def videos_add_segment(self, video_id: int, title: str, start_time: int, end_time: int,
                           segment_type: str = "qa", transcription: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/videos/{id}/segments — 手动添加视频分段。"""
        self._ensure_auth()
        body: Dict[str, Any] = {
            "title": title, "start_time": start_time, "end_time": end_time, "segment_type": segment_type,
        }
        if transcription: body["transcription"] = transcription
        resp = self.session.post(self._url(f"/api/videos/{video_id}/segments"), json=body, timeout=15)
        return self._handle_response(resp)

    def videos_update_segment(self, segment_id: int, **kwargs) -> Dict[str, Any]:
        """PUT /api/videos/segments/{id} — 更新分段信息。"""
        self._ensure_auth()
        body = {k: v for k, v in kwargs.items() if v is not None}
        resp = self.session.put(self._url(f"/api/videos/segments/{segment_id}"), json=body, timeout=15)
        return self._handle_response(resp)

    def videos_delete_segment(self, segment_id: int) -> Dict[str, Any]:
        """DELETE /api/videos/segments/{id} — 删除分段。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/videos/segments/{segment_id}"), timeout=15)
        return self._handle_response(resp)

    def videos_add_note(self, segment_id: int, content: str) -> Dict[str, Any]:
        """POST /api/videos/segments/{id}/notes — 添加/更新分段笔记。"""
        self._ensure_auth()
        resp = self.session.post(self._url(f"/api/videos/segments/{segment_id}/notes"),
                                 json={"content": content}, timeout=15)
        return self._handle_response(resp)

    def videos_update_progress(self, segment_id: int, mastered: Optional[int] = None,
                               loop_count: Optional[int] = None) -> Dict[str, Any]:
        """PUT /api/videos/segments/{id}/progress — 更新学习进度。"""
        self._ensure_auth()
        body: Dict[str, Any] = {}
        if mastered is not None: body["mastered"] = mastered
        if loop_count is not None: body["loop_count"] = loop_count
        resp = self.session.put(self._url(f"/api/videos/segments/{segment_id}/progress"),
                                json=body, timeout=15)
        return self._handle_response(resp)

    # ─── 云盘 ────────────────────────────────────────────────────────────────

    def drive_list(self, parent_id: Optional[int] = None, q: Optional[str] = None,
                   page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """GET /api/drive/files — 列出云盘文件。"""
        self._ensure_auth()
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if parent_id is not None: params["parent_id"] = parent_id
        if q: params["q"] = q
        resp = self.session.get(self._url("/api/drive/files"), params=params, timeout=15)
        return self._handle_response(resp)

    def drive_list_folders(self) -> Dict[str, Any]:
        """GET /api/drive/folders — 列出所有文件夹（平铺列表）。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/drive/folders"), timeout=15)
        return self._handle_response(resp)

    def drive_create_folder(self, filename: str, parent_id: Optional[int] = None) -> Dict[str, Any]:
        """POST /api/drive/folders — 创建文件夹。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"filename": filename}
        if parent_id is not None: body["parent_id"] = parent_id
        resp = self.session.post(self._url("/api/drive/folders"), json=body, timeout=15)
        return self._handle_response(resp)

    def drive_delete_file(self, file_id: int) -> Dict[str, Any]:
        """DELETE /api/drive/files/{id} — 删除文件。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/drive/files/{file_id}"), timeout=15)
        return self._handle_response(resp)

    def drive_delete_folder(self, folder_id: int) -> Dict[str, Any]:
        """DELETE /api/drive/folders/{id} — 删除文件夹及其内容。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/drive/folders/{folder_id}"), timeout=15)
        return self._handle_response(resp)

    def drive_move(self, file_id: int, target_parent_id: Optional[int] = None) -> Dict[str, Any]:
        """POST /api/drive/files/{id}/move — 移动文件或文件夹。"""
        self._ensure_auth()
        resp = self.session.post(self._url(f"/api/drive/files/{file_id}/move"),
                                 json={"target_parent_id": target_parent_id}, timeout=30)
        return self._handle_response(resp)

    def drive_copy(self, file_id: int, target_parent_id: Optional[int] = None) -> Dict[str, Any]:
        """POST /api/drive/files/{id}/copy — 复制文件。"""
        self._ensure_auth()
        resp = self.session.post(self._url(f"/api/drive/files/{file_id}/copy"),
                                 json={"target_parent_id": target_parent_id}, timeout=30)
        return self._handle_response(resp)

    def drive_signed_url(self, oss_key: str, expires_in: int = 3600) -> Dict[str, Any]:
        """GET /api/drive/signed-url — 生成签名下载 URL。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/drive/signed-url"),
                                params={"oss_key": oss_key, "expires_in": expires_in}, timeout=15)
        return self._handle_response(resp)

    def drive_preview_text(self, oss_key: str, page: int = 1, page_size: int = 200) -> Dict[str, Any]:
        """GET /api/drive/preview-text — 预览文本文件内容。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/drive/preview-text"),
                                params={"oss_key": oss_key, "page": page, "page_size": page_size}, timeout=30)
        return self._handle_response(resp)

    # ─── 扫描 ────────────────────────────────────────────────────────────────

    def scan_trigger(self) -> Dict[str, Any]:
        """POST /api/scan — 手动触发目录扫描。"""
        resp = self.session.post(self._url("/api/scan"), timeout=15)
        return self._handle_response(resp)

    def scan_status(self) -> Dict[str, Any]:
        """GET /api/scan/status — 获取扫描状态。"""
        resp = self.session.get(self._url("/api/scan/status"), timeout=15)
        return self._handle_response(resp)

    # ─── Dashboard ─────────────────────────────────────────────────────────

    def refresh_wallpaper(self) -> Dict[str, Any]:
        """POST /api/dashboard/refresh-wallpaper — 刷新看板壁纸并推送给所有已连接 Dashboard。"""
        self._ensure_auth()
        resp = self.session.post(self._url("/api/dashboard/refresh-wallpaper"), timeout=30)
        return self._handle_response(resp)

    def generate_wallpaper(self, prompt: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/dashboard/generate-wallpaper — AI 生成壁纸并推送给所有已连接 Dashboard。"""
        self._ensure_auth()
        body: Dict[str, Any] = {}
        if prompt:
            body["prompt"] = prompt
        # AI 图片生成耗时较长，超时设置 180 秒
        resp = self.session.post(self._url("/api/dashboard/generate-wallpaper"), json=body, timeout=180)
        return self._handle_response(resp)

    def list_wallpapers(self) -> Dict[str, Any]:
        """GET /api/dashboard/wallpapers — 列出所有已生成的 AI 壁纸。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/dashboard/wallpapers"), timeout=15)
        return self._handle_response(resp)

    def set_wallpaper(self, filename: str) -> Dict[str, Any]:
        """POST /api/dashboard/set-wallpaper — 设置指定壁纸并推送给所有已连接 Dashboard。"""
        self._ensure_auth()
        resp = self.session.post(
            self._url("/api/dashboard/set-wallpaper"),
            json={"filename": filename},
            timeout=15,
        )
        return self._handle_response(resp)

    # ─── 学习计划 ────────────────────────────────────────────────────────────

    def schedule_list_types(self) -> Dict[str, Any]:
        """GET /api/schedule/activity-types — 获取所有活动类型。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/schedule/activity-types"), timeout=15)
        return self._handle_response(resp)

    def schedule_create_type(self, name: str, icon: str = "📋", color: str = "#6b7280",
                             category: str = "custom") -> Dict[str, Any]:
        """POST /api/schedule/activity-types — 创建自定义活动类型。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"name": name, "icon": icon, "color": color, "category": category}
        resp = self.session.post(self._url("/api/schedule/activity-types"), json=body, timeout=15)
        return self._handle_response(resp)

    def schedule_update_type(self, type_id: int, **kwargs) -> Dict[str, Any]:
        """PUT /api/schedule/activity-types/{id} — 更新活动类型。"""
        self._ensure_auth()
        body = {k: v for k, v in kwargs.items() if v is not None}
        resp = self.session.put(self._url(f"/api/schedule/activity-types/{type_id}"), json=body, timeout=15)
        return self._handle_response(resp)

    def schedule_delete_type(self, type_id: int) -> Dict[str, Any]:
        """DELETE /api/schedule/activity-types/{id} — 删除自定义活动类型。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/schedule/activity-types/{type_id}"), timeout=15)
        return self._handle_response(resp)

    def schedule_get_template(self) -> Dict[str, Any]:
        """GET /api/schedule/template — 获取当前激活的周模板。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/schedule/template"), timeout=15)
        return self._handle_response(resp)

    def schedule_set_template(self, name: str, days: Dict[str, List[int]]) -> Dict[str, Any]:
        """POST /api/schedule/template — 创建/更新周模板。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"name": name, "days": days}
        resp = self.session.post(self._url("/api/schedule/template"), json=body, timeout=15)
        return self._handle_response(resp)

    def schedule_today(self) -> Dict[str, Any]:
        """GET /api/schedule/daily?date=today — 获取今天的计划。"""
        self._ensure_auth()
        from datetime import date
        today = date.today().isoformat()
        resp = self.session.get(self._url("/api/schedule/daily"), params={"date": today}, timeout=15)
        return self._handle_response(resp)

    def schedule_daily(self, date: str) -> Dict[str, Any]:
        """GET /api/schedule/daily?date=YYYY-MM-DD — 获取某天的计划。"""
        self._ensure_auth()
        resp = self.session.get(self._url("/api/schedule/daily"), params={"date": date}, timeout=15)
        return self._handle_response(resp)

    def schedule_add(self, date: str, activity_type_id: int) -> Dict[str, Any]:
        """POST /api/schedule/daily — 手动添加活动到某天。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"date": date, "activity_type_id": activity_type_id}
        resp = self.session.post(self._url("/api/schedule/daily"), json=body, timeout=15)
        return self._handle_response(resp)

    def schedule_complete(self, item_id: int, note: Optional[str] = None) -> Dict[str, Any]:
        """PUT /api/schedule/daily/{id} — 标记完成，可选附带完成备注。"""
        self._ensure_auth()
        body: Dict[str, Any] = {"completed": 1}
        if note:
            body["completion_note"] = note
        resp = self.session.put(self._url(f"/api/schedule/daily/{item_id}"), json=body, timeout=15)
        return self._handle_response(resp)

    def schedule_uncomplete(self, item_id: int) -> Dict[str, Any]:
        """PUT /api/schedule/daily/{id} — 取消完成标记。"""
        self._ensure_auth()
        resp = self.session.put(self._url(f"/api/schedule/daily/{item_id}"),
                                json={"completed": 0}, timeout=15)
        return self._handle_response(resp)

    def schedule_remove(self, item_id: int) -> Dict[str, Any]:
        """DELETE /api/schedule/daily/{id} — 删除某天的活动。"""
        self._ensure_auth()
        resp = self.session.delete(self._url(f"/api/schedule/daily/{item_id}"), timeout=15)
        return self._handle_response(resp)
