import { useState, useEffect, useRef, useCallback } from "react";
import type { DashboardData, DashboardWsMessage, BoardMessage, DashboardFamilyMember } from "../types";

interface UseDashboardWsReturn {
  data: DashboardData | null;
  isConnected: boolean;
  lastUpdate: string | null;
  familyMembers: DashboardFamilyMember[];
  acknowledgeMessage: (messageId: number, memberId: number) => void;
  /** 非壁纸内容更新版本，每次变化可用于唤醒屏保 */
  contentVersion: number;
}

/**
 * Dashboard WebSocket Hook
 * 连接到 /ws/dashboard，实时接收看板数据
 * - 自动重连（指数退避）
 * - 心跳响应
 */
export function useDashboardWs(): UseDashboardWsReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [contentVersion, setContentVersion] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectDelayRef = useRef(1000); // 初始重连延迟 1s

  const connect = useCallback(() => {
    // 避免重复连接
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectDelayRef.current = 1000; // 重置重连延迟
    };

    ws.onmessage = (event) => {
      try {
        const msg: DashboardWsMessage = JSON.parse(event.data);

        switch (msg.type) {
          case "dashboard_update":
            // 全量数据更新（周期性刷新，不唤醒屏保）
            if (msg.data) {
              setData(msg.data);
              setLastUpdate(msg.timestamp || new Date().toISOString());
            }
            break;

          case "message_added":
            // 新留言
            if (msg.message && "id" in msg.message) {
              setData((prev) => {
                if (!prev) return prev;
                // 避免重复添加
                if (prev.messages.some((m) => m.id === (msg.message as BoardMessage).id)) {
                  return prev;
                }
                return {
                  ...prev,
                  messages: [msg.message as BoardMessage, ...prev.messages],
                };
              });
              setContentVersion((v) => v + 1);
            }
            break;

          case "message_deleted":
            // 留言被删除
            if (msg.message && "id" in msg.message) {
              const deletedId = (msg.message as { id: number }).id;
              setData((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  messages: prev.messages.filter((m) => m.id !== deletedId),
                };
              });
              setContentVersion((v) => v + 1);
            }
            break;

          case "message_updated":
            // 留言内容/颜色被编辑
            if (msg.message && "id" in msg.message) {
              const updatedMsg = msg.message as BoardMessage;
              setData((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  messages: prev.messages.map((m) =>
                    m.id === updatedMsg.id ? updatedMsg : m
                  ),
                };
              });
              setContentVersion((v) => v + 1);
            }
            break;

          case "message_pinned":
            // 留言置顶状态变更
            if (msg.message && "id" in msg.message) {
              const updated = msg.message as BoardMessage;
              setData((prev) => {
                if (!prev) return prev;
                const newMessages = prev.messages.map((m) =>
                  m.id === updated.id ? updated : m
                );
                // 重新排序：置顶优先
                newMessages.sort((a, b) => {
                  if (a.pinned !== b.pinned) return b.pinned - a.pinned;
                  return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                });
                return { ...prev, messages: newMessages };
              });
              setContentVersion((v) => v + 1);
            }
            break;

          case "message_acknowledged":
            // 留言被成员确认
            if (msg.message_id !== undefined && msg.acknowledged_by) {
              const targetId = msg.message_id;
              const newAck = msg.acknowledged_by;
              setData((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  messages: prev.messages.map((m) =>
                    m.id === targetId ? { ...m, acknowledged_by: newAck } : m
                  ),
                };
              });
              setContentVersion((v) => v + 1);
            }
            break;

          case "wallpaper_updated":
            // 壁纸已刷新
            if (msg.data?.background_image) {
              const newBg = msg.data.background_image;
              setData((prev) => {
                if (!prev) return prev;
                return { ...prev, background_image: newBg };
              });
            }
            break;

          case "meal_plan_updated":
            // 菜单已更新
            if (msg.data?.meal_plans) {
              const newMealPlans = msg.data.meal_plans;
              setData((prev) => {
                if (!prev) return prev;
                return { ...prev, meal_plans: newMealPlans };
              });
              setContentVersion((v) => v + 1);
            }
            break;

          case "pong":
            // 心跳响应，无需处理
            break;
        }
      } catch (e) {
        console.error("Dashboard WS message parse error:", e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;

      // 指数退避重连
      const delay = Math.min(reconnectDelayRef.current, 30000);
      reconnectDelayRef.current *= 2;
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();

    // 心跳：每 20s 发送 ping
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 20000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  // acknowledgeMessage: 通过 WS 发送留言确认
  const acknowledgeMessage = useCallback((messageId: number, memberId: number) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "acknowledge_message",
        message_id: messageId,
        member_id: memberId,
      }));
    }
  }, []);

  // 家庭成员列表
  const familyMembers = data?.family_members ?? [];

  return { data, isConnected, lastUpdate, familyMembers, acknowledgeMessage, contentVersion };
}
