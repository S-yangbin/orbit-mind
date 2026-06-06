import { useState, useEffect, useMemo } from "react";
import { Spin, Typography, Tag, Image, Modal } from "antd";
import {
  WifiOutlined,
  DisconnectOutlined,
  CalendarOutlined,
  EnvironmentOutlined,
  MessageOutlined,
  PushpinOutlined,
  CheckCircleFilled,
} from "@ant-design/icons";
import { DashboardPets } from "./DashboardPets";
import { useDashboardWs } from "../hooks/useDashboardWs";
import { resolveColor, formatBoardDateTime, mealPhotoToUrl } from "../utils";
import type {
  DashboardMealPlanItem,
  BoardMessage,
  WeatherInfo,
  WeatherForecastItem,
  DashboardTravelPage,
  DashboardFamilyMember,
} from "../types";

const { Title, Text } = Typography;

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

/** 获取本地日期字符串 YYYY-MM-DD（避免 toISOString 的 UTC 时区偏移） */
function getLocalDateStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** 内置箴言（hitokoto API 不可用时的 fallback） */
const BUILT_IN_QUOTES = [
  "生活不是等待暴风雨过去，而是学会在雨中跳舞。",
  "每一个不曾起舞的日子，都是对生命的辜负。",
  "把每一天当作最后一天来过，终将活出非凡。",
  "温柔半两，从容一生。",
  "星光不问赶路人，时光不负有心人。",
  "人间值得，未来可期。",
  "所有的好事，都在慢慢发生。",
];

