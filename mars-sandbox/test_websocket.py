#!/usr/bin/env python3
"""
测试WebSocket连接和命令执行
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

try:
    import websockets
except ImportError:
    print("错误: 需要安装 websockets 库")
    print("运行: pip install websockets")
    sys.exit(1)


async def test_websocket_connection():
    """测试WebSocket连接"""
    server_url = os.getenv("MARS_SANDBOX_URL", "ws://localhost:8888")
    node_id = "test-node-001"
    secret = os.getenv("NODE_API_KEY", "")
    if not secret:
        print("错误: 请设置 NODE_API_KEY 环境变量")
        return False
    
    url = f"{server_url}/ws/agent/{node_id}?secret={secret}"
    
    print(f"连接到: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✓ WebSocket连接成功")
            
            # 发送注册消息
            register_msg = {
                "type": "register",
                "node_id": node_id,
                "hostname": "test-machine",
                "ip": "127.0.0.1",
                "platform": "Test Platform",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            await websocket.send(json.dumps(register_msg))
            print("✓ 已发送注册消息")
            
            # 等待注册确认
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get("type") == "register_ack":
                print(f"✓ 注册成功: {data.get('message')}")
            else:
                print(f"✗ 注册失败: {data}")
                return False
            
            # 发送心跳
            for i in range(3):
                heartbeat_msg = {
                    "type": "heartbeat",
                    "node_id": node_id,
                    "uptime_seconds": (i + 1) * 10,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
                await websocket.send(json.dumps(heartbeat_msg))
                print(f"✓ 已发送心跳 #{i+1}")
                
                await asyncio.sleep(2)
            
            print("\n✓ WebSocket连接测试通过!")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✗ 连接失败: HTTP {e.status_code}")
        print(f"  响应: {e.response}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


async def test_http_api():
    """测试HTTP API发送命令"""
    import requests
    
    server_url = os.getenv("MARS_SANDBOX_URL", "http://localhost:8888")
    api_key = os.getenv("NODE_API_KEY", "")
    if not api_key:
        print("错误: 请设置 NODE_API_KEY 环境变量")
        return False
    
    print(f"\n测试HTTP API: {server_url}/api/commands")
    
    # 先检查节点是否在线
    try:
        resp = requests.get(
            f"{server_url}/api/nodes",
            headers={"X-API-Key": api_key},
            timeout=10,
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"在线节点: {data.get('online')}/{data.get('total')}")
            
            if data.get('online', 0) == 0:
                print("✗ 没有在线节点,请先启动home-agent")
                return False
    except Exception as e:
        print(f"✗ 查询节点失败: {str(e)}")
        return False
    
    # 发送测试命令
    try:
        payload = {
            "node_id": "test-node-001",  # 修改为实际的node_id
            "command": "echo 'Hello from mars-sandbox!'",
            "timeout": 10,
        }
        
        print(f"发送命令: {payload['command']}")
        
        resp = requests.post(
            f"{server_url}/api/commands",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
            timeout=15,
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✓ 命令执行成功!")
            print(f"  退出码: {result.get('exit_code')}")
            print(f"  输出: {result.get('stdout')}")
            print(f"  耗时: {result.get('duration_ms')}ms")
            return True
        else:
            print(f"✗ 命令执行失败: HTTP {resp.status_code}")
            print(f"  响应: {resp.text}")
            return False
            
    except Exception as e:
        print(f"✗ 发送命令失败: {str(e)}")
        return False


async def main():
    print("=" * 60)
    print("Mars Sandbox WebSocket 测试")
    print("=" * 60)
    
    # 测试WebSocket连接
    print("\n[测试 1] WebSocket连接")
    ws_ok = await test_websocket_connection()
    
    # 测试HTTP API
    print("\n[测试 2] HTTP API命令执行")
    http_ok = await test_http_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"WebSocket连接: {'✓ 通过' if ws_ok else '✗ 失败'}")
    print(f"HTTP API: {'✓ 通过' if http_ok else '✗ 失败'}")
    
    if ws_ok and http_ok:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
