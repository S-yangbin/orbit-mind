import { useState } from "react";
import { Tabs } from "antd";
import {
  CalendarOutlined,
  CameraOutlined,
  HistoryOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { MealPlanner } from "./MealPlanner";
import { MealRecorder } from "./MealRecorder";
import { MealHistory } from "./MealHistory";
import { FamilySettings } from "./FamilySettings";

const TAB_ITEMS = [
  {
    key: "plan",
    label: (
      <span>
        <CalendarOutlined /> 周末菜单
      </span>
    ),
    children: <MealPlanner />,
  },
  {
    key: "record",
    label: (
      <span>
        <CameraOutlined /> 拍照记录
      </span>
    ),
    children: <MealRecorder />,
  },
  {
    key: "history",
    label: (
      <span>
        <HistoryOutlined /> 历史统计
      </span>
    ),
    children: <MealHistory />,
  },
  {
    key: "settings",
    label: (
      <span>
        <SettingOutlined /> 设置
      </span>
    ),
    children: <FamilySettings />,
  },
];

export function MealManagement() {
  const [activeKey, setActiveKey] = useState("plan");
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
