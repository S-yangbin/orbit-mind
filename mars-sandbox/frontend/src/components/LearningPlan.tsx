import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Card,
  Button,
  Input,
  Select,
  Space,
  Popconfirm,
  Empty,
  Spin,
  message,
  Typography,
  Modal,
  Tag,
  Divider,
  ColorPicker,
  Badge,
  Tooltip,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  CheckCircleFilled,
  CheckCircleOutlined,
  CalendarOutlined,
  LeftOutlined,
  RightOutlined,
  SettingOutlined,
  EditOutlined,
} from "@ant-design/icons";
import {
  fetchActivityTypes,
  createActivityType,
  deleteActivityType,
  fetchActiveTemplate,
  createOrUpdateTemplate,
  fetchDailyRange,
  addDailyItem,
  updateDailyItem,
  deleteDailyItem,
} from "../api/schedule";
import type {
  ActivityType,
  WeeklyTemplate,
  WeeklyTemplateDayItem,
  DailyScheduleItem,
} from "../types";
import dayjs from "dayjs";

const { Text, Title } = Typography;

const WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"];

// 预设活动类型 emoji 选项
const EMOJI_OPTIONS = ["📚", "📝", "🎨", "🏀", "♟️", "🎹", "🎮", "🧩", "✏️", "🏃", "⚽", "🎯", "🎭", "🧮", "📖", "🌟"];

function getLocalDateStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** 获取指定月份日历网格（包含前后补齐的其他月份日期） */
function getMonthGrid(year: number, month: number): { dateStr: string; day: number; isCurrentMonth: boolean }[] {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  // 周一=0 ... 周日=6
  const startDow = (firstDay.getDay() + 6) % 7;
  const daysInMonth = lastDay.getDate();

  const grid: { dateStr: string; day: number; isCurrentMonth: boolean }[] = [];

  // 上月补齐
  const prevMonthLastDay = new Date(year, month, 0).getDate();
  for (let i = startDow - 1; i >= 0; i--) {
    const d = prevMonthLastDay - i;
    const dt = new Date(year, month - 1, d);
    grid.push({ dateStr: getLocalDateStr(dt), day: d, isCurrentMonth: false });
  }

  // 本月
  for (let d = 1; d <= daysInMonth; d++) {
    const dt = new Date(year, month, d);
    grid.push({ dateStr: getLocalDateStr(dt), day: d, isCurrentMonth: true });
  }

  // 下月补齐（补到 6 行 = 42 格，或至少补完当前行）
  const remaining = (7 - (grid.length % 7)) % 7;
  for (let d = 1; d <= remaining; d++) {
    const dt = new Date(year, month + 1, d);
    grid.push({ dateStr: getLocalDateStr(dt), day: d, isCurrentMonth: false });
  }

  return grid;
}

