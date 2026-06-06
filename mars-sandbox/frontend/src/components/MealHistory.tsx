import { useEffect, useState, useCallback } from "react";
import {
  Card,
  Row,
  Col,
  Statistic,
  List,
  Tag,
  Progress,
  Typography,
  Spin,
  Image,
  Space,
  Empty,
  Pagination,
  Rate,
} from "antd";
import {
  RiseOutlined,
  AppstoreOutlined,
  SyncOutlined,
  SunOutlined,
  CloudOutlined,
} from "@ant-design/icons";
import type { MealLog, MealHistoryStats } from "../types";
import { fetchMealLogs, fetchHistoryStats } from "../api/meals";
import { useIsMobile } from "../hooks/useIsMobile";
import { mealPhotoToUrl } from "../utils";

const { Text, Title } = Typography;

const MEAL_LABELS: Record<string, string> = {
  breakfast: "早餐",
  lunch: "午餐",
};
const MEAL_ICONS: Record<string, React.ReactNode> = {
  breakfast: <CloudOutlined style={{ color: "#f59e0b" }} />,
  lunch: <SunOutlined style={{ color: "#f59e0b" }} />,
};

export function MealHistory() {
  const [stats, setStats] = useState<MealHistoryStats | null>(null);
  const [logs, setLogs] = useState<MealLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const isMobile = useIsMobile();

  const loadData = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const [statsData, logsData] = await Promise.all([
        fetchHistoryStats(14),
        fetchMealLogs(p, 15),
      ]);
      setStats(statsData);
      setLogs(logsData.items);
      setTotal(logsData.total);
      setPage(p);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(1);
  }, [loadData]);

  if (loading && !stats) {
    return <Spin size="large" style={{ display: "block", margin: "80px auto" }} />;
  }

  const maxRepeat = stats?.top_repeated?.[0]?.count || 1;

  return (
    <div>
      {/* Stats overview */}
      <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 16]} style={{ marginBottom: isMobile ? 16 : 24 }}>
        <Col xs={8}>
          <Card
            size="small"
            style={{ borderRadius: 12, borderLeft: "3px solid #7c3aed" }}
            styles={{ body: { padding: isMobile ? "10px 12px" : "14px 16px" } }}
          >
            <Statistic
              title={<span style={{ fontSize: 12, color: "#94a3b8" }}>近2周用餐</span>}
              value={stats?.total_meals || 0}
              suffix="餐"
              prefix={<AppstoreOutlined style={{ color: "#7c3aed" }} />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card
            size="small"
            style={{ borderRadius: 12, borderLeft: "3px solid #06b6d4" }}
            styles={{ body: { padding: isMobile ? "10px 12px" : "14px 16px" } }}
          >
            <Statistic
              title={<span style={{ fontSize: 12, color: "#94a3b8" }}>菜品种类</span>}
              value={stats?.unique_dishes || 0}
              suffix="道"
              prefix={<RiseOutlined style={{ color: "#06b6d4" }} />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card
            size="small"
            style={{ borderRadius: 12, borderLeft: `3px solid ${(stats?.repeat_rate || 0) > 0.4 ? "#ef4444" : "#10b981"}` }}
            styles={{ body: { padding: isMobile ? "10px 12px" : "14px 16px" } }}
          >
            <Statistic
              title={<span style={{ fontSize: 12, color: "#94a3b8" }}>重复率</span>}
              value={((stats?.repeat_rate || 0) * 100).toFixed(0)}
              suffix="%"
              prefix={<SyncOutlined />}
              valueStyle={{
                color: (stats?.repeat_rate || 0) > 0.4 ? "#ef4444" : "#10b981",
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Top repeated dishes */}
      {stats && stats.top_repeated.length > 0 && (
        <Card
          title={<span style={{ fontWeight: 600 }}>近2周最常出现的菜品</span>}
          size="small"
          style={{ marginBottom: isMobile ? 16 : 24, borderRadius: 12, border: "1px solid #f1f5f9" }}
        >
          {stats.top_repeated.map((d, i) => (
            <div key={d.name} style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <Space size={6}>
                  <Text strong style={{ fontSize: 13 }}>{d.name}</Text>
                  <Tag style={{ borderRadius: 10, fontSize: 11, margin: 0 }}>
                    {d.category || "其他"}
                  </Tag>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>{d.count} 次</Text>
              </div>
              <Progress
                percent={Math.round((d.count / maxRepeat) * 100)}
                showInfo={false}
                strokeColor={i < 3 ? "#f97316" : "#7c3aed"}
                size="small"
              />
            </div>
          ))}
        </Card>
      )}

      {/* Meal timeline */}
      <Title level={5} style={{ fontWeight: 600, marginBottom: 12 }}>用餐记录</Title>
      {logs.length === 0 ? (
        <Empty description="暂无用餐记录，去拍照记录吧" />
      ) : (
        <>
          <List
            itemLayout="horizontal"
            dataSource={logs}
            renderItem={(log) => (
              <List.Item style={{ padding: isMobile ? "10px 0" : "14px 0" }}>
                <List.Item.Meta
                  avatar={
                    <Image
                      src={log.image_path ? mealPhotoToUrl(log.image_path) : ""}
                      width={isMobile ? 52 : 64}
                      height={isMobile ? 52 : 64}
                      style={{ objectFit: "cover", borderRadius: 10 }}
                      fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNjY2MiIGZvbnQtc2l6ZT0iMjAiPvCfjZc8L3RleHQ+PC9zdmc+"
                    />
                  }
                  title={
                    <Space size={6} wrap>
                      <Text strong style={{ fontSize: 13 }}>{log.date}</Text>
                      <Space size={4}>
                        {MEAL_ICONS[log.meal_type]}
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {MEAL_LABELS[log.meal_type]}
                        </Text>
                      </Space>
                      {log.rating && <Rate disabled value={log.rating} style={{ fontSize: 12 }} />}
                    </Space>
                  }
                  description={
                    <div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                        {log.dishes.map((d) => (
                          <Tag key={d.name} style={{ borderRadius: 10, fontSize: 12, margin: 0 }}>
                            {d.name}
                          </Tag>
                        ))}
                      </div>
                      {log.note && (
                        <div style={{ marginTop: 6 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {log.note}
                          </Text>
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
          {total > 15 && (
            <div style={{ textAlign: "center", marginTop: 16, paddingBottom: 16 }}>
              <Pagination
                current={page}
                total={total}
                pageSize={15}
                onChange={loadData}
                showSizeChanger={false}
                simple={isMobile}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
