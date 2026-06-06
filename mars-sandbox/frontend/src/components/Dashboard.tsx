import { useState, useEffect, useMemo } from "react";
import { Spin, Typography, Tag } from "antd";
import {
  WifiOutlined,
  DisconnectOutlined,
  CalendarOutlined,
  EnvironmentOutlined,
  MessageOutlined,
  PushpinOutlined,
} from "@ant-design/icons";
import { useDashboardWs } from "../hooks/useDashboardWs";
import type {
  DashboardMealPlanItem,
  BoardMessage,
  WeatherInfo,
  WeatherForecastItem,
} from "../types";

const { Title, Text } = Typography;

const COLOR_MAP: Record<string, string> = {
  yellow: "#fef9c3",
  pink: "#fce7f3",
  blue: "#dbeafe",
  green: "#dcfce7",
};

// 留言作者首字母头像的柔和背景色
const AVATAR_COLORS = [
  "#fca5a5", "#fdba74", "#fcd34d", "#86efac",
  "#67e8f9", "#a5b4fc", "#f0abfc", "#f9a8d4",
];

function getAvatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

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

const MEAL_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  lunch: { label: "全家午餐", color: "#f97316" },
  dinner: { label: "儿童晚餐", color: "#22c55e" },
  breakfast: { label: "早餐", color: "#3b82f6" },
};

const WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

function formatWeekendDate(dateStr: string): string {
  const d = new Date(dateStr);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const weekday = WEEKDAY_NAMES[d.getDay() === 0 ? 6 : d.getDay() - 1];
  return `${month}/${day} ${weekday}`;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatFullDate(date: Date): string {
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });
}

function weatherIconUrl(icon: string, size: "2x" | "4x" = "2x"): string {
  return `https://openweathermap.org/img/wn/${icon}@${size}.png`;
}

/** 判断是否为特殊天气 */
function isSpecialWeather(desc: string): boolean {
  const keywords = ["雨", "雪", "雷", "暴雨", "暴雪", "高温", "大风"];
  return keywords.some((k) => desc.includes(k));
}

/** 旅游计划渐变色（基于 id 稳定） */
const TRAVEL_GRADIENTS = [
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
];

