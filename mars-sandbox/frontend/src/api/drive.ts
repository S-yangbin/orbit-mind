import { api } from "./client";

export interface DriveFileData {
  id: number;
  filename: string;
  oss_key: string;
  file_size: number;
  content_type: string;
  uploaded_by: string;
  is_dir: number;
  parent_id: number | null;
  created_at: string;
}

export interface Breadcrumb {
  id: number;
  filename: string;
}

export interface DriveFileListData {
  total: number;
  page: number;
  page_size: number;
  items: DriveFileData[];
  breadcrumbs: Breadcrumb[];
}

export const fetchDriveFiles = async (params: {
  parent_id?: number | null;
  q?: string;
  page?: number;
  page_size?: number;
  sort?: string;
  order?: string;
}): Promise<DriveFileListData> => {
  const { data } = await api.get<DriveFileListData>("/api/drive/files", { params });
  return data;
};

export const recordDriveFile = async (payload: {
  filename: string;
  oss_key: string;
  file_size: number;
  content_type: string;
  parent_id?: number | null;
}): Promise<DriveFileData> => {
  const { data } = await api.post<DriveFileData>("/api/drive/files", payload);
  return data;
};

export const deleteDriveFile = async (id: number): Promise<void> => {
  await api.delete(`/api/drive/files/${id}`);
};

export const getSignedDownloadUrl = async (ossKey: string): Promise<string> => {
  const { data } = await api.get<{ url: string }>("/api/drive/signed-url", {
    params: { oss_key: ossKey },
  });
  return data.url;
};

export interface TextPreviewData {
  content: string;
  page: number;
  page_size: number;
  total_lines: number;
  total_pages: number;
  truncated: boolean;
}

export const fetchTextPreview = async (
  ossKey: string,
  page: number = 1,
  pageSize: number = 200,
): Promise<TextPreviewData> => {
  const { data } = await api.get<TextPreviewData>("/api/drive/preview-text", {
    params: { oss_key: ossKey, page, page_size: pageSize },
  });
  return data;
};

// Folder operations
export interface FolderInfo {
  id: number;
  filename: string;
  parent_id: number | null;
  oss_key: string;
}

export const createFolder = async (payload: {
  filename: string;
  parent_id?: number | null;
}): Promise<DriveFileData> => {
  const { data } = await api.post<DriveFileData>("/api/drive/folders", payload);
  return data;
};

export const deleteFolder = async (folderId: number): Promise<void> => {
  await api.delete(`/api/drive/folders/${folderId}`);
};

export const moveFile = async (
  fileId: number,
  targetParentId: number | null,
): Promise<DriveFileData> => {
  const { data } = await api.post<DriveFileData>(`/api/drive/files/${fileId}/move`, {
    target_parent_id: targetParentId,
  });
  return data;
};

export const copyFile = async (
  fileId: number,
  targetParentId: number | null,
): Promise<DriveFileData> => {
  const { data } = await api.post<DriveFileData>(`/api/drive/files/${fileId}/copy`, {
    target_parent_id: targetParentId,
  });
  return data;
};

export const fetchAllFolders = async (): Promise<FolderInfo[]> => {
  const { data } = await api.get<{ items: FolderInfo[] }>("/api/drive/folders");
  return data.items;
};

export const getUploadUrl = async (ossKey: string, contentType: string = "application/octet-stream"): Promise<string> => {
  const { data } = await api.post<{ url: string }>("/api/drive/upload-url", null, {
    params: { oss_key: ossKey, content_type: contentType },
  });
  return data.url;
};
