// ===== 文件大小格式化 =====
export function formatSize(bytes: number): string {
  if (bytes === 0) return "—";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// ===== 留言板颜色相关 =====

/** 命名颜色 → hex 映射（向后兼容旧数据） */
export const NAMED_COLOR_MAP: Record<string, string> = {
  yellow: "#fef9c3",
  pink: "#fce7f3",
  blue: "#dbeafe",
  green: "#dcfce7",
};

/** 兼容命名颜色和 hex 颜色 */
export function resolveColor(color: string): string {
  return NAMED_COLOR_MAP[color] || color;
}

/** 将 hex 颜色与白色混合，生成浅色背景（ratio 0~1，越小越白） */
export function tintBackground(hex: string, ratio = 0.4): string {
  const h = hex.replace("#", "");
  if (h.length !== 6) return hex;
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const blend = (c: number) => Math.round(c * ratio + 255 * (1 - ratio));
  const toHex = (n: number) => n.toString(16).padStart(2, "0");
  return `#${toHex(blend(r))}${toHex(blend(g))}${toHex(blend(b))}`;
}

/** 留言板推荐预设颜色 */
export const PRESET_COLORS = [
  "#fef9c3", // 黄
  "#fce7f3", // 粉
  "#dbeafe", // 蓝
  "#dcfce7", // 绿
  "#fef3c7", // 琥珀
  "#e0e7ff", // 靛蓝
  "#f3e8ff", // 紫
  "#ffe4e6", // 玫瑰
  "#fed7aa", // 橙
  "#ffffff", // 白
];

// ===== 日期格式化 =====

/** 留言板留言时间格式化：M/D HH:mm */
export function formatBoardDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ===== 项目分类选项 =====

export const CATEGORY_OPTIONS = [
  { label: "工作", value: "work" },
  { label: "生活", value: "life" },
  { label: "游戏", value: "game" },
];

// ===== 菜品照片路径转 URL =====

/** 菜品照片路径转 URL: /data/meals/xxx -> /meal-photos/xxx */
export function mealPhotoToUrl(path: string): string {
  return path.replace(/^\/data\/meals\//, "/meal-photos/");
}
