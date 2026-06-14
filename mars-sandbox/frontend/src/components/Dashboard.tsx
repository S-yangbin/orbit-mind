import { useState, useEffect, useRef, useMemo, memo, useCallback } from "react";
import { Spin, Typography, Tag, Image, Modal, Button, Input, message } from "antd";
import {
  WifiOutlined,
  DisconnectOutlined,
  CalendarOutlined,
  EnvironmentOutlined,
  MessageOutlined,
  PushpinOutlined,
  CheckCircleFilled,
  CheckCircleOutlined,
  LeftOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { DashboardPets } from "./DashboardPets";
import { StarWall, StarWallFullModal } from "./StarWall";
import { useDashboardWs } from "../hooks/useDashboardWs";
import { updateDailyItem, fetchDailySchedule } from "../api/schedule";
import { updateMember } from "../api/meals";
import { resolveColor, tintBackground, formatBoardDateTime, mealPhotoToUrl } from "../utils";
import type {
  DashboardMealPlanItem,
  BoardMessage,
  WeatherInfo,
  WeatherForecastItem,
  DashboardTravelPage,
  DashboardFamilyMember,
  TodayScheduleItem,
} from "../types";

const { Title, Text } = Typography;

const AVATAR_OPTIONS = [
  "👨", "👩", "👧", "👦", "👴", "👵", "🧑", "👶",
  "🐱", "🐶", "🐰", "🐼", "🦊", "🐻", "🐨", "🐸",
];

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

/** 屏保空闲超时（毫秒）：无操作 5 分钟后隐藏内容仅展示壁纸 */
const SCREENSAVER_IDLE_MS = 5 * 60 * 1000;

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

/** 箴言前置图标池 */
const QUOTE_ICONS = [
  "✨", "🌿", "🌸", "🍃", "🌙", "🌊", "🦋",
  "🍂", "☀️", "🌷", "🍀", "🎋", "🌺", "🐚",
];

/** 根据日期哈希从数组中选取（同一天返回相同） */
function pickByDate<T>(arr: T[]): T {
  const d = new Date();
  const dayIndex = d.getFullYear() * 1000 + d.getMonth() * 31 + d.getDate();
  return arr[dayIndex % arr.length];
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
  const {
    data, isConnected, familyMembers, acknowledgeMessage, contentVersion,
    ttsVersion, ttsText, ttsPage,
    switchPageVersion, switchPageTarget, autoRotate, autoRotateInterval,
    screensaverVersion, screensaverEnabled,
  } = useDashboardWs();
  const [now, setNow] = useState(new Date());
  const [selectedTravelPage, setSelectedTravelPage] = useState<DashboardTravelPage | null>(null);
  // 菜单详情弹窗（适老化大字展示）
  const [selectedMealDay, setSelectedMealDay] = useState<{
    dateStr: string;
    isToday: boolean;
    items: DashboardMealPlanItem[];
  } | null>(null);
  const [dailyQuote, setDailyQuote] = useState<string>(pickByDate(BUILT_IN_QUOTES));
  const quoteIcon = useMemo(() => pickByDate(QUOTE_ICONS), []);

  // 看板翻页：0=主页（食谱/留言），1=学习计划
  const [dashboardPage, setDashboardPage] = useState(0);
  // 学习计划日期偏移（0=今天，-1=昨天，+1=明天）
  const [scheduleDayOffset, setScheduleDayOffset] = useState(0);
  // 切换日期后独立获取的计划数据（null 表示使用 WS 推送的 today_schedule）
  const [offsetSchedule, setOffsetSchedule] = useState<TodayScheduleItem[] | null>(null);
  // 完成备注弹窗
  const [completingScheduleItem, setCompletingScheduleItem] = useState<TodayScheduleItem | null>(null);
  const [scheduleNote, setScheduleNote] = useState("");
  // 学习计划放大弹窗
  const [scheduleFullscreen, setScheduleFullscreen] = useState(false);

  // 长按修改头像
  const [avatarEditMember, setAvatarEditMember] = useState<DashboardFamilyMember | null>(null);
  const [avatarEditValue, setAvatarEditValue] = useState("");
  const [avatarSaving, setAvatarSaving] = useState(false);
  const [starWallModalOpen, setStarWallModalOpen] = useState(false);

  const openAvatarEdit = (member: DashboardFamilyMember) => {
    setAvatarEditMember(member);
    setAvatarEditValue(member.avatar);
  };

  const handleAvatarSave = async () => {
    if (!avatarEditMember || !avatarEditValue) return;
    setAvatarSaving(true);
    try {
      await updateMember(avatarEditMember.id, { avatar: avatarEditValue });
      message.success("头像已更新");
      setAvatarEditMember(null);
    } catch {
      message.error("保存头像失败");
    } finally {
      setAvatarSaving(false);
    }
  };

  // 日期偏移变化时，获取对应日期的学习计划
  useEffect(() => {
    if (scheduleDayOffset === 0) {
      setOffsetSchedule(null);
      return;
    }
    const d = new Date();
    d.setDate(d.getDate() + scheduleDayOffset);
    const dateStr = getLocalDateStr(d);
    fetchDailySchedule(dateStr)
      .then((items) => setOffsetSchedule(items as unknown as TodayScheduleItem[]))
      .catch(() => setOffsetSchedule([]));
  }, [scheduleDayOffset]);

  // ── TTS 语音播报（使用 Web Speech API，iPad SPA 兼容）──
  const autoRotateRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (ttsVersion === 0) return;
    // 如果指定了目标页面，先切换页面
    if (ttsPage !== null && ttsPage !== dashboardPage) {
      setDashboardPage(ttsPage);
    }
    // 使用 Web Speech API 播放语音（iPad 上 <audio> 无法播放，改用原生 TTS）
    try {
      window.speechSynthesis.cancel(); // 停止之前的播报
      const utter = new SpeechSynthesisUtterance(ttsText);
      utter.lang = "zh-CN";
      utter.rate = 1.0;
      utter.pitch = 1.0;
      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.warn("TTS 播放失败:", e);
    }
  }, [ttsVersion]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 远程切换页面 ──
  useEffect(() => {
    if (switchPageVersion === 0) return;
    setDashboardPage(switchPageTarget);

    // 清理之前的轮播定时器
    if (autoRotateRef.current) {
      clearInterval(autoRotateRef.current);
      autoRotateRef.current = undefined;
    }

    // 启动自动轮播
    if (autoRotate) {
      let currentPage = switchPageTarget;
      autoRotateRef.current = setInterval(() => {
        currentPage = currentPage === 0 ? 1 : 0;
        setDashboardPage(currentPage);
      }, autoRotateInterval * 1000);
    }

    return () => {
      if (autoRotateRef.current) {
        clearInterval(autoRotateRef.current);
        autoRotateRef.current = undefined;
      }
    };
  }, [switchPageVersion]); // eslint-disable-line react-hooks/exhaustive-deps

  // 用户手动操作时停止自动轮播
  useEffect(() => {
    const stopAutoRotate = () => {
      if (autoRotateRef.current) {
        clearInterval(autoRotateRef.current);
        autoRotateRef.current = undefined;
      }
    };
    // 用户点击页面导航指示器时停止轮播
    // 这里通过监听 dashboardPage 变化来判断是否用户手动切换
    // （如果是自动轮播导致的切换不会触发 stopAutoRotate，因为轮播内部直接 setState）
    return () => {
      if (autoRotateRef.current) {
        clearInterval(autoRotateRef.current);
      }
    };
  }, []);

  // 获取指定偏移日期的计划数据
  const refreshOffsetSchedule = useCallback(() => {
    if (scheduleDayOffset === 0) return;
    const d = new Date();
    d.setDate(d.getDate() + scheduleDayOffset);
    const dateStr = getLocalDateStr(d);
    fetchDailySchedule(dateStr)
      .then((items) => setOffsetSchedule(items as unknown as TodayScheduleItem[]))
      .catch(() => {});
  }, [scheduleDayOffset]);

  // ── 屏保模式 ──
  const [screensaver, setScreensaver] = useState(false);
  const idleTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // 启动/重置空闲计时器
  const resetIdleTimer = useCallback(() => {
    if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    idleTimerRef.current = setTimeout(() => setScreensaver(true), SCREENSAVER_IDLE_MS);
  }, []);

  // 用户交互（点击/触摸）唤醒屏保
  useEffect(() => {
    const handleInteraction = () => {
      setScreensaver(false);
      resetIdleTimer();
    };
    document.addEventListener("click", handleInteraction);
    document.addEventListener("touchstart", handleInteraction);
    // 启动初始计时器
    resetIdleTimer();
    return () => {
      document.removeEventListener("click", handleInteraction);
      document.removeEventListener("touchstart", handleInteraction);
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [resetIdleTimer]);

  // 非壁纸内容更新时唤醒屏保并重置计时器
  useEffect(() => {
    if (contentVersion > 0) {
      setScreensaver(false);
      resetIdleTimer();
    }
  }, [contentVersion, resetIdleTimer]);

  // ── 远程屏保控制（WS 指令）──
  useEffect(() => {
    if (screensaverVersion === 0) return;
    if (screensaverEnabled) {
      // 强制进入屏保，清除空闲计时器
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      setScreensaver(true);
    } else {
      // 强制唤醒，重启空闲计时器
      setScreensaver(false);
      resetIdleTimer();
    }
  }, [screensaverVersion, screensaverEnabled, resetIdleTimer]);

  // ── 手势滑动切换页面 ──
  const swipeStartXRef = useRef<number | null>(null);
  const swipeStartYRef = useRef<number | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const pageRefs = useRef<(HTMLDivElement | null)[]>([null, null]);

  useEffect(() => {
    const SWIPE_THRESHOLD = 60; // 最小滑动距离 (px)
    const SWIPE_MAX_VERTICAL = 80; // 垂直偏移上限，超过则不算横向滑动

    const handleTouchStart = (e: TouchEvent) => {
      // 屏保时不响应滑动
      if (screensaver) return;
      const touch = e.touches[0];
      swipeStartXRef.current = touch.clientX;
      swipeStartYRef.current = touch.clientY;
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (swipeStartXRef.current === null || swipeStartYRef.current === null) return;
      if (screensaver) return;

      const touch = e.changedTouches[0];
      const dx = touch.clientX - swipeStartXRef.current;
      const dy = touch.clientY - swipeStartYRef.current;

      swipeStartXRef.current = null;
      swipeStartYRef.current = null;

      // 垂直偏移太大，忽略
      if (Math.abs(dy) > SWIPE_MAX_VERTICAL) return;
      // 水平滑动不够，忽略
      if (Math.abs(dx) < SWIPE_THRESHOLD) return;

      // 停止自动轮播
      if (autoRotateRef.current) {
        clearInterval(autoRotateRef.current);
        autoRotateRef.current = undefined;
      }

      if (dx < 0 && dashboardPage === 0) {
        // 左滑：切换到下一页
        setDashboardPage(1);
      } else if (dx > 0 && dashboardPage === 1) {
        // 右滑：切换到上一页
        setDashboardPage(0);
      }
    };

    document.addEventListener("touchstart", handleTouchStart, { passive: true });
    document.addEventListener("touchend", handleTouchEnd, { passive: true });
    return () => {
      document.removeEventListener("touchstart", handleTouchStart);
      document.removeEventListener("touchend", handleTouchEnd);
    };
  }, [screensaver, dashboardPage]);

  // 页面切换时重置滚动位置
  useEffect(() => {
    const page = pageRefs.current[dashboardPage];
    if (page) page.scrollTop = 0;
  }, [dashboardPage]);

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

  // ── 背景图预加载 + 双层淡入淡出：避免切换时闪烁 ──
  const [bgLayers, setBgLayers] = useState<[string | null, string | null]>([null, null]);
  const [activeLayer, setActiveLayer] = useState<0 | 1>(0);
  const bgImage = data?.background_image ?? null;

  useEffect(() => {
    if (!bgImage) return;
    if (bgLayers[0] === bgImage || bgLayers[1] === bgImage) return;
    let cancelled = false;
    const img = new window.Image();
    img.onload = () => {
      if (cancelled) return;
      const next: 0 | 1 = activeLayer === 0 ? 1 : 0;
      setBgLayers((prev) => {
        const copy = [...prev] as [string | null, string | null];
        copy[next] = bgImage;
        return copy;
      });
      requestAnimationFrame(() => {
        if (!cancelled) setActiveLayer(next);
      });
    };
    img.onerror = () => {};
    img.src = bgImage;
    return () => { cancelled = true; };
  }, [bgImage]); // eslint-disable-line react-hooks/exhaustive-deps

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

  const weather = data?.weather;
  const forecast = data?.weather_forecast;

  return (
    <div style={{
      minHeight: "100vh",
      position: "relative",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif",
      overflow: "hidden",
    }}>
      {/* 全屏壁纸背景（双层淡入淡出，预加载完成后才切换） */}
      {bgLayers[0] && (
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundImage: `url(${bgLayers[0]})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          zIndex: 0,
          opacity: activeLayer === 0 ? 1 : 0,
          transition: "opacity 1s ease",
        }} />
      )}
      {bgLayers[1] && (
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundImage: `url(${bgLayers[1]})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          zIndex: 0,
          opacity: activeLayer === 1 ? 1 : 0,
          transition: "opacity 1s ease",
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

      {/* 宠物猫狗（屏保时隐藏，省电） */}
      {!screensaver && <DashboardPets />}


      {/* 内容层（屏保时渐隐） */}
      <div style={{
        position: "relative",
        zIndex: 2,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        opacity: screensaver ? 0 : 1,
        transition: "opacity 1s ease",
        pointerEvents: screensaver ? "none" : "auto",
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
              <span style={{ fontStyle: "normal", marginRight: 8 }}>{quoteIcon}</span>
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
                background: "rgba(255,255,255,0.18)",
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
                    {weather.city && (
                      <div style={{
                        fontSize: 12,
                        color: "rgba(255,255,255,0.65)",
                        display: "flex",
                        alignItems: "center",
                        gap: 3,
                        marginTop: 2,
                      }}>
                        <EnvironmentOutlined style={{ fontSize: 11 }} />
                        {weather.city}
                      </div>
                    )}
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

        {/* 内容区：dots固定 + 每页独立滚动 */}
        <div ref={scrollContainerRef} style={{
          flex: 1,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}>
        {/* 页面导航指示器 */}
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          marginBottom: 16,
          flexShrink: 0,
          padding: "20px 32px 0",
        }}>
          <button
            onClick={() => {
              if (autoRotateRef.current) { clearInterval(autoRotateRef.current); autoRotateRef.current = undefined; }
              setDashboardPage(0);
            }}
            style={{
              width: dashboardPage === 0 ? 32 : 10,
              height: 10,
              borderRadius: 5,
              border: "none",
              background: dashboardPage === 0 ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.4)",
              cursor: "pointer",
              transition: "all 0.3s ease",
            }}
          />
          <button
            onClick={() => {
              if (autoRotateRef.current) { clearInterval(autoRotateRef.current); autoRotateRef.current = undefined; }
              setDashboardPage(1);
            }}
            style={{
              width: dashboardPage === 1 ? 32 : 10,
              height: 10,
              borderRadius: 5,
              border: "none",
              background: dashboardPage === 1 ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.4)",
              cursor: "pointer",
              transition: "all 0.3s ease",
            }}
          />
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.7)", marginLeft: 8 }}>
            {dashboardPage === 0 ? "家庭看板" : "学习计划"}
          </span>
        </div>

        {/* 滑动容器：两页并排，通过 translateX 平滑切换 */}
        <div style={{ overflow: "hidden", flex: 1, minHeight: 0 }}>
        <div style={{
          display: "flex",
          width: "200%",
          height: "100%",
          transform: `translateX(-${dashboardPage * 50}%)`,
          transition: "transform 0.38s cubic-bezier(0.4, 0, 0.2, 1)",
          willChange: "transform",
        }}>
        <div ref={el => { pageRefs.current[0] = el; }} style={{ width: "50%", height: "100%", overflowY: "auto", padding: "0 32px 20px" }}>
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
                          onClick={() => setSelectedMealDay({ dateStr: day.dateStr, isToday: day.isToday, items })}
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
                            cursor: "pointer",
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
            <MessageSection
              messages={activeMessages}
              familyMembers={familyMembers}
              acknowledgeMessage={acknowledgeMessage}
              onLongPressAvatar={openAvatarEdit}
            />
          </div>
        </div>
        </div>
        <div ref={el => { pageRefs.current[1] = el; }} style={{ width: "50%", height: "100%", overflow: "hidden", padding: "0 32px 20px" }}>
        {/* 学习计划页面 */}
        <SchedulePage
          todaySchedule={offsetSchedule !== null ? offsetSchedule : (data.today_schedule || [])}
          dayOffset={scheduleDayOffset}
          onDayOffsetChange={setScheduleDayOffset}
          onStarWallClick={() => setStarWallModalOpen(true)}
          onMarkComplete={(item: TodayScheduleItem) => {
            if (item.completed === 1) {
              updateDailyItem(item.id, { completed: 0 })
                .then(() => refreshOffsetSchedule())
                .catch(() => {});
            } else {
              setCompletingScheduleItem(item);
              setScheduleNote("");
            }
          }}
          onFullscreen={() => setScheduleFullscreen(true)}
          starSummary={data.star_summary}
        />
        </div>
        </div>
        </div>
        </div>
        {/* 全屏星星墙弹窗 */}
        {starWallModalOpen && (
          <StarWallFullModal
            starSummary={data.star_summary}
            onClose={() => setStarWallModalOpen(false)}
          />
        )}

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

        {/* 每日菜单详情弹窗 —— 适老化大字展示 */}
        <Modal
          open={!!selectedMealDay}
          onCancel={() => setSelectedMealDay(null)}
          footer={null}
          width={600}
          centered
          destroyOnClose
          title={
            selectedMealDay ? (
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <CalendarOutlined style={{ fontSize: 28, color: "#7c3aed" }} />
                <span style={{ fontSize: 26, fontWeight: 700, color: "#1e293b" }}>
                  {formatWeekendDate(selectedMealDay.dateStr)}
                </span>
                {selectedMealDay.isToday && (
                  <span style={{
                    fontSize: 16,
                    background: "#7c3aed",
                    color: "#fff",
                    padding: "4px 14px",
                    borderRadius: 10,
                    fontWeight: 600,
                  }}>今天</span>
                )}
              </div>
            ) : null
          }
          styles={{
            body: {
              padding: "20px 24px 28px",
              maxHeight: "70vh",
              overflowY: "auto",
            },
          }}
        >
          {selectedMealDay && (() => {
            const byType: Record<string, typeof selectedMealDay.items> = {};
            for (const item of selectedMealDay.items) {
              if (!byType[item.meal_type]) byType[item.meal_type] = [];
              byType[item.meal_type].push(item);
            }
            return Object.entries(byType).map(([mealType, mealItems]) => {
              const config = MEAL_TYPE_CONFIG[mealType] || { label: mealType, color: "#6b7280" };
              return (
                <div key={mealType} style={{ marginBottom: 24 }}>
                  <div style={{
                    fontSize: 22,
                    fontWeight: 700,
                    color: config.color,
                    marginBottom: 14,
                    borderBottom: `2px solid ${config.color}30`,
                    paddingBottom: 8,
                  }}>
                    {config.label}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    {mealItems.map((item) => {
                      const photo = item.dish.photo;
                      return (
                        <div
                          key={item.id}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 16,
                            background: "#f8fafc",
                            borderRadius: 14,
                            padding: "12px 18px",
                            border: "1px solid #e5e7eb",
                          }}
                        >
                          {photo ? (
                            <Image
                              src={mealPhotoToUrl(photo)}
                              alt={item.dish.name}
                              width={64}
                              height={64}
                              style={{
                                borderRadius: 12,
                                objectFit: "cover",
                                flexShrink: 0,
                                border: "1px solid #e5e7eb",
                              }}
                              preview={{ src: mealPhotoToUrl(photo) }}
                              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHJ4PSIxMiIgZmlsbD0iI2YxZjVmOSIvPjwvc3ZnPg=="
                            />
                          ) : (
                            <div style={{
                              width: 64,
                              height: 64,
                              borderRadius: 12,
                              background: `${config.color}15`,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              flexShrink: 0,
                              fontSize: 30,
                            }}>
                              🍽️
                            </div>
                          )}
                          <div style={{ flex: 1 }}>
                            <div style={{
                              fontSize: 24,
                              fontWeight: 700,
                              color: "#1e293b",
                              lineHeight: 1.3,
                            }}>
                              {item.dish.name}
                            </div>
                            {item.dish.category && (
                              <span style={{
                                display: "inline-block",
                                marginTop: 4,
                                fontSize: 16,
                                color: config.color,
                                background: `${config.color}15`,
                                padding: "2px 12px",
                                borderRadius: 8,
                                fontWeight: 500,
                              }}>
                                {item.dish.category}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            });
          })()}
        </Modal>

        {/* 学习计划完成备注弹窗 */}
        <Modal
          open={!!completingScheduleItem}
          onCancel={() => setCompletingScheduleItem(null)}
          onOk={async () => {
            if (!completingScheduleItem) return;
            try {
              await updateDailyItem(completingScheduleItem.id, {
                completed: 1,
                completion_note: scheduleNote.trim() || undefined,
              });
              setCompletingScheduleItem(null);
              refreshOffsetSchedule();
            } catch {}
          }}
          okText="确认完成"
          cancelText="取消"
          title="完成备注"
        >
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">
              为 <Text strong>{completingScheduleItem?.activity_type?.icon} {completingScheduleItem?.activity_type?.name}</Text> 添加备注（可选）
            </Text>
          </div>
          <Input.TextArea
            value={scheduleNote}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setScheduleNote(e.target.value)}
            placeholder="例如：数学作业全对，语文抄写认真"
            rows={3}
            maxLength={200}
          />
        </Modal>
      </div>

      {/* 长按修改头像弹窗 */}
      <Modal
        title={`修改 ${avatarEditMember?.name || ""} 的头像`}
        open={!!avatarEditMember}
        onOk={handleAvatarSave}
        onCancel={() => setAvatarEditMember(null)}
        okText="保存"
        cancelText="取消"
        confirmLoading={avatarSaving}
        width={400}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, padding: "12px 0" }}>
          {AVATAR_OPTIONS.map((a) => (
            <div
              key={a}
              onClick={() => setAvatarEditValue(a)}
              style={{
                width: 52,
                height: 52,
                fontSize: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: 12,
                cursor: "pointer",
                border: avatarEditValue === a ? "3px solid #1677ff" : "2px solid #e5e7eb",
                background: avatarEditValue === a ? "#e6f4ff" : "#fff",
                transition: "all 0.2s",
              }}
            >
              {a}
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
}

/* ───────── memo：学习计划页 ───────── */
const SchedulePage = memo(function SchedulePage({
  todaySchedule,
  dayOffset,
  onDayOffsetChange,
  onMarkComplete,
  onFullscreen,
  onStarWallClick,
  starSummary,
}: {
  todaySchedule: TodayScheduleItem[];
  dayOffset: number;
  onDayOffsetChange: (n: number) => void;
  onMarkComplete: (item: TodayScheduleItem) => void;
  onFullscreen: () => void;
  onStarWallClick: () => void;
  starSummary: import("../types").StarSummary | undefined;
}) {
  const d = new Date();
  d.setDate(d.getDate() + dayOffset);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const dayOfWeek = d.getDay();
  const weekday = WEEKDAY_NAMES[dayOfWeek === 0 ? 6 : dayOfWeek - 1];
  const isToday = dayOffset === 0;

  return (
    <div style={{
      display: "flex",
      gap: 16,
      height: "100%",
      minHeight: 0,
    }}>
      {/* Left: Schedule list (1/3) */}
      <div style={{
        flex: 1,
        borderRadius: 16,
        padding: "16px 18px",
        background: "rgba(255,255,255,0.1)",
        backdropFilter: "blur(12px)",
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        minHeight: 0,
      }}>
        {/* Header: date + nav + fullscreen */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              icon={<LeftOutlined />}
              size="small"
              onClick={() => onDayOffsetChange(dayOffset - 1)}
              style={{ borderRadius: 8 }}
            />
            <div>
              <span style={{ fontSize: 17, fontWeight: 700, color: "#fff", textShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
                {month}月{day}日 {weekday}
              </span>
              {isToday && (
                <span style={{
                  marginLeft: 6,
                  fontSize: 11,
                  background: "#7c3aed",
                  color: "#fff",
                  padding: "1px 8px",
                  borderRadius: 6,
                  fontWeight: 600,
                }}>今天</span>
              )}
            </div>
            <Button
              icon={<RightOutlined />}
              size="small"
              onClick={() => onDayOffsetChange(dayOffset + 1)}
              style={{ borderRadius: 8 }}
            />
          </div>
          <Button
            type="text"
            icon={<span style={{ fontSize: 16 }}>⛶</span>}
            onClick={onFullscreen}
            style={{ color: "rgba(255,255,255,0.7)" }}
          />
        </div>

        {/* Activity list */}
        {todaySchedule.length === 0 ? (
          <div style={{ textAlign: "center", color: "rgba(255,255,255,0.6)", padding: "40px 0", fontSize: 15 }}>
            {isToday ? "今天暂无学习计划" : "当天暂无学习计划"}
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1, overflowY: "auto" }}>
            {todaySchedule.map((item: TodayScheduleItem) => {
              const done = item.completed === 1;
              const icon = item.activity_type?.icon || "📋";
              const name = item.activity_type?.name || "未知活动";
              const color = item.activity_type?.color || "#6b7280";
              return (
                <div
                  key={item.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    background: done ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.12)",
                    borderRadius: 12,
                    padding: "10px 12px",
                    border: `1px solid ${done ? "rgba(255,255,255,0.08)" : color + "40"}`,
                    opacity: done ? 0.6 : 1,
                    transition: "all 0.3s ease",
                    cursor: "pointer",
                  }}
                  onClick={() => onMarkComplete(item)}
                >
                  <div style={{
                    fontSize: 24,
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: done ? "rgba(255,255,255,0.05)" : color + "25",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    filter: done ? "grayscale(0.5)" : "none",
                  }}>
                    {icon}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: done ? "rgba(255,255,255,0.5)" : "#fff",
                      textDecoration: done ? "line-through" : "none",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}>
                      {name}
                    </div>
                    {done && item.completion_note && (
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        💬 {item.completion_note}
                      </div>
                    )}
                  </div>
                  <div style={{
                    width: 26,
                    height: 26,
                    borderRadius: "50%",
                    border: done ? "none" : `2px solid ${color}`,
                    background: done ? "#22c55e" : "transparent",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    transition: "all 0.3s ease",
                  }}>
                    {done && <CheckCircleFilled style={{ fontSize: 16, color: "#fff" }} />}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Right: Star Wall (2/3) */}
      <div style={{ flex: 2, minWidth: 0, height: "100%" }}>
        <StarWall starSummary={starSummary} onClick={onStarWallClick} />
      </div>
    </div>
  );
});

/* ───────── memo：留言板 ───────── */
const MessageSection = memo(function MessageSection({
  messages,
  familyMembers,
  acknowledgeMessage,
  onLongPressAvatar,
}: {
  messages: BoardMessage[];
  familyMembers: DashboardFamilyMember[];
  acknowledgeMessage: (msgId: number, memberId: number) => void;
  onLongPressAvatar: (member: DashboardFamilyMember) => void;
}) {
  return (
    <div style={{ borderRadius: 16, padding: "16px 20px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
        <MessageOutlined style={{ fontSize: 22, color: "#fb923c" }} />
        <Text strong style={{ fontSize: 20, color: "#fff", textShadow: "0 1px 4px rgba(0,0,0,0.3)" }}>家庭留言</Text>
      </div>

      {messages.length === 0 ? (
        <div style={{ textAlign: "center", color: "rgba(255,255,255,0.6)", padding: "40px 0", fontSize: 16 }}>
          暂无留言
        </div>
      ) : (
        messages.map((msg: BoardMessage) => {
          const authorName = msg.author || "匿名";
          const initial = authorName.charAt(0).toUpperCase();
          const avatarBg = getAvatarColor(authorName);
          const isPinned = !!msg.pinned;
          const cardColor = resolveColor(msg.color);
          const cardBg = isPinned ? "#fffbeb" : tintBackground(cardColor, 0.35);

          return (
            <div
              key={msg.id}
              style={{
                background: cardBg,
                borderLeft: `8px solid ${cardColor}`,
                borderRadius: 16,
                padding: isPinned ? "16px 18px" : "14px 16px",
                marginBottom: 12,
                boxShadow: isPinned
                  ? "0 4px 16px rgba(0,0,0,0.1)"
                  : "0 2px 8px rgba(0,0,0,0.05)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
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
                  <span style={{ fontSize: 15, fontWeight: 600, color: "#334155" }}>{authorName}</span>
                  <span style={{ fontSize: 14, color: "#64748b", marginLeft: 6 }}>留言说</span>
                </div>
                {isPinned && <PushpinOutlined style={{ fontSize: 16, color: "#f59e0b" }} />}
              </div>

              <div style={{
                fontSize: 16, lineHeight: 1.6, color: "#1e293b",
                whiteSpace: "pre-wrap", wordBreak: "break-word",
                marginBottom: 10, paddingLeft: isPinned ? 50 : 46,
              }}>
                {msg.content}
              </div>

              <div style={{ fontSize: 12, color: "#94a3b8", paddingLeft: isPinned ? 50 : 46, marginBottom: 8 }}>
                {formatBoardDateTime(msg.created_at)}
                {msg.expires_at && (
                  <span style={{ marginLeft: 12, opacity: 0.7 }}>
                    有效期至 {new Date(msg.expires_at).toLocaleDateString("zh-CN")}
                  </span>
                )}
              </div>

              {familyMembers.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, paddingLeft: isPinned ? 50 : 46 }}>
                  {familyMembers.map((member) => {
                    const isAcked = msg.acknowledged_by?.includes(member.id);
                    let lpTimer: ReturnType<typeof setTimeout> | null = null;
                    let lpFired = false;
                    return (
                      <button
                        key={member.id}
                        onClick={(e) => {
                          if (lpFired) { e.preventDefault(); e.stopPropagation(); lpFired = false; }
                          else acknowledgeMessage(msg.id, member.id);
                        }}
                        onPointerDown={(e) => {
                          e.preventDefault();
                          lpFired = false;
                          lpTimer = setTimeout(() => { lpFired = true; onLongPressAvatar(member); }, 500);
                        }}
                        onPointerUp={() => { if (lpTimer) clearTimeout(lpTimer); lpTimer = null; }}
                        onPointerLeave={() => { if (lpTimer) clearTimeout(lpTimer); lpTimer = null; }}
                        style={{
                          display: "flex", alignItems: "center", gap: 4,
                          padding: "3px 10px", borderRadius: 12,
                          border: isAcked ? "1px solid #22c55e" : "1px solid #e5e7eb",
                          background: isAcked ? "#dcfce7" : "#f8fafc",
                          color: isAcked ? "#15803d" : "#64748b",
                          fontSize: 12, fontWeight: 500, cursor: "pointer",
                          lineHeight: 1, userSelect: "none", WebkitTouchCallout: "none",
                        }}
                      >
                        <span style={{ fontSize: 14 }}>{member.avatar}</span>
                        <span>{member.name}</span>
                        {isAcked && <CheckCircleFilled style={{ fontSize: 12, color: "#22c55e" }} />}
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
  );
});