export function LearningPlan() {
  // State
  const [activityTypes, setActivityTypes] = useState<ActivityType[]>([]);
  const [template, setTemplate] = useState<WeeklyTemplate | null>(null);
  const [loading, setLoading] = useState(false);

  // 当前查看月份
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth()); // 0-11

  // 选中的日期
  const [selectedDate, setSelectedDate] = useState<string>(getLocalDateStr(today));

  // 月度全部数据
  const [monthItems, setMonthItems] = useState<DailyScheduleItem[]>([]);

  // Add activity modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newActivityTypeId, setNewActivityTypeId] = useState<number | null>(null);

  // Completion note modal
  const [completingItem, setCompletingItem] = useState<DailyScheduleItem | null>(null);
  const [completionNote, setCompletionNote] = useState("");

  // Activity type management modal
  const [showTypeModal, setShowTypeModal] = useState(false);
  const [newTypeName, setNewTypeName] = useState("");
  const [newTypeIcon, setNewTypeIcon] = useState("📚");
  const [newTypeColor, setNewTypeColor] = useState("#4A90D9");
  const [newTypeCategory, setNewTypeCategory] = useState("custom");

  // Template edit modal
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateEditDays, setTemplateEditDays] = useState<WeeklyTemplateDayItem[]>([]);

  // 按月分组
  const itemsByDate = useMemo(() => {
    const map: Record<string, DailyScheduleItem[]> = {};
    for (const item of monthItems) {
      if (!map[item.date]) map[item.date] = [];
      map[item.date].push(item);
    }
    return map;
  }, [monthItems]);

  // 日历网格
  const monthGrid = useMemo(() => getMonthGrid(viewYear, viewMonth), [viewYear, viewMonth]);
  const todayStr = getLocalDateStr(new Date());

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const firstDay = new Date(viewYear, viewMonth, 1);
      const lastDay = new Date(viewYear, viewMonth + 1, 0);
      const startDow = (firstDay.getDay() + 6) % 7;
      // 扩展范围包含上月补齐日期
      const rangeStart = new Date(firstDay);
      rangeStart.setDate(rangeStart.getDate() - startDow);
      // 扩展到周六结尾
      const endDow = (lastDay.getDay() + 6) % 7;
      const rangeEnd = new Date(lastDay);
      rangeEnd.setDate(rangeEnd.getDate() + (6 - endDow));

      const [types, tpl, items] = await Promise.all([
        fetchActivityTypes(),
        fetchActiveTemplate(),
        fetchDailyRange(getLocalDateStr(rangeStart), getLocalDateStr(rangeEnd)),
      ]);
      setActivityTypes(types);
      setTemplate(tpl);
      setMonthItems(items);
    } catch (e) {
      console.error("Failed to load schedule data:", e);
      message.error("加载数据失败");
    }
    setLoading(false);
  }, [viewYear, viewMonth]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Navigation
  const navigateMonth = (delta: number) => {
    let m = viewMonth + delta;
    let y = viewYear;
    if (m < 0) { m = 11; y--; }
    if (m > 11) { m = 0; y++; }
    setViewYear(y);
    setViewMonth(m);
  };

  const goThisMonth = () => {
    const t = new Date();
    setViewYear(t.getFullYear());
    setViewMonth(t.getMonth());
  };

  // Add activity
  const handleAddItem = async () => {
    if (!newActivityTypeId) {
      message.warning("请选择活动类型");
      return;
    }
    try {
      await addDailyItem({
        date: selectedDate,
        activity_type_id: newActivityTypeId,
      });
      message.success("活动已添加");
      setShowAddModal(false);
      setNewActivityTypeId(null);
      await loadData();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "添加失败");
    }
  };

  // Mark complete
  const handleMarkComplete = (item: DailyScheduleItem) => {
    if (item.completed === 1) {
      updateDailyItem(item.id, { completed: 0, completion_note: "" })
        .then(() => {
          message.success("已取消完成");
          loadData();
        })
        .catch(() => message.error("操作失败"));
    } else {
      setCompletingItem(item);
      setCompletionNote("");
    }
  };

  const handleConfirmComplete = async () => {
    if (!completingItem) return;
    try {
      await updateDailyItem(completingItem.id, {
        completed: 1,
        completion_note: completionNote.trim() || null as any,
      });
      message.success("已完成！");
      setCompletingItem(null);
      await loadData();
    } catch {
      message.error("操作失败");
    }
  };

  // Delete item
  const handleDeleteItem = async (id: number) => {
    try {
      await deleteDailyItem(id);
      message.success("已删除");
      await loadData();
    } catch {
      message.error("删除失败");
    }
  };

  // Create activity type
  const handleCreateType = async () => {
    if (!newTypeName.trim()) {
      message.warning("请输入活动名称");
      return;
    }
    try {
      await createActivityType({
        name: newTypeName.trim(),
        icon: newTypeIcon,
        color: newTypeColor,
        category: newTypeCategory,
      });
      message.success("活动类型已创建");
      setNewTypeName("");
      setNewTypeIcon("📚");
      setNewTypeColor("#4A90D9");
      const types = await fetchActivityTypes();
      setActivityTypes(types);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "创建失败");
    }
  };

  // Delete activity type
  const handleDeleteType = async (id: number) => {
    try {
      await deleteActivityType(id);
      message.success("已删除");
      const types = await fetchActivityTypes();
      setActivityTypes(types);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "删除失败");
    }
  };

  // Open template edit modal
  const openTemplateEditor = () => {
    const initialDays = template?.days ? [...template.days] : [];
    setTemplateEditDays(initialDays);
    setShowTemplateModal(true);
  };

  const addTemplateDay = (dayOfWeek: number, activityTypeId: number) => {
    const sortOrder = templateEditDays.filter(d => d.day_of_week === dayOfWeek).length;
    setTemplateEditDays([...templateEditDays, { day_of_week: dayOfWeek, activity_type_id: activityTypeId, sort_order: sortOrder }]);
  };

  const removeTemplateDay = (index: number) => {
    setTemplateEditDays(templateEditDays.filter((_, i) => i !== index));
  };

  const handleSaveTemplate = async () => {
    try {
      await createOrUpdateTemplate({ name: "默认周计划", days: templateEditDays });
      message.success("周模板已保存");
      setShowTemplateModal(false);
      const tpl = await fetchActiveTemplate();
      setTemplate(tpl);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "保存失败");
    }
  };

  const selectedDateObj = new Date(selectedDate);
  const isCurrentMonth = viewYear === today.getFullYear() && viewMonth === today.getMonth();
  const monthLabel = `${viewYear}年${viewMonth + 1}月`;

  // 选中日期的数据
  const selectedDayItems = itemsByDate[selectedDate] || [];

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "24px 16px" }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 28,
        padding: "20px 24px",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        borderRadius: 16,
        boxShadow: "0 4px 20px rgba(102, 126, 234, 0.3)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 32 }}>📚</span>
          <Title level={3} style={{ margin: 0, color: "#fff", textShadow: "0 1px 4px rgba(0,0,0,0.15)" }}>学习计划</Title>
        </div>
        <Space size={12}>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setShowTypeModal(true)}
            style={{ borderRadius: 8, background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.3)", color: "#fff", backdropFilter: "blur(4px)" }}
          >
            活动类型
          </Button>
          <Button
            icon={<EditOutlined />}
            onClick={openTemplateEditor}
            style={{ borderRadius: 8, background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.3)", color: "#fff", backdropFilter: "blur(4px)" }}
          >
            周模板
          </Button>
        </Space>
      </div>

      {/* Month navigation */}
      <Card style={{
        marginBottom: 20,
        borderRadius: 14,
        border: "none",
        boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Button
            icon={<LeftOutlined />}
            onClick={() => navigateMonth(-1)}
            shape="circle"
            style={{ boxShadow: "0 2px 6px rgba(0,0,0,0.08)" }}
          />
          <div style={{ textAlign: "center", display: "flex", alignItems: "center", gap: 12 }}>
            <CalendarOutlined style={{ fontSize: 20, color: "#667eea" }} />
            <div style={{ fontSize: 22, fontWeight: 700, color: "#1e293b", letterSpacing: 0.5 }}>{monthLabel}</div>
            {isCurrentMonth && (
              <Tag color="blue" style={{ borderRadius: 10, padding: "2px 10px", fontWeight: 600, fontSize: 13 }}>本月</Tag>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              icon={<RightOutlined />}
              onClick={() => navigateMonth(1)}
              shape="circle"
              style={{ boxShadow: "0 2px 6px rgba(0,0,0,0.08)" }}
            />
            {!isCurrentMonth && (
              <Button type="link" onClick={goThisMonth} style={{ borderRadius: 8 }}>回到本月</Button>
            )}
          </div>
        </div>
      </Card>

      {/* Calendar Grid */}
      <Spin spinning={loading}>
        <Card
          style={{
            marginBottom: 20,
            borderRadius: 14,
            border: "none",
            boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
            overflow: "hidden",
          }}
          styles={{ body: { padding: 0 } }}
        >
          {/* Weekday header */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(7, 1fr)",
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            padding: "10px 0",
          }}>
            {WEEKDAY_LABELS.map((label) => (
              <div key={label} style={{
                textAlign: "center",
                fontSize: 14,
                fontWeight: 700,
                color: "rgba(255,255,255,0.9)",
                letterSpacing: 1,
              }}>
                {label}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(7, 1fr)",
          }}>
            {monthGrid.map((cell) => {
              const dayItems = itemsByDate[cell.dateStr] || [];
              const isToday = cell.dateStr === todayStr;
              const isSelected = cell.dateStr === selectedDate;
              const completedCount = dayItems.filter(i => i.completed === 1).length;
              const totalCount = dayItems.length;
              const allDone = totalCount > 0 && completedCount === totalCount;

              return (
                <div
                  key={cell.dateStr}
                  onClick={() => setSelectedDate(cell.dateStr)}
                  style={{
                    minHeight: 90,
                    padding: "6px 8px",
                    borderRight: "1px solid #f0f0f0",
                    borderBottom: "1px solid #f0f0f0",
                    cursor: "pointer",
                    background: isSelected
                      ? "#f0f5ff"
                      : isToday
                        ? "#fafafa"
                        : cell.isCurrentMonth
                          ? "#fff"
                          : "#f9f9f9",
                    transition: "background 0.2s",
                    position: "relative",
                  }}
                >
                  {/* Day number */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: 26,
                      height: 26,
                      borderRadius: "50%",
                      fontSize: 13,
                      fontWeight: isToday ? 700 : 500,
                      color: isToday ? "#fff" : cell.isCurrentMonth ? "#1e293b" : "#c0c0c0",
                      background: isToday
                        ? "linear-gradient(135deg, #667eea, #764ba2)"
                        : "transparent",
                    }}>
                      {cell.day}
                    </span>
                    {totalCount > 0 && (
                      <span style={{
                        fontSize: 11,
                        color: allDone ? "#22c55e" : "#94a3b8",
                        fontWeight: 500,
                      }}>
                        {completedCount}/{totalCount}
                      </span>
                    )}
                  </div>

                  {/* Activity icons */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                    {dayItems.slice(0, 4).map((item) => {
                      const at = item.activity_type;
                      const done = item.completed === 1;
                      return (
                        <Tooltip key={item.id} title={`${at?.name || "未知"}${done ? " ✓" : ""}`}>
                          <span style={{
                            fontSize: 16,
                            opacity: done ? 0.45 : 1,
                            filter: done ? "grayscale(0.6)" : "none",
                            lineHeight: 1,
                          }}>
                            {at?.icon || "📋"}
                          </span>
                        </Tooltip>
                      );
                    })}
                    {dayItems.length > 4 && (
                      <span style={{ fontSize: 11, color: "#94a3b8", lineHeight: "16px" }}>
                        +{dayItems.length - 4}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </Spin>

      {/* Selected day detail */}
      <Card
        title={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 17, fontWeight: 700 }}>
              {selectedDateObj.getMonth() + 1}月{selectedDateObj.getDate()}日 计划详情
            </span>
            {selectedDate === todayStr && (
              <Tag color="blue" style={{ borderRadius: 8, fontSize: 12 }}>今天</Tag>
            )}
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowAddModal(true)}
            style={{ borderRadius: 8, boxShadow: "0 2px 8px rgba(102, 126, 234, 0.3)" }}
          >
            添加活动
          </Button>
        }
        style={{
          marginBottom: 24,
          borderRadius: 14,
          border: "none",
          boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
        }}
      >
        {selectedDayItems.length === 0 ? (
          <Empty description="当天暂无安排，点击「添加活动」开始规划" />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {selectedDayItems.map((item) => {
              const at = item.activity_type;
              const isCompleted = item.completed === 1;
              return (
                <div
                  key={item.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 14,
                    padding: "14px 18px",
                    background: isCompleted
                      ? "linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)"
                      : "linear-gradient(135deg, #fafbfc 0%, #f8f9fb 100%)",
                    borderRadius: 14,
                    border: `1.5px solid ${isCompleted ? "#86efac" : "#e8ecf1"}`,
                    transition: "all 0.25s ease",
                    boxShadow: isCompleted
                      ? "0 2px 8px rgba(34, 197, 94, 0.08)"
                      : "0 1px 4px rgba(0,0,0,0.04)",
                  }}
                >
                  {/* Icon */}
                  <div
                    style={{
                      fontSize: 30,
                      width: 52,
                      height: 52,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: 14,
                      background: at?.color ? `${at.color}18` : "#f1f5f9",
                      border: at?.color ? `1.5px solid ${at.color}25` : "1.5px solid #e8ecf1",
                      flexShrink: 0,
                      boxShadow: "0 2px 6px rgba(0,0,0,0.04)",
                    }}
                  >
                    {at?.icon || "📋"}
                  </div>

                  {/* Name + note */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: 16,
                      fontWeight: 600,
                      color: isCompleted ? "#86efac" : "#1e293b",
                      textDecoration: isCompleted ? "line-through" : "none",
                    }}>
                      {at?.name || "未知活动"}
                    </div>
                    {isCompleted && item.completion_note && (
                      <div style={{ fontSize: 13, color: "#64748b", marginTop: 2 }}>
                        备注: {item.completion_note}
                      </div>
                    )}
                    {isCompleted && item.completed_at && (
                      <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>
                        {new Date(item.completed_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })} 完成
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <Space>
                    <Button
                      type={isCompleted ? "default" : "primary"}
                      shape="circle"
                      icon={isCompleted ? <CheckCircleFilled style={{ color: "#22c55e" }} /> : <CheckCircleOutlined />}
                      onClick={() => handleMarkComplete(item)}
                      title={isCompleted ? "取消完成" : "标记完成"}
                      style={isCompleted ? { border: "none", background: "transparent" } : {}}
                    />
                    <Popconfirm
                      title="确定删除这个活动？"
                      onConfirm={() => handleDeleteItem(item.id)}
                      okText="删除"
                      cancelText="取消"
                    >
                      <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                    </Popconfirm>
                  </Space>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Add activity modal */}
      <Modal
        title={`添加活动 - ${selectedDateObj.getMonth() + 1}月${selectedDateObj.getDate()}日`}
        open={showAddModal}
        onOk={handleAddItem}
        onCancel={() => setShowAddModal(false)}
        okText="添加"
        cancelText="取消"
      >
        <div style={{ marginBottom: 8, color: "#64748b" }}>选择要添加的活动类型：</div>
        <Select
          placeholder="选择活动类型"
          style={{ width: "100%" }}
          value={newActivityTypeId}
          onChange={setNewActivityTypeId}
          options={activityTypes.map(t => ({
            label: `${t.icon} ${t.name}`,
            value: t.id,
          }))}
        />
      </Modal>

      {/* Completion note modal */}
      <Modal
        title="完成备注"
        open={!!completingItem}
        onOk={handleConfirmComplete}
        onCancel={() => setCompletingItem(null)}
        okText="确认完成"
        cancelText="取消"
      >
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">
            为 <Text strong>{completingItem?.activity_type?.icon} {completingItem?.activity_type?.name}</Text> 添加完成备注（可选）：
          </Text>
        </div>
        <Input.TextArea
          value={completionNote}
          onChange={e => setCompletionNote(e.target.value)}
          placeholder="例如：数学作业全对，语文抄写认真"
          rows={3}
          maxLength={200}
          showCount
        />
      </Modal>

      {/* Activity type management modal */}
      <Modal
        title="活动类型管理"
        open={showTypeModal}
        onCancel={() => setShowTypeModal(false)}
        footer={null}
        width={560}
      >
        <div style={{ marginBottom: 16 }}>
          <Text strong>现有活动类型：</Text>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
            {activityTypes.map(t => (
              <Tag
                key={t.id}
                color={t.color}
                closable
                onClose={(e) => {
                  e.preventDefault();
                  handleDeleteType(t.id);
                }}
                style={{ padding: "4px 10px", fontSize: 14 }}
              >
                {t.icon} {t.name}
              </Tag>
            ))}
          </div>
        </div>

        <Divider style={{ margin: "16px 0" }} />

        <Text strong>新增自定义活动类型：</Text>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12, flexWrap: "wrap" }}>
          <Select
            value={newTypeIcon}
            onChange={setNewTypeIcon}
            style={{ width: 80 }}
            options={EMOJI_OPTIONS.map(e => ({ label: e, value: e }))}
          />
          <Input
            value={newTypeName}
            onChange={e => setNewTypeName(e.target.value)}
            placeholder="活动名称"
            style={{ width: 150 }}
          />
          <div style={{ display: "flex", alignItems: "center" }}>
            <ColorPicker
              value={newTypeColor}
              onChange={(_, hex) => setNewTypeColor(hex)}
              showText
            />
          </div>
          <Select
            value={newTypeCategory}
            onChange={setNewTypeCategory}
            style={{ width: 100 }}
            options={[
              { label: "学习", value: "homework" },
              { label: "阅读", value: "reading" },
              { label: "运动", value: "sports" },
              { label: "才艺", value: "arts" },
              { label: "自由", value: "freeplay" },
              { label: "自定义", value: "custom" },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateType} style={{ borderRadius: 8 }}>添加</Button>
        </div>
      </Modal>

      {/* Template editor modal */}
      <Modal
        title="周模板编辑"
        open={showTemplateModal}
        onOk={handleSaveTemplate}
        onCancel={() => setShowTemplateModal(false)}
        okText="保存模板"
        cancelText="取消"
        width={720}
      >
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          为每天设置默认活动安排，新的一天会自动从模板生成计划。
        </Text>
        {WEEKDAY_LABELS.map((label, dow) => {
          const dayItems = templateEditDays.filter(d => d.day_of_week === dow);
          return (
            <div key={dow} style={{ marginBottom: 12, padding: "8px 12px", background: "#fafafa", borderRadius: 8 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <Text strong>周{label}</Text>
                <Select
                  placeholder="+ 添加"
                  style={{ width: 120 }}
                  value={null}
                  onChange={(val: number) => addTemplateDay(dow, val)}
                  options={activityTypes.map(t => ({ label: `${t.icon} ${t.name}`, value: t.id }))}
                />
              </div>
              {dayItems.length === 0 ? (
                <Text type="secondary" style={{ fontSize: 13 }}>暂无安排</Text>
              ) : (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {dayItems.map((d, idx) => {
                    const at = activityTypes.find(t => t.id === d.activity_type_id);
                    const globalIdx = templateEditDays.indexOf(d);
                    return (
                      <Tag
                        key={idx}
                        closable
                        onClose={(e) => { e.preventDefault(); removeTemplateDay(globalIdx); }}
                        color={at?.color}
                      >
                        {at?.icon} {at?.name || `ID:${d.activity_type_id}`}
                      </Tag>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </Modal>
    </div>
  );
}
