import { useEffect, useState } from "react";
import {
  Card,
  Row,
  Col,
  Tag,
  Button,
  Modal,
  Input,
  Space,
  message,
  Spin,
  Typography,
  Divider,
  Popconfirm,
  ColorPicker,
  Form,
} from "antd";
import { PlusOutlined, DeleteOutlined, EditOutlined } from "@ant-design/icons";
import type { FamilyMember } from "../types";
import { fetchMembers, createMember, updateMember, deleteMember } from "../api/meals";
import { useIsMobile } from "../hooks/useIsMobile";
import { PRESET_COLORS } from "../utils";

const { Text } = Typography;

const AVATAR_OPTIONS = [
  "👨", "👩", "👧", "👦", "👴", "👵", "🧑", "👶",
  "🐱", "🐶", "🐰", "🐼", "🦊", "🐻", "🐨", "🐸",
];


export function FamilySettings() {
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState<FamilyMember | null>(null);
  const [editName, setEditName] = useState("");
  const [editAvatar, setEditAvatar] = useState("");
  const [editLikes, setEditLikes] = useState<string[]>([]);
  const [editDislikes, setEditDislikes] = useState<string[]>([]);
  const [editAllergies, setEditAllergies] = useState<string[]>([]);
  const [editNote, setEditNote] = useState("");
  const [editBoardColor, setEditBoardColor] = useState<string>("#fef9c3");
  const [newTag, setNewTag] = useState({ likes: "", dislikes: "", allergies: "" });

  // 新增成员弹窗
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addName, setAddName] = useState("");
  const [addAvatar, setAddAvatar] = useState("🧑");
  const [addBoardColor, setAddBoardColor] = useState("#fef9c3");

  const isMobile = useIsMobile();

  useEffect(() => {
    loadMembers();
  }, []);

  const loadMembers = async () => {
    try {
      const data = await fetchMembers();
      setMembers(data);
    } catch {
      message.error("加载家庭成员失败");
    } finally {
      setLoading(false);
    }
  };

  const openEdit = (m: FamilyMember) => {
    setEditModal(m);
    setEditName(m.name);
    setEditAvatar(m.avatar);
    setEditLikes(m.preferences?.likes || []);
    setEditDislikes(m.preferences?.dislikes || []);
    setEditAllergies(m.allergies || []);
    setEditNote(m.preferences?.note || "");
    setEditBoardColor(m.board_color || "#fef9c3");
    setNewTag({ likes: "", dislikes: "", allergies: "" });
  };

  const handleSave = async () => {
    if (!editModal) return;
    if (!editName.trim()) {
      message.warning("名字不能为空");
      return;
    }
    try {
      await updateMember(editModal.id, {
        name: editName.trim(),
        avatar: editAvatar,
        preferences: { likes: editLikes, dislikes: editDislikes, note: editNote },
        allergies: editAllergies,
        board_color: editBoardColor,
      });
      message.success("保存成功");
      setEditModal(null);
      loadMembers();
    } catch {
      message.error("保存失败");
    }
  };

  const handleAdd = async () => {
    if (!addName.trim()) {
      message.warning("请输入成员名字");
      return;
    }
    try {
      await createMember({
        name: addName.trim(),
        avatar: addAvatar,
        board_color: addBoardColor,
      });
      message.success("添加成功");
      setAddModalOpen(false);
      setAddName("");
      setAddAvatar("🧑");
      setAddBoardColor("#fef9c3");
      loadMembers();
    } catch {
      message.error("添加失败");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMember(id);
      message.success("删除成功");
      loadMembers();
    } catch {
      message.error("删除失败");
    }
  };

  const addTag = (type: "likes" | "dislikes" | "allergies") => {
    const val = newTag[type].trim();
    if (!val) return;
    if (type === "likes" && !editLikes.includes(val)) setEditLikes([...editLikes, val]);
    if (type === "dislikes" && !editDislikes.includes(val)) setEditDislikes([...editDislikes, val]);
    if (type === "allergies" && !editAllergies.includes(val)) setEditAllergies([...editAllergies, val]);
    setNewTag({ ...newTag, [type]: "" });
  };

  const removeTag = (type: "likes" | "dislikes" | "allergies", val: string) => {
    if (type === "likes") setEditLikes(editLikes.filter((v) => v !== val));
    if (type === "dislikes") setEditDislikes(editDislikes.filter((v) => v !== val));
    if (type === "allergies") setEditAllergies(editAllergies.filter((v) => v !== val));
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "80px auto" }} />;

  const renderTagSection = (
    label: string,
    tags: string[],
    type: "likes" | "dislikes" | "allergies",
    color: string
  ) => (
    <div style={{ marginBottom: 12 }}>
      <Text strong>{label}</Text>
      <div style={{ marginTop: 6 }}>
        {tags.map((t) => (
          <Tag
            key={t}
            color={color}
            closable
            onClose={() => removeTag(type, t)}
            style={{ marginBottom: 4 }}
          >
            {t}
          </Tag>
        ))}
        <Space size="small" style={{ display: "inline-flex" }}>
          <Input
            size="small"
            placeholder="添加..."
            value={newTag[type]}
            onChange={(e) => setNewTag({ ...newTag, [type]: e.target.value })}
            onPressEnter={() => addTag(type)}
            style={{ width: 80 }}
          />
          <Button size="small" type="dashed" icon={<PlusOutlined />} onClick={() => addTag(type)} />
        </Space>
      </div>
    </div>
  );

  const renderAvatarPicker = (
    selectedAvatar: string,
    onSelect: (avatar: string) => void
  ) => (
    <div style={{ marginBottom: 12 }}>
      <Text strong>头像</Text>
      <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 8 }}>
        {AVATAR_OPTIONS.map((a) => (
          <Button
            key={a}
            type={selectedAvatar === a ? "primary" : "default"}
            size="small"
            onClick={() => onSelect(a)}
            style={{ fontSize: 20, width: 40, height: 40, padding: 0 }}
          >
            {a}
          </Button>
        ))}
      </div>
    </div>
  );

  const renderBoardColorPicker = (
    color: string,
    onChange: (color: string) => void
  ) => (
    <div style={{ marginBottom: 12 }}>
      <Text strong>留言板默认颜色</Text>
      <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8 }}>
        <ColorPicker
          value={color}
          onChange={(_, hex) => onChange(hex)}
          presets={[{ label: "推荐", colors: PRESET_COLORS }]}
          showText
          size="small"
        />
        <div
          style={{
            width: 60,
            height: 24,
            borderRadius: 4,
            background: color,
            border: "1px solid #e2e8f0",
          }}
        />
      </div>
    </div>
  );

  return (
    <div>
      {/* 顶部操作栏 */}
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text strong style={{ fontSize: 18 }}>家庭成员管理</Text>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
          添加成员
        </Button>
      </div>

      <Row gutter={[isMobile ? 10 : 16, isMobile ? 10 : 16]}>
        {members.map((m) => (
          <Col xs={24} sm={12} md={6} key={m.id}>
            <Card
              size="small"
              title={
                <Space>
                  <span style={{ fontSize: 24 }}>{m.avatar}</span>
                  <span style={{ fontWeight: 600 }}>{m.name}</span>
                </Space>
              }
              extra={
                <Space size="small">
                  <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(m)} style={{ borderRadius: 6 }}>
                    编辑
                  </Button>
                  <Popconfirm
                    title="确定删除该成员吗？"
                    onConfirm={() => handleDelete(m.id)}
                    okText="删除"
                    cancelText="取消"
                  >
                    <Button size="small" danger icon={<DeleteOutlined />} style={{ borderRadius: 6 }} />
                  </Popconfirm>
                </Space>
              }
              style={{ borderRadius: 12, border: "1px solid #f1f5f9" }}
            >
              {m.board_color && (
                <div style={{ marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
                  <Text type="secondary">留言颜色:</Text>
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 4,
                      background: m.board_color,
                      border: "1px solid #e2e8f0",
                    }}
                  />
                </div>
              )}
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">喜欢: </Text>
                {(m.preferences?.likes || []).length > 0
                  ? (m.preferences?.likes || []).map((l) => (
                      <Tag key={l} color="green" style={{ marginBottom: 2 }}>{l}</Tag>
                    ))
                  : <Text type="secondary">暂无</Text>}
              </div>
              {m.liked_dishes && m.liked_dishes.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">常点赞: </Text>
                  {m.liked_dishes.map((d) => (
                    <Tag key={d.dish_id} color="blue" style={{ marginBottom: 2 }}>
                      {d.dish_name} ({d.like_count})
                    </Tag>
                  ))}
                </div>
              )}
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">不喜欢: </Text>
                {(m.preferences?.dislikes || []).length > 0
                  ? (m.preferences?.dislikes || []).map((d) => (
                      <Tag key={d} color="red" style={{ marginBottom: 2 }}>{d}</Tag>
                    ))
                  : <Text type="secondary">暂无</Text>}
              </div>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">忌口: </Text>
                {(m.allergies || []).length > 0
                  ? (m.allergies || []).map((a) => (
                      <Tag key={a} color="orange" style={{ marginBottom: 2 }}>{a}</Tag>
                    ))
                  : <Text type="secondary">无</Text>}
              </div>
              {m.preferences?.note && (
                <div>
                  <Text type="secondary">备注: </Text>
                  <Text>{m.preferences.note}</Text>
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>

      {/* 编辑成员弹窗 */}
      <Modal
        title="编辑家庭成员"
        open={!!editModal}
        onOk={handleSave}
        onCancel={() => setEditModal(null)}
        okText="保存"
        cancelText="取消"
        width={500}
      >
        {editModal && (
          <>
            <Form layout="vertical">
              <Form.Item label="名字">
                <Input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="输入名字"
                  maxLength={20}
                />
              </Form.Item>
            </Form>
            {renderAvatarPicker(editAvatar, setEditAvatar)}
            {renderBoardColorPicker(editBoardColor, setEditBoardColor)}
            <Divider />
            {renderTagSection("喜欢的菜品", editLikes, "likes", "green")}
            {renderTagSection("不喜欢的菜品", editDislikes, "dislikes", "red")}
            {renderTagSection("过敏/忌口", editAllergies, "allergies", "orange")}
            <Divider />
            <div>
              <Text strong>备注</Text>
              <Input.TextArea
                rows={2}
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                placeholder="如：偏好清淡、不吃辣..."
                style={{ marginTop: 6 }}
              />
            </div>
          </>
        )}
      </Modal>

      {/* 添加成员弹窗 */}
      <Modal
        title="添加家庭成员"
        open={addModalOpen}
        onOk={handleAdd}
        onCancel={() => setAddModalOpen(false)}
        okText="添加"
        cancelText="取消"
      >
        <Form layout="vertical">
          <Form.Item label="名字" required>
            <Input
              value={addName}
              onChange={(e) => setAddName(e.target.value)}
              placeholder="输入成员名字"
              maxLength={20}
            />
          </Form.Item>
        </Form>
        {renderAvatarPicker(addAvatar, setAddAvatar)}
        {renderBoardColorPicker(addBoardColor, setAddBoardColor)}
      </Modal>
    </div>
  );
}