/** 根据日期哈希从数组中选取箴言（同一天返回相同） */
function pickBuiltinQuote(): string {
  const d = new Date();
  const dayIndex = d.getFullYear() * 1000 + d.getMonth() * 31 + d.getDate();
  return BUILT_IN_QUOTES[dayIndex % BUILT_IN_QUOTES.length];
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
  const { data, isConnected, familyMembers, acknowledgeMessage } = useDashboardWs();
  const [now, setNow] = useState(new Date());
  const [selectedTravelPage, setSelectedTravelPage] = useState<DashboardTravelPage | null>(null);
  const [dailyQuote, setDailyQuote] = useState<string>(pickBuiltinQuote());

  // 每分钟刷新（用于夜间模式判断）
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(timer);
  }, []);

  // 获取每日箴言（hitokoto API + 内置 fallback）
  useEffect(() => {
    let cancelled = false;
    fetch("https://v1.hitokoto.cn/?c=a&c=b&c=d&c=i&c=k",
      { headers: { "User-Agent": "OrbitMind/1.0" } }
    )
      .then((r) => r.json())
      .then((j) => {
        if (cancelled) return;
        const text = j?.hitokoto;
        const from = j?.from;
        if (text) {
          setDailyQuote(from ? `${text} —— ${from}` : text);
        }
      })
      .catch(() => { /* 使用内置 fallback */ });
    return () => { cancelled = true; };
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

  // 获取所有周末日期（周六、周日），按周分组 —— 仅保留上周和这周
  const weekendWeeks = useMemo(() => {
    const dates = Object.keys(mealByDate);
    if (dates.length === 0) return [];

    const today = new Date();
    const todayStr = getLocalDateStr(today);

    // 本周一（使用本地时间，避免 UTC 偏移）
    const dayOfWeekLocal = today.getDay(); // 0=Sun, 1=Mon, ..., 6=Sat
    const thisMonday = new Date(today);
    thisMonday.setDate(today.getDate() - (dayOfWeekLocal === 0 ? 6 : dayOfWeekLocal - 1));

    // 上周一
    const lastMonday = new Date(thisMonday);
    lastMonday.setDate(thisMonday.getDate() - 7);

    // 下周一（不包含）
    const nextMonday = new Date(thisMonday);
    nextMonday.setDate(thisMonday.getDate() + 7);

    const lastMondayStr = getLocalDateStr(lastMonday);
    const nextMondayStr = getLocalDateStr(nextMonday);

    // 按周分组
    const weeks: { weekLabel: string; days: { dateStr: string; isToday: boolean; isPast: boolean }[] }[] = [];
    let currentWeek: typeof weeks[0] | null = null;

    for (const dateStr of dates) {
      // 只保留 >= 上周一 且 < 下周一 的日期
      if (dateStr < lastMondayStr || dateStr >= nextMondayStr) continue;

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

      {/* 宠物猫狗 */}
      <DashboardPets />

      {/* 内容层 */}
      <div style={{
        position: "relative",
        zIndex: 2,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}>
        {/* Header - 固定不动 */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "20px 32px 16px",
          borderBottom: "1px solid rgba(255,255,255,0.15)",
          flexShrink: 0,
        }}>
          {/* 左侧：每日箴言 */}
          <div style={{
            maxWidth: "60%",
          }}>
            <div style={{
              fontSize: 22,
              fontWeight: 500,
              color: "rgba(255,255,255,0.95)",
              textShadow: "0 2px 8px rgba(0,0,0,0.3)",
              lineHeight: 1.5,
              letterSpacing: "0.5px",
              fontStyle: "italic",
            }}>
              「{dailyQuote}」
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

        {/* 可滚动内容区 */}
        <div style={{
          flex: 1,
          overflow: "auto",
          padding: "20px 32px 20px",
        }}>
        {/* 两栏布局 */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
        }}>
          {/* 左栏 - 食谱安排（周末卡片） */}
          <div style={{
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
                            opacity: day.isPast ? 0.82 : 1,
                            filter: day.isPast ? "grayscale(0.12)" : "none",
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
                                <Image.PreviewGroup>
                                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                                    {mealItems.map((item) => {
                                      const photo = item.dish.photo;
                                      return (
                                        <div key={item.id} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                          {photo ? (
                                            <Image
                                              src={mealPhotoToUrl(photo)}
                                              alt={item.dish.name}
                                              width={28}
                                              height={28}
                                              style={{
                                                borderRadius: 6,
                                                objectFit: "cover",
                                                cursor: "pointer",
                                                border: "1px solid #e5e7eb",
                                              }}
                                              preview={{ src: mealPhotoToUrl(photo) }}
                                              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyOCAyOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHJ4PSI2IiBmaWxsPSIjZjFmNWY5Ii8+PC9zdmc+"
                                            />
                                          ) : null}
                                          <Tag
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
                                        </div>
                                      );
                                    })}
                                  </div>
                                </Image.PreviewGroup>
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

          {/* 右栏 - 旅游计划 + 留言板 上下排列 */}
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}>
            {/* 旅游计划 */}
            <div style={{
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
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {data.travel_pages.map((page, idx) => {
                  const hasImage = !!page.thumbnail;
                  const gradient = TRAVEL_GRADIENTS[page.id % TRAVEL_GRADIENTS.length];

                  return (
                    <div
                      key={page.id}
                      style={{
                        display: "flex",
                        gap: 12,
                        borderRadius: 16,
                        overflow: "hidden",
                        background: "#fff",
                        boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                        transition: "transform 0.2s ease, box-shadow 0.2s ease",
                        cursor: "pointer",
                        padding: 0,
                      }}
                      onClick={() => setSelectedTravelPage(page)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = "scale(1.02)";
                        e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.15)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = "scale(1)";
                        e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.08)";
                      }}
                    >
                      {/* 左侧缩略图 */}
                      {hasImage ? (
                        <img
                          src={page.thumbnail!}
                          alt={page.title}
                          style={{
                            width: 120,
                            height: 80,
                            objectFit: "cover",
                            flexShrink: 0,
                          }}
                        />
                      ) : (
                        <div style={{
                          width: 120,
                          height: 80,
                          flexShrink: 0,
                          background: gradient,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}>
                          <EnvironmentOutlined style={{ fontSize: 28, color: "rgba(255,255,255,0.8)" }} />
                        </div>
                      )}
                      {/* 右侧标题+描述 */}
                      <div style={{ flex: 1, padding: "10px 12px 10px 0", minWidth: 0 }}>
                        <div style={{
                          fontSize: 15,
                          fontWeight: 600,
                          color: "#1e293b",
                          lineHeight: 1.3,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
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
                    </div>
                  );
                })}
              </div>
            )}
          </div>

            {/* 留言板 */}
            <div style={{
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
                      marginBottom: 8,
                    }}>
                      {formatBoardDateTime(msg.created_at)}
                      {msg.expires_at && (
                        <span style={{ marginLeft: 12, opacity: 0.7 }}>
                          有效期至 {new Date(msg.expires_at).toLocaleDateString("zh-CN")}
                        </span>
                      )}
                    </div>

                    {/* 家庭成员已读按钮 */}
                    {familyMembers.length > 0 && (
                      <div style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 6,
                        paddingLeft: isPinned ? 50 : 46,
                      }}>
                        {familyMembers.map((member) => {
                          const isAcked = msg.acknowledged_by?.includes(member.id);
                          return (
                            <button
                              key={member.id}
                              onClick={() => acknowledgeMessage(msg.id, member.id)}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 4,
                                padding: "3px 10px",
                                borderRadius: 12,
                                border: isAcked
                                  ? "1px solid #22c55e"
                                  : "1px solid #e5e7eb",
                                background: isAcked
                                  ? "#dcfce7"
                                  : "#f8fafc",
                                color: isAcked
                                  ? "#15803d"
                                  : "#64748b",
                                fontSize: 12,
                                fontWeight: 500,
                                cursor: "pointer",
                                transition: "all 0.2s ease",
                                lineHeight: 1,
                              }}
                            >
                              <span style={{ fontSize: 14 }}>{member.avatar}</span>
                              <span>{member.name}</span>
                              {isAcked && (
                                <CheckCircleFilled style={{ fontSize: 12, color: "#22c55e" }} />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
          </div>
        </div>
        </div>

        {/* 旅游计划弹窗 */}
        <Modal
          open={!!selectedTravelPage}
          onCancel={() => setSelectedTravelPage(null)}
          footer={null}
          title={selectedTravelPage?.title}
          width="90vw"
          style={{ top: 20 }}
          styles={{ body: { height: "80vh", padding: 0 } }}
          destroyOnClose
        >
          {selectedTravelPage && (
            <iframe
              src={`/files/${selectedTravelPage.slug}/${selectedTravelPage.entry_file}`}
              style={{
                width: "100%",
                height: "100%",
                border: "none",
                borderRadius: 8,
              }}
              sandbox="allow-scripts allow-same-origin allow-forms allow-modals"
              title={selectedTravelPage.title}
            />
          )}
        </Modal>
      </div>
    </div>
  );
}
