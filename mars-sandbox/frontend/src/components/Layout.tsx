import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Space } from "antd";
import {
  HomeOutlined,
  LogoutOutlined,
  RocketOutlined,
  ClusterOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";

const { Header, Content } = AntLayout;

const NAV_ITEMS = [
  { key: "/", icon: <HomeOutlined />, label: "页面" },
  { key: "/nodes", icon: <ClusterOutlined />, label: "节点" },
];

export function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Match current path to nav key
  const selectedKey = NAV_ITEMS.find(
    (item) => item.key !== "/" && location.pathname.startsWith(item.key)
  )?.key || "/";

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
          <Menu
            mode="horizontal"
            selectedKeys={[selectedKey]}
            items={NAV_ITEMS}
            onClick={({ key }) => navigate(key)}
            style={{ border: "none", marginLeft: 24 }}
          />
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
