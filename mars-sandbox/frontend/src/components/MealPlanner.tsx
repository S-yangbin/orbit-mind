import { useEffect, useState, useMemo, useCallback } from "react";
import {
  Button,
  Card,
  Space,
  Tag,
  Popover,
  Select,
  message,
  Spin,
  Typography,
  Empty,
  Divider,
  Image,
} from "antd";
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  SwapOutlined,
  HistoryOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import type { MealPlan, MealPlanItem, Dish } from "../types";
import {
  fetchCurrentPlans,
  generatePlan,
  confirmPlan,
  removePlanItem,
  replacePlanItem,
  addPlanItem,
  fetchDishes,
} from "../api/meals";
import { useIsMobile } from "../hooks/useIsMobile";
import { mealPhotoToUrl } from "../utils";

const { Text, Title } = Typography;

const DAY_NAMES: Record<number, string> = { 6: "周六", 0: "周日" };
const MEAL_LABELS: Record<string, string> = {
  lunch: "午餐（全家）",
};

/** Category → subtle color for dish chips */
const CATEGORY_COLORS: Record<string, string> = {
  荤菜: "#fef3c7",
  素菜: "#dcfce7",
  凉菜: "#e0e7ff",
  汤: "#fce7f3",
  主食: "#fff7ed",
};

function getDayOfWeek(dateStr: string): number {
  return new Date(dateStr + "T00:00:00").getDay();
}

function getDay(dateStr: string): number {
  return new Date(dateStr + "T00:00:00").getDate();
}

