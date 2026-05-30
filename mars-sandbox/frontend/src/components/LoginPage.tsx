import { useState } from "react";
import { Form, Input, Button, Card, message, Typography } from "antd";
import { UserOutlined, LockOutlined, RocketOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const { Title, Text } = Typography;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    const ok = await login(values.username, values.password);
    setLoading(false);
    if (ok) {
      message.success("登录成功");
      navigate("/");
    } else {
      message.error("用户名或密码错误");
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4c1d95 100%)",
      padding: 16,
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Decorative background elements */}
      <div style={{
        position: "absolute",
        top: -120,
        right: -80,
        width: 300,
        height: 300,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(139,92,246,0.25) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute",
        bottom: -100,
        left: -60,
        width: 250,
        height: 250,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <Card
        style={{
          width: "100%",
          maxWidth: 380,
          border: "none",
          borderRadius: 16,
          boxShadow: "0 25px 50px -12px rgba(0,0,0,0.4)",
        }}
        styles={{ body: { padding: "36px 32px 28px" } }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          {/* Brand icon */}
          <div style={{
            width: 60,
            height: 60,
            borderRadius: 16,
            background: "linear-gradient(135deg, #7c3aed, #6366f1)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 16,
            boxShadow: "0 8px 20px rgba(124,58,237,0.3)",
          }}>
            <RocketOutlined style={{ fontSize: 28, color: "#fff" }} />
          </div>
          <Title level={3} style={{ margin: "0 0 6px", color: "#0f172a", fontWeight: 700 }}>
            Mars Sandbox
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            个人 HTML 页面托管与智能管理中心
          </Text>
        </div>

        <Form onFinish={onFinish} size="large" layout="vertical">
          <Form.Item
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
            style={{ marginBottom: 16 }}
          >
            <Input
              prefix={<UserOutlined style={{ color: "#94a3b8" }} />}
              placeholder="用户名"
              style={{ borderRadius: 8, height: 44 }}
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: "请输入密码" }]}
            style={{ marginBottom: 24 }}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: "#94a3b8" }} />}
              placeholder="密码"
              style={{ borderRadius: 8, height: 44 }}
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loading}
              style={{
                height: 44,
                borderRadius: 8,
                fontWeight: 600,
                fontSize: 15,
              }}
            >
              登 录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
