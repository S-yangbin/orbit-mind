import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Row, Col, Card, Button, Tag, Spin, Empty, Progress, Typography, Space, Tooltip, message,
} from "antd";
import {
  PlusOutlined,
  PlayCircleOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  RedoOutlined,
} from "@ant-design/icons";
import { fetchVideos, processVideo } from "../api/videos";
import type { VideoInfo } from "../types";
import { VideoUpload } from "./VideoUpload";
import { useIsMobile } from "../hooks/useIsMobile";
import { formatSize } from "../utils";

const { Title, Text } = Typography;

const STATUS_MAP: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  pending: { color: "default", icon: <ClockCircleOutlined />, label: "待处理" },
  processing: { color: "processing", icon: <LoadingOutlined />, label: "分析中" },
  ready: { color: "success", icon: <CheckCircleOutlined />, label: "已完成" },
  error: { color: "error", icon: <ExclamationCircleOutlined />, label: "失败" },
};

export function VideoList() {
  const navigate = useNavigate();
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [showUpload, setShowUpload] = useState(false);
  const isMobile = useIsMobile();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchVideos({ page, page_size: 20, sort: "created_at", order: "desc" });
      setVideos(data.items);
      setTotal(data.total);
    } catch {
      // ignore
    }
    setLoading(false);
  }, [page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const hasProcessing = videos.some((v) => v.status === "processing" || v.status === "pending");
    if (!hasProcessing) return;
    const timer = setInterval(loadData, 5000);
    return () => clearInterval(timer);
  }, [videos, loadData]);

  const handleRetry = async (e: React.MouseEvent, videoId: number) => {
    e.stopPropagation();
    try {
      await processVideo(videoId);
      message.success("已重新开始处理");
      loadData();
    } catch {
      message.error("重试失败");
    }
  };

  return (
    <div>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: isMobile ? 16 : 24,
        flexWrap: "wrap",
        gap: 8,
      }}>
        <Title level={isMobile ? 4 : 3} style={{ margin: 0, fontWeight: 700, color: "#0f172a" }}>
          作业视频
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setShowUpload(true)}
          style={{ borderRadius: 8, fontWeight: 500 }}
        >
          {isMobile ? "上传" : "上传视频"}
        </Button>
      </div>

      <Spin spinning={loading}>
        {videos.length === 0 && !loading ? (
          <Empty
            description="暂无视频，点击「上传视频」添加第一个作业视频"
            style={{ padding: "60px 0" }}
          />
        ) : (
          <Row gutter={[isMobile ? 12 : 16, isMobile ? 12 : 16]}>
            {videos.map((v) => {
              const segCount = v.segment_count ?? v.segments?.length ?? 0;
              const masteredCount = v.mastered_count ?? 0;
              const progressPct = segCount > 0 ? Math.round((masteredCount / segCount) * 100) : 0;
              const statusInfo = STATUS_MAP[v.status] || STATUS_MAP.pending;

              return (
                <Col xs={24} sm={12} md={8} lg={6} key={v.id}>
                  <Card
                    hoverable
                    onClick={() => navigate(`/videos/${v.id}`)}
                    cover={
                      <div style={{
                        height: 140,
                        background: "linear-gradient(135deg, #ede9fe 0%, #e0e7ff 50%, #dbeafe 100%)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}>
                        <PlayCircleOutlined style={{ fontSize: 44, color: "#7c3aed", opacity: 0.5 }} />
                      </div>
                    }
                    actions={[
                      <Tooltip title="查看详情" key="view">
                        <PlayCircleOutlined
                          style={{ color: "#64748b" }}
                          onClick={(e) => { e.stopPropagation(); navigate(`/videos/${v.id}`); }}
                        />
                      </Tooltip>,
                      ...(v.status === "error" ? [
                        <Tooltip title="重试处理" key="retry">
                          <RedoOutlined
                            style={{ color: "#64748b" }}
                            onClick={(e) => handleRetry(e, v.id)}
                          />
                        </Tooltip>,
                      ] : []),
                    ]}
                    style={{ borderRadius: 12, border: "1px solid #f1f5f9", overflow: "hidden" }}
                    styles={{ body: { padding: "12px 16px" } }}
                  >
                    <Card.Meta
                      title={
                        <Space size={6}>
                          <span style={{ fontSize: 14, fontWeight: 600 }}>{v.title}</span>
                          <Tag
                            color={statusInfo.color}
                            icon={statusInfo.icon}
                            style={{ borderRadius: 10, fontSize: 11, margin: 0 }}
                          >
                            {statusInfo.label}
                          </Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <Text type="secondary" style={{ fontSize: 12, display: "block" }}>
                            {formatSize(v.file_size)} · {segCount} 个分段
                          </Text>
                          {v.status === "ready" && segCount > 0 && (
                            <div style={{ marginTop: 8 }}>
                              <Progress
                                percent={progressPct}
                                size="small"
                                format={() => `${masteredCount}/${segCount} 已掌握`}
                                strokeColor="#10b981"
                              />
                            </div>
                          )}
                          {v.status === "error" && (
                            <Text type="danger" style={{ fontSize: 12 }}>
                              {v.error_message?.slice(0, 60)}
                            </Text>
                          )}
                        </div>
                      }
                    />
                  </Card>
                </Col>
              );
            })}
          </Row>
        )}
      </Spin>

      <VideoUpload
        visible={showUpload}
        onClose={() => setShowUpload(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
