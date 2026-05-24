import { useState, useRef, useEffect } from "react";
import {
  Modal,
  Input,
  Button,
  Space,
  Typography,
  Tag,
  InputNumber,
  Divider,
  Alert,
  Spin,
  Tooltip,
} from "antd";
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  CopyOutlined,
  ClearOutlined,
} from "@ant-design/icons";
import { executeNodeCommand } from "../api/nodes";
import type { NodeCommandResponse } from "../types";

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const PRESET_COMMANDS = [
  { label: "系统信息", cmd: "uname -a" },
  { label: "磁盘使用", cmd: "df -h" },
  { label: "内存使用", cmd: "free -h" },
  { label: "CPU 信息", cmd: "lscpu" },
  { label: "网络状态", cmd: "ip addr" },
  { label: "进程列表", cmd: "ps aux" },
  { label: "系统负载", cmd: "uptime" },
];

interface CommandModalProps {
  open: boolean;
  nodeId: string;
  onClose: () => void;
}

export function CommandModal({ open, nodeId, onClose }: CommandModalProps) {
  const [command, setCommand] = useState("");
  const [timeout, setTimeout] = useState(30);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NodeCommandResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setCommand("");
      setResult(null);
      setError(null);
    }
  }, [open]);

  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [result]);

  const handleExecute = async () => {
    if (!command.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await executeNodeCommand(nodeId, {
        command: command.trim(),
        timeout,
      });
      setResult(res);
      // Add to history (deduplicate, max 10)
      setHistory((prev) => {
        const filtered = prev.filter((c) => c !== command.trim());
        return [command.trim(), ...filtered].slice(0, 10);
      });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      const msg =
        err.response?.data?.detail || "命令执行失败，请检查节点状态";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleExecute();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Modal
      title={
        <Space>
          <PlayCircleOutlined />
          <span>执行命令</span>
          <Tag color="blue">{nodeId}</Tag>
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={720}
      footer={null}
      destroyOnClose
    >
      <div style={{ marginBottom: 12 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          预设命令
        </Text>
        <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 6 }}>
          {PRESET_COMMANDS.map((p) => (
            <Tooltip key={p.cmd} title={p.cmd}>
              <Tag
                style={{ cursor: "pointer", userSelect: "none" }}
                onClick={() => setCommand(p.cmd)}
                color="default"
              >
                {p.label}
              </Tag>
            </Tooltip>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <TextArea
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入要执行的命令... (Ctrl+Enter 执行)"
          autoSize={{ minRows: 2, maxRows: 4 }}
          disabled={loading}
        />
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <Space>
          <Text type="secondary" style={{ fontSize: 13 }}>
            超时(秒):
          </Text>
          <InputNumber
            min={5}
            max={300}
            value={timeout}
            onChange={(v) => setTimeout(v || 30)}
            size="small"
            disabled={loading}
          />
          {history.length > 0 && (
            <>
              <Divider type="vertical" />
              <Text type="secondary" style={{ fontSize: 12 }}>
                历史:
              </Text>
              {history.slice(0, 3).map((cmd, i) => (
                <Tag
                  key={i}
                  style={{ cursor: "pointer", fontSize: 11 }}
                  onClick={() => setCommand(cmd)}
                >
                  {cmd.length > 20 ? cmd.slice(0, 20) + "..." : cmd}
                </Tag>
              ))}
            </>
          )}
        </Space>
        <Space>
          <Button
            icon={<ClearOutlined />}
            size="small"
            onClick={() => {
              setResult(null);
              setError(null);
            }}
          >
            清除结果
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleExecute}
            loading={loading}
            disabled={!command.trim()}
          >
            执行
          </Button>
        </Space>
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "24px 0" }}>
          <Spin tip="命令执行中，请稍候..." />
        </div>
      )}

      {error && (
        <Alert
          type="error"
          showIcon
          message="执行失败"
          description={error}
          style={{ marginBottom: 12 }}
          closable
          onClose={() => setError(null)}
        />
      )}

      {result && (
        <div ref={resultRef}>
          <Divider style={{ margin: "8px 0 12px" }} />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 8,
            }}
          >
            <Space>
              {result.exit_code === 0 ? (
                <Tag icon={<CheckCircleOutlined />} color="success">
                  成功 (exit: 0)
                </Tag>
              ) : (
                <Tag icon={<CloseCircleOutlined />} color="error">
                  失败 (exit: {result.exit_code})
                </Tag>
              )}
              <Tag icon={<ClockCircleOutlined />} color="default">
                {result.duration_ms}ms
              </Tag>
            </Space>
          </div>

          {result.stdout && (
            <div style={{ marginBottom: 12 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 4,
                }}
              >
                <Text type="secondary" style={{ fontSize: 12 }}>
                  stdout
                </Text>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(result.stdout)}
                >
                  复制
                </Button>
              </div>
              <Paragraph
                style={{
                  background: "#1e1e1e",
                  color: "#d4d4d4",
                  padding: "12px",
                  borderRadius: 6,
                  fontSize: 13,
                  fontFamily:
                    "'Menlo', 'Monaco', 'Courier New', monospace",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  maxHeight: 300,
                  overflow: "auto",
                  margin: 0,
                }}
              >
                {result.stdout}
              </Paragraph>
            </div>
          )}

          {result.stderr && (
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 4,
                }}
              >
                <Text type="secondary" style={{ fontSize: 12 }}>
                  stderr
                </Text>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(result.stderr)}
                >
                  复制
                </Button>
              </div>
              <Paragraph
                style={{
                  background: "#2d1117",
                  color: "#f48771",
                  padding: "12px",
                  borderRadius: 6,
                  fontSize: 13,
                  fontFamily:
                    "'Menlo', 'Monaco', 'Courier New', monospace",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  maxHeight: 200,
                  overflow: "auto",
                  margin: 0,
                }}
              >
                {result.stderr}
              </Paragraph>
            </div>
          )}

          {!result.stdout && !result.stderr && (
            <Alert
              type="info"
              showIcon
              message="命令执行完成，无输出"
              style={{ marginTop: 8 }}
            />
          )}
        </div>
      )}
    </Modal>
  );
}
