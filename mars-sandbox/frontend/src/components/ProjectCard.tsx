import { Card, Tag, Space, Tooltip, Typography } from "antd";
import { EyeOutlined, EditOutlined, ClockCircleOutlined, FileTextOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/zh-cn";
import type { Page } from "../types";

dayjs.extend(relativeTime);
dayjs.locale("zh-cn");

const { Text } = Typography;

interface Props {
  page: Page;
  onEdit: (page: Page) => void;
}

export function ProjectCard({ page, onEdit }: Props) {
  const navigate = useNavigate();
  const thumbSrc = page.thumbnail ? `/thumbnails/${page.slug}.png` : undefined;

  return (
    <Card
      hoverable
      cover={
        thumbSrc ? (
          <div style={{ height: 160, overflow: "hidden", background: "#f1f5f9" }}>
            <img
              src={thumbSrc}
              alt={page.title}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
        ) : (
          <div style={{
            height: 160,
            background: "linear-gradient(135deg, #ede9fe 0%, #e0e7ff 50%, #dbeafe 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <FileTextOutlined style={{ fontSize: 40, color: "#8b5cf6", opacity: 0.6 }} />
          </div>
        )
      }
      actions={[
        <Tooltip title="预览" key="view">
          <EyeOutlined
            onClick={() => navigate(`/preview/${page.id}`)}
            style={{ fontSize: 16, cursor: "pointer", color: "#64748b" }}
          />
        </Tooltip>,
        <Tooltip title="编辑" key="edit">
          <EditOutlined
            onClick={() => onEdit(page)}
            style={{ fontSize: 16, cursor: "pointer", color: "#64748b" }}
          />
        </Tooltip>,
      ]}
      style={{
        borderRadius: 12,
        overflow: "hidden",
        border: "1px solid #f1f5f9",
      }}
      styles={{ body: { padding: "14px 16px" } }}
    >
      <Card.Meta
        title={
          <Text strong ellipsis style={{ fontSize: 14, fontWeight: 600 }}>
            {page.title}
          </Text>
        }
        description={
          <div>
            {page.description && (
              <Text
                type="secondary"
                style={{
                  fontSize: 12,
                  display: "-webkit-box",
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                  lineHeight: "18px",
                  marginBottom: 8,
                }}
              >
                {page.description}
              </Text>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
              {page.tags.slice(0, 3).map((t) => (
                <Tag key={t.id} color="purple" style={{ fontSize: 11, borderRadius: 10, margin: 0 }}>
                  {t.name}
                </Tag>
              ))}
              {page.tags.length > 3 && (
                <Tag style={{ fontSize: 11, borderRadius: 10, margin: 0 }}>
                  +{page.tags.length - 3}
                </Tag>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: 11, color: "#94a3b8" }}>
              <ClockCircleOutlined style={{ marginRight: 4 }} />
              {dayjs(page.synced_at).fromNow()}
            </Text>
          </div>
        }
      />
    </Card>
  );
}
