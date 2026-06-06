import { useState, useEffect, useMemo } from "react";
import { Spin, Typography, Tag } from "antd";
import {
  WifiOutlined,
  DisconnectOutlined,
  CalendarOutlined,
  EnvironmentOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import { useDashboardWs } from "../hooks/useDashboardWs";
import type { DashboardMealPlanItem, BoardMessage } from "../types";

const { Title, Text } = Typography;

const COLOR_MAP: Record<string, string> = {
  yellow: "#fef9c3",
  pink: "#fce7f3",
  blue: "#dbeafe",
  green: "#dcfce7",
};

/** 兼容命名颜色和 hex 颜色 */
function resolveColor(color: string): string {
  return COLOR_MAP[color] || color;
}

function formatBoardDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: "早餐",
  lunch: "午餐",
  dinner: "晚餐",
};

const WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const weekday = WEEKDAY_NAMES[d.getDay() === 0 ? 6 : d.getDay() - 1];
  return `${month}/${day} ${weekday}`;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function formatFullDate(date: Date): string {
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });
}

export function Dashboard() {
  const { data, isConnected } = useDashboardWs();
  const [now, setNow] = useState(new Date());

  // 每秒更新时间显示
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 按日期分组食谱
  const mealByDate = useMemo(() => {
    if (!data?.meal_plans) return {};
    const map: Record<string, DashboardMealPlanItem[]> = {};
    for (const plan of data.meal_plans) {
      for (const item of plan.items) {
        if (!item.date) continue;
        if (!map[item.date]) map[item.date] = [];
        map[item.date].push(item);
      }
    }
    // 按日期排序
    return Object.fromEntries(
      Object.entries(map).sort(([a], [b]) => a.localeCompare(b))
    );
  }, [data?.meal_plans]);

  // 只显示今天及未来 7 天
  const upcomingDates = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dates: string[] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      dates.push(d.toISOString().split("T")[0]);
    }
    return dates;
  }, []);

  // 客户端过滤过期留言（后端也过滤，这里做双重保障）
  const activeMessages = useMemo(() => {
    if (!data?.messages) return [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return data.messages.filter((msg: BoardMessage) => {
      if (!msg.expires_at) return true; // 永不过期
      return new Date(msg.expires_at) >= today;
    });
  }, [data?.messages]);

  if (!data) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        background: "#f8fafc",
      }}>
        <Spin size="large" tip="正在连接看板..." />
      </div>
    );
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #f0f4ff 0%, #fdf2f8 50%, #f0fdf4 100%)",
      padding: "20px 32px",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    }}>
      {/* 顶部标题栏 */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 24,
        paddingBottom: 16,
        borderBottom: "1px solid rgba(0,0,0,0.06)",
      }}>
        <div>
          <Title level={2} style={{ margin: 0, color: "#1e293b" }}>
            {formatFullDate(now)}
          </Title>
          <Text style={{ fontSize: 36, fontWeight: 300, color: "#64748b" }}>
            {formatTime(now)}
          </Text>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isConnected ? (
            <Tag icon={<WifiOutlined />} color="success" style={{ fontSize: 13, padding: "4px 12px" }}>
              已连接
            </Tag>
          ) : (
            <Tag icon={<DisconnectOutlined />} color="error" style={{ fontSize: 13, padding: "4px 12px" }}>
              重连中...
            </Tag>
          )}
        </div>
      </div>

      {/* 三栏布局 */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 24,
        height: "calc(100vh - 160px)",
        overflow: "hidden",
      }}>
        {/* 左栏 - 食谱安排 */}
        <div style={{ overflow: "auto", paddingRight: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <CalendarOutlined style={{ fontSize: 20, color: "#7c3aed" }} />
            <Text strong style={{ fontSize: 18 }}>食谱安排</Text>
          </div>

          {upcomingDates.map((dateStr) => {
            const items = mealByDate[dateStr];
            if (!items || items.length === 0) return null;

            // 按餐次分组
            const byMealType: Record<string, typeof items> = {};
            for (const item of items) {
              if (!byMealType[item.meal_type]) byMealType[item.meal_type] = [];
              byMealType[item.meal_type].push(item);
            }

            return (
              <div key={dateStr} style={{
                background: "#fff",
                borderRadius: 12,
                padding: "12px 16px",
                marginBottom: 12,
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              }}>
                <Text strong style={{ fontSize: 14, color: "#475569" }}>
                  {formatDate(dateStr)}
                </Text>
                {Object.entries(byMealType).map(([mealType, mealItems]) => (
                  <div key={mealType} style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {MEAL_TYPE_LABELS[mealType] || mealType}
                    </Text>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                      {mealItems.map((item) => (
                        <Tag key={item.id} color="purple" style={{ margin: 0 }}>
                          {item.dish.name}
                        </Tag>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            );
          })}

          {upcomingDates.every((d) => !mealByDate[d]?.length) && (
            <div style={{ textAlign: "center", color: "#94a3b8", padding: "40px 0" }}>
              暂无食谱安排
            </div>
          )}
        </div>

        {/* 中栏 - 旅游计划 */}
        <div style={{ overflow: "auto", paddingRight: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <EnvironmentOutlined style={{ fontSize: 20, color: "#0891b2" }} />
            <Text strong style={{ fontSize: 18 }}>旅游计划</Text>
          </div>

          {data.travel_pages.length === 0 ? (
            <div style={{ textAlign: "center", color: "#94a3b8", padding: "40px 0" }}>
              暂无旅游计划
            </div>
          ) : (
            data.travel_pages.map((page) => (
              <div key={page.id} style={{
                background: "#fff",
                borderRadius: 12,
                padding: "16px",
                marginBottom: 12,
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              }}>
                {page.thumbnail && (
                  <img
                    src={page.thumbnail}
                    alt={page.title}
                    style={{
                      width: "100%",
                      height: 120,
                      objectFit: "cover",
                      borderRadius: 8,
                      marginBottom: 8,
                    }}
                  />
                )}
                <Text strong style={{ fontSize: 15, display: "block" }}>
                  {page.title}
                </Text>
                {page.description && (
                  <Text type="secondary" style={{ fontSize: 13, lineHeight: 1.5, display: "block", marginTop: 4 }}>
                    {page.description.length > 100
                      ? page.description.substring(0, 100) + "..."
                      : page.description}
                  </Text>
                )}
              </div>
            ))
          )}
        </div>

        {/* 右栏 - 留言板 */}
        <div style={{ overflow: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <MessageOutlined style={{ fontSize: 20, color: "#ea580c" }} />
            <Text strong style={{ fontSize: 18 }}>家庭留言</Text>
          </div>

          {activeMessages.length === 0 ? (
            <div style={{ textAlign: "center", color: "#94a3b8", padding: "40px 0" }}>
              暂无留言
            </div>
          ) : (
            activeMessages.map((msg: BoardMessage) => (
              <div key={msg.id} style={{
                background: resolveColor(msg.color),
                borderRadius: 10,
                padding: "12px 16px",
                marginBottom: 10,
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              }}>
                <div style={{
                  fontSize: 14,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  marginBottom: 8,
                }}>
                  {msg.content}
                </div>
                <div style={{ fontSize: 11, color: "#64748b" }}>
                  {msg.author || "匿名"} · {formatBoardDateTime(msg.created_at)}
                  {msg.expires_at && (
                    <span style={{ marginLeft: 8, opacity: 0.7 }}>
                      至 {new Date(msg.expires_at).toLocaleDateString("zh-CN")}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
