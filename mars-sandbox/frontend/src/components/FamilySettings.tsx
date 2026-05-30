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
} from "antd";
import { PlusOutlined, CloseCircleFilled } from "@ant-design/icons";
import type { FamilyMember } from "../types";
import { fetchMembers, updateMember } from "../api/meals";
import { useIsMobile } from "../hooks/useIsMobile";

const { Text } = Typography;

const ROLE_LABELS: Record<string, string> = {
  father: "爸爸",
  mother: "妈妈",
  child: "孩子(6岁)",
  grandma: "奶奶(59岁)",
};

export function FamilySettings() {
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState<FamilyMember | null>(null);
  const [editLikes, setEditLikes] = useState<string[]>([]);
  const [editDislikes, setEditDislikes] = useState<string[]>([]);
  const [editAllergies, setEditAllergies] = useState<string[]>([]);
  const [editNote, setEditNote] = useState("");
  const [newTag, setNewTag] = useState({ likes: "", dislikes: "", allergies: "" });
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
    setEditLikes(m.preferences?.likes || []);
    setEditDislikes(m.preferences?.dislikes || []);
    setEditAllergies(m.allergies || []);
    setEditNote(m.preferences?.note || "");
    setNewTag({ likes: "", dislikes: "", allergies: "" });
  };

  const handleSave = async () => {
    if (!editModal) return;
    try {
      await updateMember(editModal.id, {
        preferences: { likes: editLikes, dislikes: editDislikes, note: editNote },
        allergies: editAllergies,
      });
      message.success("保存成功");
      setEditModal(null);
      loadMembers();
    } catch {
      message.error("保存失败");
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

  return (
    <div>
      <Row gutter={[isMobile ? 10 : 16, isMobile ? 10 : 16]}>
        {members.map((m) => (
          <Col xs={24} sm={12} md={6} key={m.id}>
            <Card
              size="small"
              title={
                <Space>
                  <span style={{ fontSize: 24 }}>{m.avatar}</span>
                  <span style={{ fontWeight: 600 }}>{ROLE_LABELS[m.role] || m.name}</span>
                </Space>
              }
              extra={<Button size="small" onClick={() => openEdit(m)} style={{ borderRadius: 6 }}>编辑</Button>}
              style={{ borderRadius: 12, border: "1px solid #f1f5f9" }}
            >
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

      <Modal
        title={`编辑偏好 - ${editModal ? (ROLE_LABELS[editModal.role] || editModal.name) : ""}`}
        open={!!editModal}
        onOk={handleSave}
        onCancel={() => setEditModal(null)}
        okText="保存"
        cancelText="取消"
      >
        {editModal && (
          <>
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
    </div>
  );
}
