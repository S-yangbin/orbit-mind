import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Card,
  Row,
  Col,
  Statistic,
  Badge,
  Button,
  Space,
  Popconfirm,
  message,
  Tooltip,
  Switch,
  Typography,
} from "antd";
import {
  ReloadOutlined,
  DeleteOutlined,
  DesktopOutlined,
  WifiOutlined,
  DisconnectOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { fetchNodes, deleteNode } from "../api/nodes";
import type { NodeInfo } from "../types";

dayjs.extend(relativeTime);

const { Text } = Typography;

export function NodeManagement() {
  const [nodes, setNodes] = useState<NodeInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [online, setOnline] = useState(0);
  const [offline, setOffline] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchNodes();
      setNodes(data.nodes);
      setTotal(data.total);
      setOnline(data.online);
      setOffline(data.offline);
    } catch (e) {
      console.error("Failed to load nodes:", e);
      message.error("加载节点列表失败");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 10s
  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(loadData, 10000);
    return () => clearInterval(timer);
  }, [autoRefresh, loadData]);

  const handleDelete = async (nodeId: string) => {
    try {
      await deleteNode(nodeId);
      message.success(`节点 "${nodeId}" 已删除`);
      loadData();
    } catch {
      message.error("删除节点失败");
    }
  };

  const columns: ColumnsType<NodeInfo> = [
    {
      title: "状态",
      dataIndex: "status",
      width: 90,
      filters: [
        { text: "在线", value: "online" },
        { text: "离线", value: "offline" },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status: string) => (
        <Badge
          status={status === "online" ? "success" : "error"}
          text={status === "online" ? "在线" : "离线"}
        />
      ),
    },
    {
      title: "节点 ID",
      dataIndex: "node_id",
      sorter: (a, b) => a.node_id.localeCompare(b.node_id),
      render: (id: string) => <Text strong copyable={{ text: id }}>{id}</Text>,
    },
    {
      title: "主机名",
      dataIndex: "hostname",
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "IP 地址",
      dataIndex: "ip",
      width: 140,
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "平台",
      dataIndex: "platform",
      width: 120,
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "版本",
      dataIndex: "version",
      width: 90,
    },
    {
      title: "运行时长",
      dataIndex: "uptime",
      width: 120,
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "最后心跳",
      dataIndex: "last_heartbeat_at",
      width: 150,
      sorter: (a, b) =>
        (a.last_heartbeat_at || "").localeCompare(b.last_heartbeat_at || ""),
      render: (v: string | null) =>
        v ? (
          <Tooltip title={dayjs(v).format("YYYY-MM-DD HH:mm:ss")}>
            {dayjs(v).fromNow()}
          </Tooltip>
        ) : (
          <Text type="secondary">从未上线</Text>
        ),
    },
    {
      title: "操作",
      key: "action",
      width: 80,
      render: (_, record) => (
        <Popconfirm
          title="确认删除"
          description={`确定要删除节点 "${record.node_id}" 吗？`}
          onConfirm={() => handleDelete(record.node_id)}
          okText="删除"
          cancelText="取消"
          okButtonProps={{ danger: true }}
        >
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            size="small"
          />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 24,
      }}>
        <span style={{ fontSize: 20, fontWeight: 600 }}>节点管理</span>
        <Space>
          <span style={{ fontSize: 13, color: "#888" }}>自动刷新</span>
          <Switch
            size="small"
            checked={autoRefresh}
            onChange={setAutoRefresh}
          />
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={8}>
          <Card>
            <Statistic
              title="总节点数"
              value={total}
              prefix={<DesktopOutlined />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card>
            <Statistic
              title="在线"
              value={online}
              valueStyle={{ color: "#52c41a" }}
              prefix={<WifiOutlined />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card>
            <Statistic
              title="离线"
              value={offline}
              valueStyle={{ color: "#ff4d4f" }}
              prefix={<DisconnectOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Table<NodeInfo>
          rowKey="node_id"
          columns={columns}
          dataSource={nodes}
          loading={loading}
          pagination={false}
          size="middle"
          locale={{ emptyText: "暂无注册节点" }}
        />
      </Card>
    </div>
  );
}
