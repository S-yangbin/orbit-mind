import { useState } from "react";
import { Tabs } from "antd";
import { UserOutlined, ClusterOutlined } from "@ant-design/icons";
import { FamilySettings } from "./FamilySettings";
import { NodeManagement } from "./NodeManagement";

const TAB_ITEMS = [
  {
    key: "members",
    label: (
      <span>
        <UserOutlined /> 人员管理
      </span>
    ),
    children: <FamilySettings />,
  },
  {
    key: "nodes",
    label: (
      <span>
        <ClusterOutlined /> 节点管理
      </span>
    ),
    children: <NodeManagement />,
  },
];

export function SettingsPage() {
  const [activeKey, setActiveKey] = useState("members");
  return (
    <div>
      <Tabs
        items={TAB_ITEMS}
        activeKey={activeKey}
        onChange={setActiveKey}
        destroyInactiveTabPane
        size="large"
      />
    </div>
  );
}
