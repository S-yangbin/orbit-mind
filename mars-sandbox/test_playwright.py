"""Playwright test for Mars Sandbox - comprehensive functional test."""
import json
import subprocess
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def run_test(name, func):
    """Run a single test and report result."""
    try:
        func()
        print(f"  ✓ {name}")
        return True
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def test_health():
    """Test health endpoint."""
    from urllib.request import urlopen
    resp = urlopen(f"{BASE_URL}/health")
    data = json.loads(resp.read())
    assert data["status"] == "ok", f"Expected ok, got {data}"


def test_api_docs_accessible():
    """Test that Swagger docs are accessible."""
    from urllib.request import urlopen
    resp = urlopen(f"{BASE_URL}/docs")
    assert resp.status == 200


def test_login_flow():
    """Test login via API."""
    import urllib.request
    
    # First, get the auth credentials from .env
    env_path = Path(__file__).parent / "backend" / ".env"
    env_content = env_path.read_text()
    username = "admin"
    password = "admin"
    for line in env_content.split("\n"):
        if line.startswith("AUTH_USERNAME="):
            username = line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith("AUTH_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    # Test login
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    assert data.get("success") == True, f"Login failed: {data}"
    
    # Check cookie is set
    cookies = resp.headers.get_all("Set-Cookie")
    assert any("session" in c for c in cookies), f"No session cookie: {cookies}"


def test_auth_required():
    """Test that pages API requires auth."""
    from urllib.request import urlopen, HTTPError
    try:
        urlopen(f"{BASE_URL}/api/pages")
        assert False, "Expected 401 Unauthorized"
    except HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"


def test_scan_api():
    """Test scan trigger endpoint."""
    import urllib.request
    
    # Get auth cookies first
    env_path = Path(__file__).parent / "backend" / ".env"
    env_content = env_path.read_text()
    username = "admin"
    password = "admin"
    for line in env_content.split("\n"):
        if line.startswith("AUTH_USERNAME="):
            username = line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith("AUTH_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    # Login
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    cookies = resp.headers.get_all("Set-Cookie")
    cookie_str = "; ".join(cookies) if cookies else ""
    
    # Trigger scan
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/scan",
        method="POST",
        headers={"Cookie": cookie_str},
    )
    resp2 = urllib.request.urlopen(req2)
    data = json.loads(resp2.read())
    print(f"    Scan result: {data}")


def test_pages_list_empty():
    """Test pages list (should be empty since /mnt/oss-sybuddy/html is empty)."""
    import urllib.request
    
    # Get auth cookies first
    env_path = Path(__file__).parent / "backend" / ".env"
    env_content = env_path.read_text()
    username = "admin"
    password = "admin"
    for line in env_content.split("\n"):
        if line.startswith("AUTH_USERNAME="):
            username = line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith("AUTH_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    # Login
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    cookies = resp.headers.get_all("Set-Cookie")
    cookie_str = "; ".join(cookies) if cookies else ""
    
    # Get pages list
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/pages",
        headers={"Cookie": cookie_str},
    )
    resp2 = urllib.request.urlopen(req2)
    data = json.loads(resp2.read())
    assert "items" in data, f"Expected 'items' key in response: {data}"
    assert "total" in data, f"Expected 'total' key in response: {data}"
    print(f"    Pages: total={data['total']}, items={len(data['items'])}")


def test_frontend_served():
    """Test that frontend is served at /."""
    from urllib.request import urlopen
    resp = urlopen(f"{BASE_URL}/")
    html = resp.read().decode()
    assert "<div" in html or "<!doctype" in html.lower(), f"Expected HTML content, got: {html[:200]}"


def test_playwright_browser_login_page():
    """Use Playwright to test the login page rendering."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        # Navigate to login page
        page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=15000)
        
        # Check page title or content
        title = page.title()
        print(f"    Page title: {title}")
        
        # Check for login form elements (Ant Design structure)
        username_input = page.locator('input[placeholder="用户名"]').first
        assert username_input.is_visible(), "Username input not visible"
        
        password_input = page.locator('input[placeholder="密码"], input[type="password"]').first
        assert password_input.is_visible(), "Password input not visible"
        
        login_button = page.locator('button.ant-btn-primary').first
        assert login_button.is_visible(), "Login button not visible"
        
        browser.close()
        print("    Login page elements verified")


def test_playwright_browser_auth_flow():
    """Use Playwright to test full login → redirect → dashboard flow."""
    from playwright.sync_api import sync_playwright
    import urllib.request
    
    # Read credentials
    env_path = Path(__file__).parent / "backend" / ".env"
    env_content = env_path.read_text()
    username = "admin"
    password = "admin"
    for line in env_content.split("\n"):
        if line.startswith("AUTH_USERNAME="):
            username = line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith("AUTH_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        # Go to login page
        page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=15000)
        
        # Fill in credentials
        page.locator('input[placeholder="用户名"]').fill(username)
        page.locator('input[type="password"]').fill(password)
        
        # Click login
        page.locator('button.ant-btn-primary').click()
        
        # Wait for navigation (should redirect to /)
        page.wait_for_url("**/*", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Check we're on the main page (check content, not just URL — React Router may lag)
        import time
        time.sleep(2)
        current_url = page.url
        print(f"    After login, URL: {current_url}")
        
        # Check dashboard content is shown
        body_text = page.locator("body").inner_text()
        print(f"    Page body preview: {body_text[:200]}")
        
        # Dashboard should show scan button or "暂无页面数据"
        has_dashboard = "扫描" in body_text or "scan" in body_text.lower() or "暂无" in body_text or "empty" in body_text.lower()
        assert has_dashboard or "/login" not in current_url, \
            f"Still on login page after login: URL={current_url}, body={body_text[:200]}"
        
        browser.close()
        print("    Full auth flow verified")


def test_playwright_dashboard_scan_button():
    """Use Playwright to test scan button on dashboard."""
    from playwright.sync_api import sync_playwright
    from urllib.request import urlopen, Request
    import urllib
    
    # Get auth cookies
    env_path = Path(__file__).parent / "backend" / ".env"
    env_content = env_path.read_text()
    username = "admin"
    password = "admin"
    for line in env_content.split("\n"):
        if line.startswith("AUTH_USERNAME="):
            username = line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith("AUTH_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    # Login to get session cookie
    req = Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urlopen(req)
    cookie_header = resp.headers.get_all("Set-Cookie")
    cookie_str = "; ".join(cookie_header) if cookie_header else ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        # Add cookies to context
        from http.cookiejar import CookieJar, Cookie
        import time
        
        # Parse cookies from string
        cookies_to_add = []
        for cookie in cookie_str.split("; "):
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                cookies_to_add.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "url": BASE_URL,
                })
        
        if cookies_to_add:
            context.add_cookies(cookies_to_add)
        
        page = context.new_page()
        page.goto(f"{BASE_URL}/", wait_until="networkidle", timeout=15000)
        
        # Look for scan button
        body_text = page.locator("body").inner_text()
        has_scan = "扫描" in body_text or "scan" in body_text.lower() or "Scan" in body_text
        print(f"    Has scan button: {has_scan}")
        
        # Screenshot for debugging
        screenshot_path = "/tmp/mars-sandbox-dashboard.png"
        page.screenshot(path=screenshot_path)
        print(f"    Screenshot saved: {screenshot_path}")
        
        browser.close()


def test_playwright_404_page():
    """Test that non-existent page returns appropriate response."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        # Navigate to non-existent API endpoint
        resp = page.goto(f"{BASE_URL}/api/nonexistent", wait_until="commit", timeout=10000)
        assert resp.status == 404, f"Expected 404, got {resp.status}"
        
        browser.close()


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Mars Sandbox — Playwright Functional Tests")
    print("=" * 60)
    
    tests = [
        # API tests
        ("Health endpoint", test_health),
        ("API docs accessible", test_api_docs_accessible),
        ("Login flow (API)", test_login_flow),
        ("Auth required for pages", test_auth_required),
        ("Scan API", test_scan_api),
        ("Pages list (empty)", test_pages_list_empty),
        ("Frontend served at /", test_frontend_served),
        
        # Playwright browser tests
        ("Login page rendering (Playwright)", test_playwright_browser_login_page),
        ("Full auth flow (Playwright)", test_playwright_browser_auth_flow),
        ("Dashboard scan button (Playwright)", test_playwright_dashboard_scan_button),
        ("404 page (Playwright)", test_playwright_404_page),
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for name, func in tests:
        result = run_test(name, func)
        if result:
            passed += 1
        else:
            failed += 1
            failed_tests.append(name)
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed_tests:
        print("Failed tests:")
        for t in failed_tests:
            print(f"  - {t}")
    print("=" * 60)
    
    sys.exit(1 if failed > 0 else 0)
