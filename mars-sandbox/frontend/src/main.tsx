import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import App from "./App";
import "./global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#7c3aed",
          colorLink: "#7c3aed",
          colorBgLayout: "#f8fafc",
          colorBorder: "#e2e8f0",
          colorBorderSecondary: "#f1f5f9",
          borderRadius: 8,
          borderRadiusLG: 12,
          controlHeight: 38,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
          colorText: "#0f172a",
          colorTextSecondary: "#64748b",
          colorTextTertiary: "#94a3b8",
          boxShadow: "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06)",
          boxShadowSecondary: "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)",
        },
        components: {
          Card: {
            boxShadowTertiary: "0 1px 3px 0 rgba(0,0,0,0.05)",
          },
          Menu: {
            itemSelectedColor: "#7c3aed",
            itemHoverColor: "#7c3aed",
          },
          Button: {
            primaryShadow: "0 2px 4px rgba(124,58,237,0.2)",
          },
          Table: {
            headerBg: "#f8fafc",
            headerColor: "#475569",
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