function getMonthDay(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function getMonthKey(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function getMonthLabel(monthKey: string): string {
  const [year, month] = monthKey.split("-");
  return `${year}年${parseInt(month)}月`;
}

function isPastDate(dateStr: string): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(dateStr + "T00:00:00");
  return d < today;
}

function isToday(dateStr: string): boolean {
  const today = new Date();
  const d = new Date(dateStr + "T00:00:00");
  return d.toDateString() === today.toDateString();
}


interface WeekData {
  plan: MealPlan;
  dates: string[];
  itemsBySlot: Record<string, MealPlanItem[]>;
}

export function MealPlanner() {
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [replaceItem, setReplaceItem] = useState<MealPlanItem | null>(null);
  const [addTarget, setAddTarget] = useState<{ date: string; meal_type: string } | null>(null);
  const [datePhotos, setDatePhotos] = useState<Record<string, string>>({});
  const [refreshing, setRefreshing] = useState(false);
  const isMobile = useIsMobile();

  const loadData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    try {
      const { plans: plansData, datePhotos: photos } = await fetchCurrentPlans();
      const dishData = await fetchDishes(1, 200);
      setPlans(plansData);
      setDishes(dishData.items);
      setDatePhotos(photos);
    } catch {
      message.error("加载菜单失败");
    } finally {
      setLoading(false);
      if (showRefreshing) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh when the tab becomes visible again
  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        loadData(true);
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [loadData]);

  const handleRefresh = () => loadData(true);

  // Group plans by month
  const weeksByMonth = useMemo(() => {
    const result: Record<string, WeekData[]> = {};
    for (const plan of plans) {
      const itemsBySlot: Record<string, MealPlanItem[]> = {};
      const dateSet = new Set<string>();

      for (const item of plan.items) {
        const day = getDayOfWeek(item.date);
        if (day === 0 || day === 6) {
          dateSet.add(item.date);
          const key = `${item.date}_${item.meal_type}`;
          if (!itemsBySlot[key]) itemsBySlot[key] = [];
          itemsBySlot[key].push(item);
        }
      }

      Object.values(itemsBySlot).forEach((arr) =>
        arr.sort((a, b) => a.sort_order - b.sort_order)
      );

      const sortedDates = Array.from(dateSet).sort();
      if (sortedDates.length === 0) continue;

      const monthKey = getMonthKey(sortedDates[0]);
      if (!result[monthKey]) result[monthKey] = [];
      result[monthKey].push({ plan, dates: sortedDates, itemsBySlot });
    }

    // Sort weeks within each month
    Object.values(result).forEach((weeks) =>
      weeks.sort((a, b) => a.dates[0].localeCompare(b.dates[0]))
    );

    return result;
  }, [plans]);

  // Sort month keys: past months first, then future
  const sortedMonthKeys = useMemo(() => {
    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
    return Object.keys(weeksByMonth).sort((a, b) => {
      // Past months first (descending), then current/future (ascending)
      const aPast = a < currentMonth;
      const bPast = b < currentMonth;
      if (aPast && bPast) return b.localeCompare(a);
      if (aPast && !bPast) return -1;
      if (!aPast && bPast) return 1;
      return a.localeCompare(b);
    });
  }, [weeksByMonth]);

  const hasDraft = plans.some((p) => p.status === "draft");
  const hasFutureDraft = plans.some(
    (p) => p.status === "draft" && p.items.some((i) => !isPastDate(i.date))
  );

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generatePlan();
      await loadData();
      message.success("未来一个月周末菜单生成成功！可以手动调整后确认");
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || "AI 生成菜单失败，请稍后重试");
    } finally {
      setGenerating(false);
    }
  };

  const handleConfirm = async () => {
    try {
      await confirmPlan();
      setPlans((prev) => prev.map((p) => ({ ...p, status: "confirmed" as const })));
      message.success("菜单已确认");
    } catch {
      message.error("确认失败");
    }
  };

  const handleRemove = async (itemId: number) => {
    if (itemId < 0) {
      message.warning("历史记录无法移除");
      return;
    }
    try {
      await removePlanItem(itemId);
      setPlans((prev) =>
        prev.map((p) => ({ ...p, items: p.items.filter((i) => i.id !== itemId) }))
      );
      message.success("已移除");
    } catch {
      message.error("移除失败");
    }
  };

  const handleReplace = async (dishId: number) => {
    if (!replaceItem || replaceItem.id < 0) return;
    try {
      await replacePlanItem(replaceItem.id, dishId);
      await loadData();
      setReplaceItem(null);
      message.success("已替换");
    } catch {
      message.error("替换失败");
    }
  };

  const handleAdd = async (dishId: number) => {
    if (!addTarget) return;
    try {
      await addPlanItem(addTarget.date, addTarget.meal_type, dishId);
      await loadData();
      setAddTarget(null);
      message.success("已添加");
    } catch {
      message.error("添加失败");
    }
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "80px auto" }} />;

  const dishSelector = (onSelect: (id: number) => void) => (
    <Select
      showSearch
      placeholder="搜索菜品..."
      style={{ width: 200 }}
      optionFilterProp="label"
      onChange={onSelect}
      options={dishes.map((d) => ({
        value: d.id,
        label: `${d.name} (${d.category})`,
      }))}
    />
  );

  const dishPopover = (item: MealPlanItem, isPast: boolean) => {
    return (
      <div style={{ maxWidth: 280 }}>
        <Text strong>{item.dish.name}</Text>
        <Tag style={{ marginLeft: 8, borderRadius: 10 }}>{item.dish.category}</Tag>
        {item.source === "log" && (
          <Tag color="green" style={{ marginLeft: 4, borderRadius: 10 }}>
            <HistoryOutlined /> 实际
          </Tag>
        )}
        {item.dish.recipe && (
          <div style={{ marginTop: 8, fontSize: 12, color: "#64748b" }}>
            {item.dish.recipe}
          </div>
        )}
        {!isPast && item.id > 0 && (
          <div style={{ marginTop: 8, display: "flex", gap: 4 }}>
            <Button
              size="small"
              icon={<SwapOutlined />}
              onClick={() => setReplaceItem(item)}
              style={{ borderRadius: 6 }}
            >
              替换
            </Button>
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleRemove(item.id)}
              style={{ borderRadius: 6 }}
            >
              移除
            </Button>
          </div>
        )}
      </div>
    );
  };

  const renderWeekCard = (weekData: WeekData, isPastMonth: boolean) => {
    const { plan, dates, itemsBySlot } = weekData;

    return dates.map((dateStr: string) => {
      const dayOfWeek = getDayOfWeek(dateStr);
      const dayNum = getDay(dateStr);
      const lunchItems = itemsBySlot[`${dateStr}_lunch`] || [];
      const isPast = isPastDate(dateStr);
      const today = isToday(dateStr);
      const isLogOnly = plan.status === "log";
      const photoUrl = datePhotos[dateStr] ? mealPhotoToUrl(datePhotos[dateStr]) : null;

      return (
        <div
          key={dateStr}
          style={{
            display: "flex",
            gap: isMobile ? 10 : 14,
            padding: isMobile ? "12px 10px" : "14px 16px",
            borderRadius: 14,
            background: isPast
              ? "#fafafa"
              : today
              ? "linear-gradient(135deg, #fffbeb 0%, #fef9c3 100%)"
              : "#fff",
            border: today
              ? "1.5px solid #f59e0b"
              : isPast
              ? "1px solid #f0f0f0"
              : "1px solid #f5f5f5",
            boxShadow: isPast
              ? "none"
              : "0 1px 3px rgba(0,0,0,0.04)",
            transition: "box-shadow 0.2s, border-color 0.2s",
            cursor: "default",
          }}
        >
          {/* Date badge */}
          <div
            style={{
              flexShrink: 0,
              width: isMobile ? 48 : 56,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
            }}
          >
            <div
              style={{
                width: isMobile ? 44 : 52,
                height: isMobile ? 44 : 52,
                borderRadius: 14,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                background: today
                  ? "#f59e0b"
                  : isPast
                  ? "#e5e7eb"
                  : dayOfWeek === 6
                  ? "linear-gradient(135deg, #fbbf24, #f59e0b)"
                  : "linear-gradient(135deg, #a78bfa, #8b5cf6)",
                color: "#fff",
                fontWeight: 800,
                fontSize: isMobile ? 20 : 24,
                lineHeight: 1,
              }}
            >
              {dayNum}
            </div>
            <Text
              style={{
                fontSize: 11,
                color: isPast ? "#9ca3af" : today ? "#f59e0b" : "#6b7280",
                fontWeight: 600,
                letterSpacing: 0.5,
              }}
            >
              {DAY_NAMES[dayOfWeek] || "周末"}
            </Text>
            <Text style={{ fontSize: 10, color: "#9ca3af" }}>
              {getMonthDay(dateStr)}
            </Text>
          </div>

          {/* Content */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Status bar */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 8,
              }}
            >
              <Text
                style={{
                  fontSize: 12,
                  color: isPast ? "#9ca3af" : "#78716c",
                  fontWeight: 500,
                }}
              >
                {MEAL_LABELS.lunch}
              </Text>
              {isPast && (
                <Tag
                  color={isLogOnly ? "default" : "green"}
                  style={{ borderRadius: 10, fontSize: 10, lineHeight: "18px", margin: 0 }}
                >
                  {isLogOnly ? "已记录" : "已确认"}
                </Tag>
              )}
            </div>

            {/* Photo thumbnail + Dish chips row */}
            <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
              {/* Meal photo thumbnail */}
              {photoUrl && (
                <Image
                  src={photoUrl}
                  alt={`${dateStr} 午餐`}
                  width={isMobile ? 56 : 64}
                  height={isMobile ? 56 : 64}
                  style={{
                    borderRadius: 8,
                    objectFit: "cover",
                    flexShrink: 0,
                    border: "1px solid #e5e7eb",
                  }}
                  preview={{ src: photoUrl }}
                  fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIGZpbGw9IiNmM2Y0ZjYiLz48dGV4dCB4PSIzMiIgeT0iMzYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM5Y2EzYWYiIGZvbnQtc2l6ZT0iMTIiPjwvdGV4dD48L3N2Zz4="
                />
              )}

              {/* Dish chips */}
              <div style={{ flex: 1, display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                {lunchItems.map((item) => {
                  const catColor = CATEGORY_COLORS[item.dish.category] || "#f3f4f6";
                  return (
                    <Popover
                      key={item.id}
                      content={dishPopover(item, isPast)}
                      trigger="click"
                      placement="bottom"
                    >
                      <Tag
                        style={{
                          cursor: "pointer",
                          borderRadius: 8,
                          border: "none",
                          background: item.source === "log" ? "#dcfce7" : catColor,
                          color: isPast ? "#6b7280" : "#374151",
                          fontSize: 13,
                          padding: "2px 10px",
                          lineHeight: "24px",
                          fontWeight: 500,
                          transition: "opacity 0.15s",
                        }}
                      >
                        {item.dish.name}
                      </Tag>
                    </Popover>
                  );
                })}
                {!isPast && (
                  <div
                    style={{
                      width: 26,
                      height: 26,
                      borderRadius: 8,
                      border: "1px dashed #d1d5db",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      color: "#9ca3af",
                      transition: "border-color 0.15s, color 0.15s",
                    }}
                    onClick={() => setAddTarget({ date: dateStr, meal_type: "lunch" })}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = "#f59e0b";
                      e.currentTarget.style.color = "#f59e0b";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = "#d1d5db";
                      e.currentTarget.style.color = "#9ca3af";
                    }}
                  >
                    <PlusOutlined style={{ fontSize: 12 }} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    });
  };

  return (
    <div>
      {/* Action buttons */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 16,
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <Space wrap>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={generating}
            onClick={handleGenerate}
            style={{ borderRadius: 8, fontWeight: 500 }}
          >
            AI 生成未来一个月菜单
          </Button>
          {hasFutureDraft && (
            <Button
              icon={<CheckCircleOutlined />}
              onClick={handleConfirm}
              style={{ borderRadius: 8 }}
            >
              确认菜单
            </Button>
          )}
        </Space>
        <Button
          icon={<ReloadOutlined spin={refreshing} />}
          onClick={handleRefresh}
          loading={refreshing}
          style={{ borderRadius: 8 }}
        >
          刷新
        </Button>
      </div>

      {sortedMonthKeys.length === 0 ? (
        <Empty description="还没有周末菜单，点击「AI 生成」开始规划" style={{ padding: "60px 0" }} />
      ) : (
        <div>
          {sortedMonthKeys.map((monthKey, idx) => {
            const weeks = weeksByMonth[monthKey];
            const today = new Date();
            const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
            const isPastMonth = monthKey < currentMonth;

            return (
              <div key={monthKey} style={{ marginBottom: 24 }}>
                {idx > 0 && <Divider style={{ margin: "16px 0" }} />}

                {/* Month header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 12,
                  }}
                >
                  <Title level={4} style={{ margin: 0, color: isPastMonth ? "#9ca3af" : "#78350f" }}>
                    {getMonthLabel(monthKey)}
                  </Title>
                  {isPastMonth && (
                    <Tag
                      icon={<HistoryOutlined />}
                      color="default"
                      style={{ borderRadius: 10 }}
                    >
                      历史记录
                    </Tag>
                  )}
                </div>

                {/* Week cards grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: isMobile
                      ? "1fr"
                      : "repeat(auto-fill, minmax(320px, 1fr))",
                    gap: isMobile ? 8 : 12,
                  }}
                >
                  {weeks.map((weekData) => renderWeekCard(weekData, isPastMonth))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Replace Modal */}
      {replaceItem && replaceItem.id > 0 && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.3)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 16,
          }}
          onClick={() => setReplaceItem(null)}
        >
          <Card
            title={`替换: ${replaceItem.dish.name}`}
            style={{ width: "100%", maxWidth: 320, borderRadius: 12 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Text style={{ display: "block", marginBottom: 8, color: "#64748b" }}>
              选择新菜品:
            </Text>
            {dishSelector(handleReplace)}
          </Card>
        </div>
      )}

      {/* Add Modal */}
      {addTarget && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.3)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 16,
          }}
          onClick={() => setAddTarget(null)}
        >
          <Card
            title={`添加菜品 - ${MEAL_LABELS[addTarget.meal_type]}`}
            style={{ width: "100%", maxWidth: 320, borderRadius: 12 }}
            onClick={(e) => e.stopPropagation()}
          >
            {dishSelector(handleAdd)}
          </Card>
        </div>
      )}
    </div>
  );
}
