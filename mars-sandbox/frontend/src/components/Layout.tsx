import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Drawer } from "antd";
import {
  HomeOutlined,
  LogoutOutlined,
  RocketOutlined,
  ClusterOutlined,
  PlayCircleOutlined,
  CoffeeOutlined,
  CloudOutlined,
  MenuOutlined,
  MessageOutlined,
  DashboardOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import { useIsMobile } from "../hooks/useIsMobile";

const { Header, Content } = AntLayout;

const NAV_ITEMS = [
  { key: "/", icon: <HomeOutlined />, label: "页面" },
  { key: "/nodes", icon: <ClusterOutlined />, label: "节点" },
  { key: "/videos", icon: <PlayCircleOutlined />, label: "视频" },
  { key: "/meals", icon: <CoffeeOutlined />, label: "吃什么" },
  { key: "/drive", icon: <CloudOutlined />, label: "云盘" },
  { key: "/board", icon: <MessageOutlined />, label: "留言板" },
  { key: "/dashboard", icon: <DashboardOutlined />, label: "看板" },
];

export function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const selectedKey = NAV_ITEMS.find(
    (item) => item.key !== "/" && location.pathname.startsWith(item.key)
  )?.key || "/";

  const handleNav = (key: string) => {
    navigate(key);
    setDrawerOpen(false);
  };

  return (
    <AntLayout style={{ minHeight: "100vh", background: "#f8fafc" }}>
      <Header style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "#fff",
        borderBottom: "1px solid #f1f5f9",
        padding: isMobile ? "0 12px" : "0 32px",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxShadow: "0 1px 3px 0 rgba(0,0,0,0.04)",
        height: isMobile ? 52 : 64,
        lineHeight: isMobile ? "52px" : "64px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: isMobile ? 8 : 16, flex: 1, minWidth: 0 }}>
          {isMobile ? (
            <>
              <Button
                type="text"
                icon={<MenuOutlined style={{ fontSize: 18, color: "#475569" }} />}
                onClick={() => setDrawerOpen(true)}
                style={{ padding: 6, borderRadius: 8 }}
              />
              <div style={{
                width: 30,
                height: 30,
                borderRadius: 8,
                background: "linear-gradient(135deg, #7c3aed, #6366f1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}>
                <RocketOutlined style={{ fontSize: 14, color: "#fff" }} />
              </div>
              <span style={{ fontSize: 16, fontWeight: 700, color: "#0f172a", whiteSpace: "nowrap" }}>
                Mars
              </span>
            </>
          ) : (
            <>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: "linear-gradient(135deg, #7c3aed, #6366f1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                boxShadow: "0 4px 12px rgba(124,58,237,0.2)",
              }}>
                <RocketOutlined style={{ fontSize: 17, color: "#fff" }} />
              </div>
              <span style={{ fontSize: 17, fontWeight: 700, color: "#0f172a", whiteSpace: "nowrap" }}>
                Mars Sandbox
              </span>
              <Menu
                mode="horizontal"
                selectedKeys={[selectedKey]}
                items={NAV_ITEMS}
                onClick={({ key }) => navigate(key)}
                disabledOverflow
                style={{
                  border: "none",
                  marginLeft: 24,
                  flex: 1,
                  background: "transparent",
                  fontSize: 14,
                  fontWeight: 500,
                }}
              />
            </>
          )}
        </div>
        {!isMobile && (
          <Button
            icon={<LogoutOutlined />}
            onClick={logout}
            style={{ borderRadius: 8, fontWeight: 500 }}
          >
            退出
          </Button>
        )}
      </Header>

      {/* Mobile drawer navigation */}
      <Drawer
        title={null}
        placement="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={280}
        styles={{
          body: { padding: 0 },
          header: { display: "none" },
        }}
      >
        {/* Drawer header */}
        <div style={{
          padding: "20px 20px 16px",
          background: "linear-gradient(135deg, #7c3aed, #6366f1)",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: "rgba(255,255,255,0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <RocketOutlined style={{ fontSize: 18, color: "#fff" }} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>Mars Sandbox</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.8)" }}>智能管理中心</div>
          </div>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={NAV_ITEMS}
          onClick={({ key }) => handleNav(key)}
          style={{
            border: "none",
            paddingTop: 8,
            fontWeight: 500,
          }}
        />

        <div style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: "16px 20px",
          borderTop: "1px solid #f1f5f9",
          background: "#fff",
        }}>
          <Button
            icon={<LogoutOutlined />}
            onClick={logout}
            block
            style={{ borderRadius: 8 }}
          >
            退出登录
          </Button>
        </div>
      </Drawer>

      <Content style={{
        padding: isMobile ? "12px" : "24px 32px",
        background: "#f8fafc",
        minHeight: `calc(100vh - ${isMobile ? 52 : 64}px)`,
        maxWidth: 1400,
        width: "100%",
        margin: "0 auto",
      }}>
        <div className="page-enter">
          <Outlet />
        </div>
      </Content>
    </AntLayout>
  );
}
