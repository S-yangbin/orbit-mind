import { useState, useEffect, useCallback } from "react";
import {
  Card,
  Button,
  Input,
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
} from "@ant-design/icons";
import { fetchMessages, createMessage, updateMessage, deleteMessage, togglePin } from "../api/board";
import type { BoardMessage } from "../types";
import dayjs from "dayjs";

const { TextArea } = Input;
const { Text } = Typography;

// 预设颜色（保留向后兼容，旧数据仍可能是命名颜色）
const NAMED_COLOR_MAP: Record<string, string> = {
  yellow: "#fef9c3",
  pink: "#fce7f3",
  blue: "#dbeafe",
  green: "#dcfce7",
};

const PRESET_COLORS = [
  "#fef9c3", // 黄
  "#fce7f3", // 粉
  "#dbeafe", // 蓝
  "#dcfce7", // 绿
  "#fef3c7", // 琥珀
  "#e0e7ff", // 靛蓝
  "#f3e8ff", // 紫
  "#ffe4e6", // 玫瑰
  "#fed7aa", // 橙
  "#ffffff", // 白
];

/** 将颜色值（可能是命名色或 hex）统一转为 hex */
function resolveColor(color: string): string {
  return NAMED_COLOR_MAP[color] || color;
}

function formatDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function BoardManagement() {
  const [messages, setMessages] = useState<BoardMessage[]>([]);
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
  }, [loadMessages]);

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
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setShowForm(!showForm)}
        >
          新增留言
        </Button>
      </div>

      {/* 新增留言表单 */}
      {showForm && (
        <Card style={{ marginBottom: 24, background: newColor }}>
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
              <Input
                placeholder="作者（可选）"
                value={newAuthor}
                onChange={(e) => setNewAuthor(e.target.value)}
                style={{ width: 150 }}
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
                  background: resolveColor(msg.color),
                  borderRadius: 8,
                  position: "relative",
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
                    {msg.author || "匿名"} · {formatDateTime(msg.created_at)}
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
        <div style={{ background: editColor, borderRadius: 8, padding: 16 }}>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <TextArea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={4}
              maxLength={500}
              showCount
            />
            <Space wrap>
              <Input
                placeholder="作者"
                value={editAuthor}
                onChange={(e) => setEditAuthor(e.target.value)}
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
    </div>
  );
}
