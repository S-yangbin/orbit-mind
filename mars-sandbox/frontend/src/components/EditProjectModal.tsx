import { useState, useEffect } from "react";
import { Modal, Form, Input, Select, Button, Space, message } from "antd";
import { fetchTags, createTag } from "../api/tags";
import { updatePage } from "../api/pages";
import type { Page, Tag } from "../types";
import { useIsMobile } from "../hooks/useIsMobile";
import { CATEGORY_OPTIONS } from "../utils";

interface Props {
  page: Page;
  visible: boolean;
  onClose: () => void;
  onSave: () => void;
}

export function EditProjectModal({ page, visible, onClose, onSave }: Props) {
  const [form] = Form.useForm();
  const [tags, setTags] = useState<Tag[]>([]);
  const [saving, setSaving] = useState(false);
  const isMobile = useIsMobile();

  useEffect(() => {
    if (visible) {
      form.setFieldsValue({
        title: page.title,
        description: page.description || "",
        tags: page.tags.map((t) => t.name),
        category: page.category || "work",
      });
      fetchTags().then(setTags).catch(() => {});
    }
  }, [visible, page, form]);

  const handleSave = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      await updatePage(page.id, {
        title: values.title,
        description: values.description,
        tags: values.tags || [],
        category: values.category,
      });
      message.success("保存成功");
      onSave();
    } catch {
      message.error("保存失败");
    }
    setSaving(false);
  };

  // Create new tag on the fly
  const handleCreateTag = async (name: string) => {
    try {
      const newTag = await createTag(name);
      setTags((prev) => [...prev, newTag]);
      return newTag.name;
    } catch {
      return name;
    }
  };

  return (
    <Modal
      title="编辑项目信息"
      open={visible}
      onCancel={onClose}
      footer={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={handleSave} loading={saving}>
            保存
          </Button>
        </Space>
      }
      width={isMobile ? "calc(100vw - 16px)" : 500}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="title"
          label="标题"
          rules={[{ required: true, message: "请输入标题" }]}
        >
          <Input placeholder="页面标题" />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <Input.TextArea rows={3} placeholder="页面描述" />
        </Form.Item>
        <Form.Item name="category" label="分组">
          <Select options={CATEGORY_OPTIONS} />
        </Form.Item>
        <Form.Item name="tags" label="标签">
          <Select
            mode="tags"
            placeholder="输入或选择标签"
            options={tags.map((t) => ({ label: t.name, value: t.name }))}
            tokenSeparators={[","]}
            allowClear
          />
        </Form.Item>
      </Form>
      {page.is_customized === 1 && (
        <div style={{
          marginTop: 12,
          padding: "8px 12px",
          background: "#eff6ff",
          borderRadius: 8,
          fontSize: 12,
          color: "#64748b",
          border: "1px solid #dbeafe",
        }}>
          此页面已被手动编辑过，后续扫描不会覆盖您修改的字段
        </div>
      )}
    </Modal>
  );
}
