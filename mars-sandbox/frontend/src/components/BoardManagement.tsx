import { useState, useEffect, useCallback } from "react";
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
  DatePicker,
  ColorPicker,
  Modal,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  PushpinOutlined,
  PushpinFilled,
  ClockCircleOutlined,
  StarFilled,
} from "@ant-design/icons";
import { fetchMessages, createMessage, updateMessage, deleteMessage, togglePin } from "../api/board";
import { fetchMembers } from "../api/meals";
import { createStar, fetchStars, deleteStar } from "../api/stars";
import { fetchDailySchedule } from "../api/schedule";
import type { BoardMessage, FamilyMember, StarReward, TodayScheduleItem } from "../types";
import { resolveColor, formatBoardDateTime, PRESET_COLORS } from "../utils";
import dayjs from "dayjs";

const { TextArea } = Input;
const { Text } = Typography;

export function BoardManagement() {
  const [messages, setMessages] = useState<BoardMessage[]>([]);
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // 新增留言表单
  const [newContent, setNewContent] = useState("");
  const [newAuthor, setNewAuthor] = useState("");
  const [newColor, setNewColor] = useState("#fef9c3");
  const [newExpiresAt, setNewExpiresAt] = useState<dayjs.Dayjs | null>(null);
  const [showForm, setShowForm] = useState(false);

  // 编辑留言
  const [editingMsg, setEditingMsg] = useState<BoardMessage | null>(null);
  const [editContent, setEditContent] = useState("");
  const [editAuthor, setEditAuthor] = useState("");
  const [editColor, setEditColor] = useState("#fef9c3");
  const [editExpiresAt, setEditExpiresAt] = useState<dayjs.Dayjs | null>(null);

  // 星星奖励
  const [starModalOpen, setStarModalOpen] = useState(false);
  const [starCount, setStarCount] = useState(3);
  const [starReason, setStarReason] = useState("");
  const [starAwardedBy, setStarAwardedBy] = useState("");
  const [starScheduleId, setStarScheduleId] = useState<number | null>(null);
  const [todayCompleted, setTodayCompleted] = useState<TodayScheduleItem[]>([]);
  const [starRecords, setStarRecords] = useState<StarReward[]>([]);
  const [starLoading, setStarLoading] = useState(false);

  const loadMessages = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMessages();
      setMessages(data);
    } catch (e) {
      console.error("Failed to load messages:", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadMessages();
    fetchMembers().then(setMembers).catch(() => {});
  }, [loadMessages]);

  // 加载今日已完成计划和星星记录
  const loadStarData = useCallback(async () => {
    try {
      const [schedule, stars] = await Promise.all([
        fetchDailySchedule().catch(() => []),
        fetchStars({ page_size: 20 }).catch(() => []),
      ]);
      setTodayCompleted((schedule as unknown as TodayScheduleItem[]).filter((s: TodayScheduleItem) => s.completed === 1));
      setStarRecords(stars);
    } catch {}
  }, []);

  const openStarModal = () => {
    setStarModalOpen(true);
    setStarCount(3);
    setStarReason("");
    setStarAwardedBy("");
    setStarScheduleId(null);
    loadStarData();
  };

  const handleCreateStar = async () => {
    if (!starAwardedBy.trim()) {
      message.warning("请选择或输入颁发者");
      return;
    }
    setStarLoading(true);
    try {
      await createStar({
        stars: starCount,
        awarded_by: starAwardedBy.trim(),
        reason: starReason.trim() || undefined,
        related_schedule_id: starScheduleId || undefined,
      });
      message.success(`已奖励 ${starCount} 颗星星`);
      setStarModalOpen(false);
      await loadStarData();
    } catch {
      message.error("发星星失败");
    }
    setStarLoading(false);
  };

  const handleDeleteStar = async (id: number) => {
    try {
      await deleteStar(id);
      message.success("星星已删除");
      await loadStarData();
    } catch {
      message.error("删除失败");
    }
  };

  // 将家庭成员转为下拉选项
  const memberOptions = members.map((m) => ({
    label: `${m.avatar} ${m.name}`,
    value: m.name,
  }));

  // 选择作者时，自动使用该成员的默认留言板颜色
  const handleSelectAuthor = (name: string | undefined) => {
    setNewAuthor(name || "");
    if (name) {
      const member = members.find((m) => m.name === name);
      if (member?.board_color) {
        setNewColor(member.board_color);
      }
    }
  };

  const handleCreate = async () => {
    if (!newContent.trim()) {
      message.warning("请输入留言内容");
      return;
    }
    setSubmitting(true);
    try {
      await createMessage({
        content: newContent.trim(),
        author: newAuthor.trim() || "匿名",
        color: newColor,
        expires_at: newExpiresAt ? newExpiresAt.format("YYYY-MM-DD") : null,
      });
      message.success("留言已添加");
      setNewContent("");
      setNewAuthor("");
      setNewColor("#fef9c3");
      setNewExpiresAt(null);
      setShowForm(false);
      await loadMessages();
    } catch (e) {
      message.error("添加留言失败");
    }
    setSubmitting(false);
  };

  const openEditModal = (msg: BoardMessage) => {
    setEditingMsg(msg);
    setEditContent(msg.content);
    setEditAuthor(msg.author || "");
    setEditColor(resolveColor(msg.color));
    setEditExpiresAt(msg.expires_at ? dayjs(msg.expires_at) : null);
  };

  const handleEdit = async () => {
    if (!editingMsg) return;
    if (!editContent.trim()) {
      message.warning("留言内容不能为空");
      return;
    }
    setSubmitting(true);
    try {
      await updateMessage(editingMsg.id, {
        content: editContent.trim(),
        author: editAuthor.trim() || "匿名",
        color: editColor,
        expires_at: editExpiresAt ? editExpiresAt.format("YYYY-MM-DD") : null,
      });
      message.success("留言已更新");
      setEditingMsg(null);
      await loadMessages();
    } catch (e) {
      message.error("更新留言失败");
    }
    setSubmitting(false);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMessage(id);
      message.success("留言已删除");
      await loadMessages();
    } catch (e) {
      message.error("删除失败");
    }
  };

  const handleTogglePin = async (id: number) => {
    try {
      await togglePin(id);
      await loadMessages();
    } catch (e) {
      message.error("操作失败");
    }
  };

  return (
    <div>
      {/* 顶部操作栏 */}
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text strong style={{ fontSize: 18 }}>家庭留言板</Text>
        <Space>
          <Button
            type="primary"
            icon={<StarFilled />}
            onClick={openStarModal}
            style={{ background: "linear-gradient(135deg, #fbbf24, #f59e0b)", borderColor: "#f59e0b" }}
          >
            发星星
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowForm(!showForm)}
          >
            新增留言
          </Button>
        </Space>
      </div>

      {/* 新增留言表单 */}
      {showForm && (
        <Card style={{ marginBottom: 24, borderLeft: `4px solid ${newColor}`, background: "#fff" }}>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <TextArea
              placeholder="输入留言内容..."
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              rows={3}
              maxLength={500}
              showCount
            />
            <Space wrap>
              <Select
                placeholder="选择作者"
                value={newAuthor || undefined}
                onChange={handleSelectAuthor}
                options={memberOptions}
                allowClear
                style={{ width: 140 }}
              />
              <Space size={4}>
                <span style={{ fontSize: 13, color: "#64748b" }}>颜色：</span>
                <ColorPicker
                  value={newColor}
                  onChange={(_, hex) => setNewColor(hex)}
                  presets={[{ label: "推荐", colors: PRESET_COLORS }]}
                  showText
                  size="small"
                />
              </Space>
              <DatePicker
                placeholder="过期日期（可选）"
                value={newExpiresAt}
                onChange={(date) => setNewExpiresAt(date)}
                style={{ width: 160 }}
                disabledDate={(current) => current && current < dayjs().startOf("day")}
              />
              <Space>
                <Button type="primary" onClick={handleCreate} loading={submitting}>
                  发布
                </Button>
                <Button onClick={() => setShowForm(false)}>取消</Button>
              </Space>
            </Space>
          </Space>
        </Card>
      )}

      {/* 留言列表 */}
      <Spin spinning={loading}>
        {messages.length === 0 && !loading ? (
          <Empty description="暂无留言，快来写一条吧" />
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 16,
          }}>
            {messages.map((msg) => (
              <Card
                key={msg.id}
                style={{
                  borderLeft: `4px solid ${resolveColor(msg.color)}`,
                  borderRadius: 8,
                  position: "relative",
                  background: "#fff",
                }}
                styles={{ body: { padding: "16px 20px" } }}
              >
                {/* 置顶标记 */}
                {msg.pinned ? (
                  <PushpinFilled style={{
                    position: "absolute",
                    top: 12,
                    right: 12,
                    color: "#ef4444",
                    fontSize: 14,
                  }} />
                ) : null}

                {/* 内容 */}
                <div style={{
                  fontSize: 15,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  marginBottom: 12,
                  paddingRight: msg.pinned ? 20 : 0,
                }}>
                  {msg.content}
                </div>

                {/* 底部信息 */}
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontSize: 12,
                  color: "#64748b",
                }}>
                  <span>
                    {msg.author || "匿名"} · {formatBoardDateTime(msg.created_at)}
                  </span>
                  <Space size="small">
                    {msg.expires_at && (
                      <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                        <ClockCircleOutlined />
                        {new Date(msg.expires_at).toLocaleDateString("zh-CN")}
                      </span>
                    )}
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => openEditModal(msg)}
                      title="编辑"
                    />
                    <Button
                      type="text"
                      size="small"
                      icon={msg.pinned ? <PushpinFilled /> : <PushpinOutlined />}
                      onClick={() => handleTogglePin(msg.id)}
                      title={msg.pinned ? "取消置顶" : "置顶"}
                    />
                    <Popconfirm
                      title="确定删除这条留言吗？"
                      onConfirm={() => handleDelete(msg.id)}
                      okText="删除"
                      cancelText="取消"
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                      />
                    </Popconfirm>
                  </Space>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Spin>

      {/* 编辑留言弹窗 */}
      <Modal
        title="编辑留言"
        open={!!editingMsg}
        onOk={handleEdit}
        onCancel={() => setEditingMsg(null)}
        confirmLoading={submitting}
        okText="保存"
        cancelText="取消"
      >
        <div style={{ background: "#fff", borderLeft: `4px solid ${editColor}`, borderRadius: 8, padding: 16 }}>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <TextArea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={4}
              maxLength={500}
              showCount
            />
            <Space wrap>
              <Select
                placeholder="选择作者"
                value={editAuthor || undefined}
                onChange={(val) => setEditAuthor(val || "")}
                options={memberOptions}
                allowClear
                style={{ width: 140 }}
              />
              <Space size={4}>
                <span style={{ fontSize: 13, color: "#64748b" }}>颜色：</span>
                <ColorPicker
                  value={editColor}
                  onChange={(_, hex) => setEditColor(hex)}
                  presets={[{ label: "推荐", colors: PRESET_COLORS }]}
                  showText
                  size="small"
                />
              </Space>
              <DatePicker
                placeholder="过期日期（可选）"
                value={editExpiresAt}
                onChange={(date) => setEditExpiresAt(date)}
                style={{ width: 160 }}
                disabledDate={(current) => current && current < dayjs().startOf("day")}
              />
            </Space>
          </Space>
        </div>
      </Modal>

      {/* 发星星弹窗 */}
      <Modal
        title={
          <span>
            <StarFilled style={{ color: "#f59e0b", marginRight: 8 }} />
            奖励星星
          </span>
        }
        open={starModalOpen}
        onOk={handleCreateStar}
        onCancel={() => setStarModalOpen(false)}
        confirmLoading={starLoading}
        okText="确认奖励"
        cancelText="取消"
        width={480}
      >
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          {/* 星星数量选择 */}
          <div>
            <Text type="secondary" style={{ fontSize: 13 }}>星星数量</Text>
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              {[1, 2, 3, 4, 5].map((n) => (
                <div
                  key={n}
                  onClick={() => setStarCount(n)}
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    border: starCount >= n ? "2px solid #f59e0b" : "2px solid #e5e7eb",
                    background: starCount >= n ? "#fef3c7" : "#f8fafc",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    fontSize: 24,
                    transition: "all 0.2s ease",
                  }}
                >
                  <StarFilled style={{ color: starCount >= n ? "#f59e0b" : "#cbd5e1" }} />
                </div>
              ))}
              <div style={{
                display: "flex",
                alignItems: "center",
                fontSize: 20,
                fontWeight: 700,
                color: "#f59e0b",
                marginLeft: 8,
              }}>
                x{starCount}
              </div>
            </div>
          </div>

          {/* 颁发者 */}
          <div>
            <Text type="secondary" style={{ fontSize: 13 }}>颁发者</Text>
            <Select
              placeholder="选择颁发者"
              value={starAwardedBy || undefined}
              onChange={(val) => setStarAwardedBy(val || "")}
              options={memberOptions}
              allowClear
              style={{ width: "100%", marginTop: 4 }}
            />
          </div>

          {/* 原因 */}
          <div>
            <Text type="secondary" style={{ fontSize: 13 }}>奖励原因（可选）</Text>
            <Input
              placeholder="例如：数学作业完成优秀"
              value={starReason}
              onChange={(e) => setStarReason(e.target.value)}
              maxLength={200}
              style={{ marginTop: 4 }}
            />
          </div>

          {/* 关联学习计划 */}
          {todayCompleted.length > 0 && (
            <div>
              <Text type="secondary" style={{ fontSize: 13 }}>关联今日已完成计划（可选）</Text>
              <Select
                placeholder="选择已完成的计划项"
                value={starScheduleId}
                onChange={(val) => setStarScheduleId(val)}
                allowClear
                style={{ width: "100%", marginTop: 4 }}
                options={todayCompleted.map((item) => ({
                  label: `${item.activity_type?.icon || ""} ${item.activity_type?.name || "未知活动"}`,
                  value: item.id,
                }))}
              />
            </div>
          )}

          {/* 最近星星记录 */}
          {starRecords.length > 0 && (
            <div>
              <Text type="secondary" style={{ fontSize: 13 }}>最近奖励记录</Text>
              <div style={{
                marginTop: 8,
                display: "flex",
                flexDirection: "column",
                gap: 6,
                maxHeight: 160,
                overflowY: "auto",
              }}>
                {starRecords.slice(0, 8).map((record) => (
                  <div
                    key={record.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      background: "#f8fafc",
                      borderRadius: 8,
                      padding: "6px 10px",
                    }}
                  >
                    <StarFilled style={{ color: "#f59e0b" }} />
                    <span style={{ fontWeight: 600, color: "#f59e0b" }}>+{record.stars}</span>
                    <span style={{ flex: 1, fontSize: 13 }}>{record.reason || "学习奖励"}</span>
                    <span style={{ fontSize: 11, color: "#94a3b8" }}>
                      {record.awarded_by}
                    </span>
                    <Popconfirm
                      title="确定删除吗？"
                      onConfirm={() => handleDeleteStar(record.id)}
                      okText="删除"
                      cancelText="取消"
                    >
                      <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Space>
      </Modal>
    </div>
  );
}
