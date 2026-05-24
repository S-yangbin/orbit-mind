export interface Tag {
  id: number;
  name: string;
  page_count?: number;
}

export interface Page {
  id: number;
  slug: string;
  title: string;
  description: string;
  thumbnail: string | null;
  entry_file: string;
  is_customized: number;
  category: string;
  created_at: string;
  updated_at: string;
  synced_at: string;
  tags: Tag[];
}

export interface PageListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Page[];
}

export interface ScanStatus {
  is_running: boolean;
  last_scan_at: string | null;
  last_result: string | null;
}

export interface UserStatus {
  authenticated: boolean;
}

export interface NodeInfo {
  node_id: string;
  hostname: string;
  ip: string;
  platform: string;
  version: string;
  status: "online" | "offline";
  last_heartbeat_at: string | null;
  uptime_seconds: number;
  uptime: string;
}

export interface NodeListResponse {
  total: number;
  online: number;
  offline: number;
  nodes: NodeInfo[];
}
