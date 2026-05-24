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
