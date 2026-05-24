import { Outlet } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Space } from "antd";
import {
  HomeOutlined,
  LogoutOutlined,
  RocketOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";

const { Header, Content } = AntLayout;

export function Layout() {
  const { logout } = useAuth();

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Header style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "#fff",
        borderBottom: "1px solid #f0f0f0",
        padding: "0 24px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <RocketOutlined style={{ fontSize: 24, color: "#722ed1" }} />
          <span style={{ fontSize: 18, fontWeight: 600 }}>Mars Sandbox</span>
        </div>
        <Space>
          <Button icon={<LogoutOutlined />} onClick={logout}>
            退出
          </Button>
        </Space>
      </Header>
      <Content style={{ padding: 24, background: "#f5f5f5", minHeight: "calc(100vh - 64px)" }}>
        <Outlet />
      </Content>
    </AntLayout>
  );
}