export function Dashboard() {
  const { data, isConnected } = useDashboardWs();
  const [now, setNow] = useState(new Date());

  // 每秒更新时间显示
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 夜间模式判断（18:00后或6:00前）
  const isNight = now.getHours() >= 18 || now.getHours() < 6;

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
    return Object.fromEntries(
      Object.entries(map).sort(([a], [b]) => a.localeCompare(b))
    );
  }, [data?.meal_plans]);

  // 获取所有周末日期（周六、周日），按周分组
  const weekendWeeks = useMemo(() => {
    const dates = Object.keys(mealByDate);
    if (dates.length === 0) return [];

    const todayStr = new Date().toISOString().split("T")[0];
    // 按周分组
    const weeks: { weekLabel: string; days: { dateStr: string; isToday: boolean; isPast: boolean }[] }[] = [];
    let currentWeek: typeof weeks[0] | null = null;

    for (const dateStr of dates) {
      const d = new Date(dateStr);
      const dayOfWeek = d.getDay(); // 0=Sun, 6=Sat
      if (dayOfWeek !== 0 && dayOfWeek !== 6) continue;

      // 计算该日期所在周的周一
      const monday = new Date(d);
      monday.setDate(d.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
      const weekLabel = `${monday.getMonth() + 1}/${monday.getDate()} 周`;

      const isPast = dateStr < todayStr;
      const isToday = dateStr === todayStr;

      if (!currentWeek || currentWeek.weekLabel !== weekLabel) {
        currentWeek = { weekLabel, days: [] };
        weeks.push(currentWeek);
      }
      currentWeek.days.push({ dateStr, isToday, isPast });
    }
    return weeks;
  }, [mealByDate]);

  // 客户端过滤过期留言
  const activeMessages = useMemo(() => {
    if (!data?.messages) return [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return data.messages.filter((msg: BoardMessage) => {
      if (!msg.expires_at) return true;
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
        background: "#0f172a",
      }}>
        <Spin size="large" tip="正在连接看板..." />
      </div>
    );
  }

  const bgImage = data.background_image;
  const weather = data.weather;
  const forecast = data.weather_forecast;

  return (
    <div style={{
      minHeight: "100vh",
      position: "relative",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif",
      overflow: "hidden",
    }}>
      {/* 全屏壁纸背景 */}
      {bgImage && (
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundImage: `url(${bgImage})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          zIndex: 0,
          transition: "opacity 0.8s ease",
        }} />
      )}

      {/* 暗色遮罩（夜间加深） */}
      <div style={{
        position: "fixed",
        inset: 0,
        background: isNight
          ? "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.4) 100%)"
          : "linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.15) 100%)",
        zIndex: 1,
        transition: "background 1s ease",
      }} />

      {/* 内容层 */}
      <div style={{
        position: "relative",
        zIndex: 2,
        padding: "20px 32px",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}>
        {/* Header */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
          paddingBottom: 16,
          borderBottom: "1px solid rgba(255,255,255,0.15)",
        }}>
          {/* 左侧：日期时间 */}
          <div>
            <div style={{
              fontSize: 28,
              fontWeight: 600,
              color: "#fff",
              textShadow: "0 2px 8px rgba(0,0,0,0.3)",
              marginBottom: 4,
            }}>
              {formatFullDate(now)}
            </div>
            <div style={{
              fontSize: 48,
              fontWeight: 300,
              color: "rgba(255,255,255,0.9)",
              textShadow: "0 2px 8px rgba(0,0,0,0.3)",
              lineHeight: 1,
              letterSpacing: "-1px",
            }}>
              {formatTime(now)}
            </div>
          </div>

          {/* 右侧：天气信息 */}
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            {weather && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                background: "rgba(255,255,255,0.15)",
                backdropFilter: "blur(12px)",
                borderRadius: 16,
                padding: "8px 20px",
              }}>
                {/* 当前天气 */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <img
                    src={weatherIconUrl(weather.icon, "4x")}
                    alt={weather.description}
                    style={{ width: 64, height: 64, filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.2))" }}
                  />
                  <div>
                    <div style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: "#fff",
                      lineHeight: 1,
                    }}>
                      {weather.temp}°
                    </div>
                    <div style={{ fontSize: 14, color: "rgba(255,255,255,0.8)" }}>
                      {weather.description}
                    </div>
                  </div>
                </div>

                {/* 分隔线 */}
                <div style={{
                  width: 1,
                  height: 48,
                  background: "rgba(255,255,255,0.2)",
                }} />

                {/* 未来3天预报 */}
                <div style={{ display: "flex", gap: 16 }}>
                  {forecast?.map((f: WeatherForecastItem) => (
                    <div key={f.date} style={{
                      textAlign: "center",
                      opacity: isSpecialWeather(f.description) ? 1 : 0.85,
                    }}>
                      <div style={{
                        fontSize: 11,
                        color: "rgba(255,255,255,0.7)",
                        marginBottom: 2,
                      }}>
                        {new Date(f.date).toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" })}
                      </div>
                      <img
                        src={weatherIconUrl(f.icon)}
                        alt={f.description}
                        style={{
                          width: 36,
                          height: 36,
                          filter: isSpecialWeather(f.description)
                            ? "drop-shadow(0 0 4px rgba(251,191,36,0.6))"
                            : "none",
                        }}
                      />
                      <div style={{
                        fontSize: 12,
                        color: isSpecialWeather(f.description)
                          ? "#fbbf24"
                          : "rgba(255,255,255,0.9)",
                        fontWeight: 500,
                      }}>
                        {f.temp_max}° / {f.temp_min}°
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 连接状态 */}
            {isConnected ? (
              <Tag
                icon={<WifiOutlined />}
                color="success"
                style={{
                  fontSize: 13,
                  padding: "4px 12px",
                  borderRadius: 12,
                }}
              >
                已连接
              </Tag>
            ) : (
              <Tag
                icon={<DisconnectOutlined />}
                color="error"
                style={{
                  fontSize: 13,
                  padding: "4px 12px",
                  borderRadius: 12,
                }}
              >
                重连中
              </Tag>
            )}
          </div>
        </div>

        {/* 三栏布局 */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 20,
          flex: 1,
          overflow: "hidden",
        }}>
          {/* 左栏 - 食谱安排（周末卡片） */}
          <div style={{
            overflow: "auto",
            borderRadius: 16,
            padding: "16px 20px",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <CalendarOutlined style={{ fontSize: 22, color: "#a78bfa" }} />
              <Text strong style={{ fontSize: 20, color: "#fff", textShadow: "0 1px 4px rgba(0,0,0,0.3)" }}>周末食谱</Text>
            </div>

            {weekendWeeks.length === 0 ? (
              <div style={{ textAlign: "center", color: "rgba(255,255,255,0.6)", padding: "40px 0", fontSize: 16 }}>
                暂无周末食谱安排
              </div>
            ) : (
              weekendWeeks.map((week) => (
                <div key={week.weekLabel} style={{ marginBottom: 16 }}>
                  <div style={{
                    fontSize: 13,
                    color: "rgba(255,255,255,0.6)",
                    fontWeight: 500,
                    marginBottom: 8,
                    textTransform: "uppercase",
                  }}>
                    {week.weekLabel}
                  </div>
                  <div style={{ display: "flex", gap: 12 }}>
                    {week.days.map((day) => {
                      const items = mealByDate[day.dateStr];
                      const byMealType: Record<string, typeof items> = {};
                      for (const item of items) {
                        if (!byMealType[item.meal_type]) byMealType[item.meal_type] = [];
                        byMealType[item.meal_type].push(item);
                      }

                      return (
                        <div
                          key={day.dateStr}
                          style={{
                            flex: 1,
                            background: "#fff",
                            borderRadius: 16,
                            padding: "12px 14px",
                            border: day.isToday
                              ? "2px solid rgba(124,58,237,0.4)"
                              : "1px solid rgba(0,0,0,0.06)",
                            opacity: day.isPast ? 0.5 : 1,
                            filter: day.isPast ? "grayscale(0.3)" : "none",
                            transition: "all 0.3s ease",
                          }}
                        >
                          <div style={{
                            fontSize: 15,
                            fontWeight: 600,
                            color: day.isToday ? "#7c3aed" : "#334155",
                            marginBottom: 10,
                          }}>
                            {formatWeekendDate(day.dateStr)}
                            {day.isToday && (
                              <span style={{
                                marginLeft: 8,
                                fontSize: 11,
                                background: "#7c3aed",
                                color: "#fff",
                                padding: "2px 8px",
                                borderRadius: 8,
                                fontWeight: 500,
                              }}>
                                今天
                              </span>
                            )}
                          </div>

                          {Object.entries(byMealType).map(([mealType, mealItems]) => {
                            const config = MEAL_TYPE_CONFIG[mealType] || { label: mealType, color: "#6b7280" };
                            return (
                              <div key={mealType} style={{ marginBottom: 8 }}>
                                <div style={{
                                  fontSize: 12,
                                  color: config.color,
                                  fontWeight: 500,
                                  marginBottom: 4,
                                }}>
                                  {config.label}
                                </div>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                                  {mealItems.map((item) => (
                                    <Tag
                                      key={item.id}
                                      style={{
                                        margin: 0,
                                        borderRadius: 8,
                                        fontSize: 13,
                                        background: `${config.color}15`,
                                        color: config.color,
                                        border: `1px solid ${config.color}30`,
                                      }}
                                    >
                                      {item.dish.name}
                                    </Tag>
                                  ))}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 中栏 - 旅游计划（瀑布流照片墙） */}
          <div style={{
            overflow: "auto",
            borderRadius: 16,
            padding: "16px 20px",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <EnvironmentOutlined style={{ fontSize: 22, color: "#22d3ee" }} />
              <Text strong style={{ fontSize: 20, color: "#fff", textShadow: "0 1px 4px rgba(0,0,0,0.3)" }}>旅游计划</Text>
            </div>

            {data.travel_pages.length === 0 ? (
              <div style={{ textAlign: "center", color: "rgba(255,255,255,0.6)", padding: "40px 0", fontSize: 16 }}>
                暂无旅游计划
              </div>
            ) : (
              <div style={{
                columns: 2,
                columnGap: 12,
              }}>
                {data.travel_pages.map((page, idx) => {
                  const hasImage = !!page.thumbnail;
                  const gradient = TRAVEL_GRADIENTS[page.id % TRAVEL_GRADIENTS.length];

                  return (
                    <div
                      key={page.id}
                      style={{
                        breakInside: "avoid",
                        marginBottom: 12,
                        borderRadius: 16,
                        overflow: "hidden",
                        background: hasImage ? "#fff" : gradient,
                        boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                        transition: "transform 0.2s ease, box-shadow 0.2s ease",
                        cursor: "pointer",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = "scale(1.03)";
                        e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.15)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = "scale(1)";
                        e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.08)";
                      }}
                    >
                      {hasImage ? (
                        <>
                          <img
                            src={page.thumbnail!}
                            alt={page.title}
                            style={{
                              width: "100%",
                              display: "block",
                              // 交替高度制造错落感
                              height: idx % 3 === 0 ? 180 : idx % 3 === 1 ? 140 : 160,
                              objectFit: "cover",
                            }}
                          />
                          <div style={{ padding: "10px 12px" }}>
                            <div style={{
                              fontSize: 14,
                              fontWeight: 600,
                              color: "#1e293b",
                              lineHeight: 1.3,
                            }}>
                              {page.title}
                            </div>
                            {page.description && (
                              <div style={{
                                fontSize: 12,
                                color: "#64748b",
                                marginTop: 4,
                                lineHeight: 1.4,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                display: "-webkit-box",
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: "vertical",
                              }}>
                                {page.description}
                              </div>
                            )}
                          </div>
                        </>
                      ) : (
                        <div style={{
                          padding: "20px 16px",
                          minHeight: idx % 2 === 0 ? 140 : 120,
                          display: "flex",
                          flexDirection: "column",
                          justifyContent: "center",
                        }}>
                          <div style={{
                            fontSize: 16,
                            fontWeight: 600,
                            color: "#fff",
                            textShadow: "0 1px 4px rgba(0,0,0,0.2)",
                            lineHeight: 1.3,
                          }}>
                            {page.title}
                          </div>
                          {page.description && (
                            <div style={{
                              fontSize: 13,
                              color: "rgba(255,255,255,0.85)",
                              marginTop: 6,
                              lineHeight: 1.4,
                            }}>
                              {page.description.length > 60
                                ? page.description.substring(0, 60) + "..."
                                : page.description}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 右栏 - 留言板（家庭卡片） */}
          <div style={{
            overflow: "auto",
            borderRadius: 16,
            padding: "16px 20px",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <MessageOutlined style={{ fontSize: 22, color: "#fb923c" }} />
              <Text strong style={{ fontSize: 20, color: "#fff", textShadow: "0 1px 4px rgba(0,0,0,0.3)" }}>家庭留言</Text>
            </div>

            {activeMessages.length === 0 ? (
              <div style={{ textAlign: "center", color: "rgba(255,255,255,0.6)", padding: "40px 0", fontSize: 16 }}>
                暂无留言
              </div>
            ) : (
              activeMessages.map((msg: BoardMessage) => {
                const authorName = msg.author || "匿名";
                const initial = authorName.charAt(0).toUpperCase();
                const avatarBg = getAvatarColor(authorName);
                const isPinned = !!msg.pinned;

                return (
                  <div
                    key={msg.id}
                    style={{
                      background: isPinned ? "#fffbeb" : "#fff",
                      borderLeft: `4px solid ${resolveColor(msg.color)}`,
                      borderRadius: 16,
                      padding: isPinned ? "16px 18px" : "14px 16px",
                      marginBottom: 12,
                      boxShadow: isPinned
                        ? "0 4px 16px rgba(0,0,0,0.1)"
                        : "0 2px 8px rgba(0,0,0,0.05)",
                      transition: "all 0.3s ease",
                    }}
                  >
                    {/* 头部：头像 + 作者 */}
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      marginBottom: 10,
                    }}>
                      <div style={{
                        width: isPinned ? 40 : 36,
                        height: isPinned ? 40 : 36,
                        borderRadius: "50%",
                        background: avatarBg,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: isPinned ? 18 : 16,
                        fontWeight: 600,
                        color: "#fff",
                        flexShrink: 0,
                      }}>
                        {initial}
                      </div>
                      <div style={{ flex: 1 }}>
                        <span style={{
                          fontSize: 15,
                          fontWeight: 600,
                          color: "#334155",
                        }}>
                          {authorName}
                        </span>
                        <span style={{ fontSize: 14, color: "#64748b", marginLeft: 6 }}>
                          留言说
                        </span>
                      </div>
                      {isPinned && (
                        <PushpinOutlined style={{
                          fontSize: 16,
                          color: "#f59e0b",
                        }} />
                      )}
                    </div>

                    {/* 内容 */}
                    <div style={{
                      fontSize: 16,
                      lineHeight: 1.6,
                      color: "#1e293b",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      marginBottom: 10,
                      paddingLeft: isPinned ? 50 : 46,
                    }}>
                      {msg.content}
                    </div>

                    {/* 底部时间 */}
                    <div style={{
                      fontSize: 12,
                      color: "#94a3b8",
                      paddingLeft: isPinned ? 50 : 46,
                    }}>
                      {formatBoardDateTime(msg.created_at)}
                      {msg.expires_at && (
                        <span style={{ marginLeft: 12, opacity: 0.7 }}>
                          有效期至 {new Date(msg.expires_at).toLocaleDateString("zh-CN")}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
