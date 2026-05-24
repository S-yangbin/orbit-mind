import { Card, Tag, Space, Tooltip, Typography } from "antd";
import { EyeOutlined, EditOutlined, ClockCircleOutlined } from "@ant-design/icons";
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
          <div style={{ height: 160, overflow: "hidden", background: "#f0f0f0" }}>
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
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <span style={{ fontSize: 48 }}>📄</span>
          </div>
        )
      }
      actions={[
        <div key="actions" style={{ display: "flex", justifyContent: "space-around" }}>
          <Tooltip title="预览">
            <EyeOutlined
              onClick={() => navigate(`/preview/${page.id}`)}
              style={{ fontSize: 16, cursor: "pointer" }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <EditOutlined
              onClick={() => onEdit(page)}
              style={{ fontSize: 16, cursor: "pointer" }}
            />
          </Tooltip>
        </div>,
      ]}
      style={{ borderRadius: 8 }}
    >
      <Card.Meta
        title={<Text strong ellipsis>{page.title}</Text>}
        description={
          <div>
            <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 8 }}>
              {page.description?.slice(0, 80)}
              {page.description && page.description.length > 80 ? "..." : ""}
            </Text>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
              {page.tags.slice(0, 3).map((t) => (
                <Tag key={t.id} color="blue" style={{ fontSize: 11 }}>{t.name}</Tag>
              ))}
              {page.tags.length > 3 && (
                <Tag style={{ fontSize: 11 }}>+{page.tags.length - 3}</Tag>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: 11 }}>
              <ClockCircleOutlined /> {dayjs(page.synced_at).fromNow()}
            </Text>
          </div>
        }
      />
    </Card>
  );
}
