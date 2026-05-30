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
  PlayCircleOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { fetchNodes, deleteNode } from "../api/nodes";
import type { NodeInfo } from "../types";
import { CommandModal } from "./CommandModal";
import { useIsMobile } from "../hooks/useIsMobile";

dayjs.extend(relativeTime);

const { Text } = Typography;

export function NodeManagement() {
  const [nodes, setNodes] = useState<NodeInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [online, setOnline] = useState(0);
  const [offline, setOffline] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [commandModalOpen, setCommandModalOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("");
  const isMobile = useIsMobile();

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
      width: 80,
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
      render: (id: string) => (
        <Text strong copyable={{ text: id }} style={{ fontSize: 13 }}>
          {isMobile ? id.slice(0, 12) + "..." : id}
        </Text>
      ),
    },
    {
      title: "主机名",
      dataIndex: "hostname",
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "IP 地址",
      dataIndex: "ip",
      width: 130,
      responsive: ["sm"],
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "平台",
      dataIndex: "platform",
      width: 100,
      responsive: ["md"],
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "版本",
      dataIndex: "version",
      width: 80,
      responsive: ["md"],
    },
    {
      title: "运行时长",
      dataIndex: "uptime",
      width: 100,
      responsive: ["sm"],
      render: (v: string) => v || <Text type="secondary">-</Text>,
    },
    {
      title: "最后心跳",
      dataIndex: "last_heartbeat_at",
      width: 130,
      sorter: (a, b) =>
        (a.last_heartbeat_at || "").localeCompare(b.last_heartbeat_at || ""),
      render: (v: string | null) =>
        v ? (
          <Tooltip title={dayjs(v).format("YYYY-MM-DD HH:mm:ss")}>
            <span style={{ fontSize: 13 }}>{dayjs(v).fromNow()}</span>
          </Tooltip>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>从未上线</Text>
        ),
    },
    {
      title: "操作",
      key: "action",
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title={record.status === "online" ? "执行命令" : "节点离线"}>
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              size="small"
              disabled={record.status !== "online"}
              onClick={() => {
                setSelectedNodeId(record.node_id);
                setCommandModalOpen(true);
              }}
              style={{ borderRadius: 6 }}
            />
          </Tooltip>
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
              style={{ borderRadius: 6 }}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

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
        <span style={{ fontSize: isMobile ? 18 : 20, fontWeight: 700, color: "#0f172a" }}>
          节点管理
        </span>
        <Space size={isMobile ? "small" : "middle"}>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>自动刷新</span>
          <Switch size="small" checked={autoRefresh} onChange={setAutoRefresh} />
          <Button
            icon={<ReloadOutlined />}
            onClick={loadData}
            loading={loading}
            size={isMobile ? "small" : "middle"}
          >
            {!isMobile && "刷新"}
          </Button>
        </Space>
      </div>

      {/* Stat cards with colored accents */}
      <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 16]} style={{ marginBottom: isMobile ? 16 : 24 }}>
        <Col xs={8}>
          <Card
            size="small"
            style={{ borderRadius: 12, borderLeft: "3px solid #7c3aed" }}
            styles={{ body: { padding: isMobile ? "10px 12px" : "14px 16px" } }}
          >
            <Statistic
              title={<span style={{ fontSize: 12, color: "#94a3b8" }}>总节点数</span>}
              value={total}
              prefix={<DesktopOutlined style={{ color: "#7c3aed" }} />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card
            size="small"
            style={{ borderRadius: 12, borderLeft: "3px solid #10b981" }}
            styles={{ body: { padding: isMobile ? "10px 12px" : "14px 16px" } }}
          >
            <Statistic
              title={<span style={{ fontSize: 12, color: "#94a3b8" }}>在线</span>}
              value={online}
              valueStyle={{ color: "#10b981" }}
              prefix={<WifiOutlined />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card
            size="small"
            style={{ borderRadius: 12, borderLeft: "3px solid #ef4444" }}
            styles={{ body: { padding: isMobile ? "10px 12px" : "14px 16px" } }}
          >
            <Statistic
              title={<span style={{ fontSize: 12, color: "#94a3b8" }}>离线</span>}
              value={offline}
              valueStyle={{ color: "#ef4444" }}
              prefix={<DisconnectOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ borderRadius: 12, border: "1px solid #f1f5f9" }}>
        <Table<NodeInfo>
          rowKey="node_id"
          columns={columns}
          dataSource={nodes}
          loading={loading}
          pagination={false}
          size={isMobile ? "small" : "middle"}
          scroll={{ x: 700 }}
          locale={{ emptyText: "暂无注册节点" }}
        />
      </Card>

      <CommandModal
        open={commandModalOpen}
        nodeId={selectedNodeId}
        onClose={() => setCommandModalOpen(false)}
      />
    </div>
  );
}
