import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Spin, Button, Space, Tag, Typography, Descriptions, Card } from "antd";
import { ArrowLeftOutlined, EditOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/zh-cn";
import { fetchPage } from "../api/pages";
import type { Page } from "../types";
import { EditProjectModal } from "./EditProjectModal";
import { useIsMobile } from "../hooks/useIsMobile";

dayjs.extend(relativeTime);
dayjs.locale("zh-cn");

const { Title, Text } = Typography;

export function PagePreview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [page, setPage] = useState<Page | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEdit, setShowEdit] = useState(false);
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchPage(Number(id))
      .then(setPage)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "80px 0" }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!page) {
    return <div style={{ textAlign: "center", padding: "80px 0" }}>页面不存在</div>;
  }

  return (
    <div style={{
      height: isMobile ? "auto" : "calc(100vh - 112px)",
      display: "flex",
      flexDirection: isMobile ? "column" : "row",
      gap: isMobile ? 12 : 16,
    }}>
      {/* Left: iframe preview */}
      <div style={{
        flex: isMobile ? undefined : 1,
        background: "#fff",
        borderRadius: 12,
        overflow: "hidden",
        height: isMobile ? "60vh" : undefined,
        minHeight: isMobile ? 300 : undefined,
        border: "1px solid #f1f5f9",
      }}>
        <iframe
          src={`/files/${page.slug}/${page.entry_file}`}
          style={{
            width: "100%",
            height: "100%",
            border: "none",
          }}
          sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups"
          title={page.title}
        />
      </div>

      {/* Right: metadata panel */}
      <div style={{
        width: isMobile ? "100%" : 320,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate("/")}
          style={{ alignSelf: "flex-start" }}
        >
          返回列表
        </Button>

        <Card style={{ flex: isMobile ? undefined : 1, borderRadius: 12, border: "1px solid #f1f5f9" }}>
          <div style={{ marginBottom: 12 }}>
            <Space>
              <Button
                type="primary"
                size="small"
                icon={<EditOutlined />}
                onClick={() => setShowEdit(true)}
              >
                编辑
              </Button>
            </Space>
          </div>

          <Title level={4} style={{ marginTop: 0 }}>{page.title}</Title>

          {page.description && (
            <Text type="secondary" style={{ fontSize: 13, display: "block", marginBottom: 16 }}>
              {page.description}
            </Text>
          )}

          {page.tags.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              {page.tags.map((t) => (
                <Tag key={t.id} color="blue">{t.name}</Tag>
              ))}
            </div>
          )}

          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="目录名">{page.slug}</Descriptions.Item>
            <Descriptions.Item label="入口文件">{page.entry_file}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(page.created_at).format("YYYY-MM-DD HH:mm")}
            </Descriptions.Item>
            <Descriptions.Item label="最后同步">
              {dayjs(page.synced_at).fromNow()}
            </Descriptions.Item>
            <Descriptions.Item label="用户编辑">
              {page.is_customized ? "是" : "否"}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>

      {/* Edit modal */}
      {showEdit && (
        <EditProjectModal
          page={page}
          visible={showEdit}
          onClose={() => setShowEdit(false)}
          onSave={() => {
            setShowEdit(false);
            fetchPage(Number(id)).then(setPage);
          }}
        />
      )}
    </div>
  );
}
