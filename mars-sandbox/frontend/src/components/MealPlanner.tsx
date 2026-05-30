import { useEffect, useState, useMemo } from "react";
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
} from "antd";
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  SwapOutlined,
  SunOutlined,
  MoonOutlined,
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

const { Text, Title } = Typography;

const DAY_NAMES: Record<number, string> = { 6: "周六", 0: "周日" };
const MEAL_LABELS: Record<string, string> = {
  lunch: "午餐（全家）",
  dinner: "晚餐（孩子）",
};
const MEAL_ICONS: Record<string, React.ReactNode> = {
  lunch: <SunOutlined style={{ color: "#f59e0b" }} />,
  dinner: <MoonOutlined style={{ color: "#8b5cf6" }} />,
};

function getDayOfWeek(dateStr: string): number {
  return new Date(dateStr + "T00:00:00").getDay();
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

export function MealPlanner() {
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [replaceItem, setReplaceItem] = useState<MealPlanItem | null>(null);
  const [addTarget, setAddTarget] = useState<{ date: string; meal_type: string } | null>(null);
  const isMobile = useIsMobile();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [plansData, dishData] = await Promise.all([
        fetchCurrentPlans(),
        fetchDishes(1, 200),
      ]);
      setPlans(plansData);
      setDishes(dishData.items);
    } catch {
      message.error("加载菜单失败");
    } finally {
      setLoading(false);
    }
  };

  const allWeekendDates = useMemo(() => {
    const dateSet = new Set<string>();
    for (const plan of plans) {
      for (const item of plan.items) {
        const day = getDayOfWeek(item.date);
        if (day === 0 || day === 6) {
          dateSet.add(item.date);
        }
      }
    }
    return Array.from(dateSet).sort();
  }, [plans]);

  const hasDraft = plans.some((p) => p.status === "draft");

  const itemsBySlot = useMemo(() => {
    const map: Record<string, MealPlanItem[]> = {};
    for (const plan of plans) {
      for (const item of plan.items) {
        const key = `${item.date}_${item.meal_type}`;
        if (!map[key]) map[key] = [];
        map[key].push(item);
      }
    }
    Object.values(map).forEach((arr) => arr.sort((a, b) => a.sort_order - b.sort_order));
    return map;
  }, [plans]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generatePlan();
      const allPlans = await fetchCurrentPlans();
      setPlans(allPlans);
      message.success("未来一个月周末菜单生成成功！可以手动调整后确认");
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "AI 生成菜单失败，请稍后重试");
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
    if (!replaceItem) return;
    try {
      await replacePlanItem(replaceItem.id, dishId);
      loadData();
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
      loadData();
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

  const dishPopover = (item: MealPlanItem) => {
    return (
      <div style={{ maxWidth: 280 }}>
        <Text strong>{item.dish.name}</Text>
        <Tag style={{ marginLeft: 8, borderRadius: 10 }}>{item.dish.category}</Tag>
        {item.dish.recipe && (
          <div style={{ marginTop: 8, fontSize: 12, color: "#64748b" }}>
            {item.dish.recipe}
          </div>
        )}
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
      </div>
    );
  };

  return (
    <div>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        marginBottom: 16,
        flexWrap: "wrap",
        gap: 8,
      }}>
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
          {hasDraft && (
            <Button
              icon={<CheckCircleOutlined />}
              onClick={handleConfirm}
              style={{ borderRadius: 8 }}
            >
              确认菜单
            </Button>
          )}
        </Space>
      </div>

      {allWeekendDates.length === 0 ? (
        <Empty description="还没有周末菜单，点击「AI 生成」开始规划" style={{ padding: "60px 0" }} />
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: isMobile
            ? "1fr"
            : "repeat(auto-fill, minmax(280px, 1fr))",
          gap: isMobile ? 10 : 14,
        }}>
          {allWeekendDates.map((dateStr: string) => {
            const dayOfWeek = getDayOfWeek(dateStr);
            const lunchItems = itemsBySlot[`${dateStr}_lunch`] || [];
            const dinnerItems = itemsBySlot[`${dateStr}_dinner`] || [];

            return (
              <Card
                key={dateStr}
                size="small"
                style={{
                  borderRadius: 12,
                  border: "1px solid #fef3c7",
                  background: "#fffbeb",
                }}
                styles={{ body: { padding: "12px 14px" } }}
              >
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 10,
                  paddingBottom: 8,
                  borderBottom: "1px solid #fef3c7",
                }}>
                  <Title level={5} style={{ margin: 0, fontWeight: 700, fontSize: 15 }}>
                    {DAY_NAMES[dayOfWeek] || "周末"}
                  </Title>
                  <Text style={{ fontSize: 13, color: "#92400e" }}>
                    {formatDate(dateStr)}
                  </Text>
                </div>

                {/* Lunch section */}
                <div style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    {MEAL_ICONS.lunch}
                    <Text style={{ fontSize: 12, color: "#78716c", fontWeight: 500 }}>
                      {MEAL_LABELS.lunch}
                    </Text>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, alignItems: "center" }}>
                    {lunchItems.map((item) => (
                      <Popover
                        key={item.id}
                        content={dishPopover(item)}
                        trigger="click"
                        placement="bottom"
                      >
                        <Tag
                          style={{
                            cursor: "pointer",
                            borderRadius: 10,
                            border: item.is_manual ? "1px solid #8b5cf6" : undefined,
                          }}
                          color={item.is_manual ? "purple" : undefined}
                        >
                          {item.dish.name}
                        </Tag>
                      </Popover>
                    ))}
                    <Button
                      type="text"
                      size="small"
                      style={{
                        fontSize: 14,
                        color: "#d4d4d8",
                        padding: "0 4px",
                        minWidth: 24,
                        height: 24,
                        borderRadius: 6,
                      }}
                      onClick={() => setAddTarget({ date: dateStr, meal_type: "lunch" })}
                    >
                      +
                    </Button>
                  </div>
                </div>

                {/* Dinner section */}
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    {MEAL_ICONS.dinner}
                    <Text style={{ fontSize: 12, color: "#78716c", fontWeight: 500 }}>
                      {MEAL_LABELS.dinner}
                    </Text>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, alignItems: "center" }}>
                    {dinnerItems.map((item) => (
                      <Popover
                        key={item.id}
                        content={dishPopover(item)}
                        trigger="click"
                        placement="bottom"
                      >
                        <Tag
                          style={{
                            cursor: "pointer",
                            borderRadius: 10,
                            border: item.is_manual ? "1px solid #8b5cf6" : undefined,
                          }}
                          color={item.is_manual ? "purple" : undefined}
                        >
                          {item.dish.name}
                        </Tag>
                      </Popover>
                    ))}
                    <Button
                      type="text"
                      size="small"
                      style={{
                        fontSize: 14,
                        color: "#d4d4d8",
                        padding: "0 4px",
                        minWidth: 24,
                        height: 24,
                        borderRadius: 6,
                      }}
                      onClick={() => setAddTarget({ date: dateStr, meal_type: "dinner" })}
                    >
                      +
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Replace Modal */}
      {replaceItem && (
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
