import { api } from "./client";
import type {
  VideoInfo,
  VideoListResponse,
  VideoUploadResponse,
  VideoSegmentInfo,
  SegmentNoteInfo,
  SegmentProgressInfo,
  SegmentCreateData,
  SegmentUpdateData,
  SegmentProgressUpdateData,
} from "../types";

export const fetchVideos = async (params: {
  q?: string;
  status?: string;
  page?: number;
  page_size?: number;
  sort?: string;
  order?: string;
}): Promise<VideoListResponse> => {
  const { data } = await api.get<VideoListResponse>("/api/videos", { params });
  return data;
};

export const fetchVideo = async (id: number): Promise<VideoInfo> => {
  const { data } = await api.get<VideoInfo>(`/api/videos/${id}`);
  return data;
};

export const uploadVideo = async (
  file: File,
  title: string,
  onProgress?: (pct: number) => void
): Promise<VideoUploadResponse> => {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  const { data } = await api.post<VideoUploadResponse>("/api/videos/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
};

export const processVideo = async (id: number): Promise<{ message: string }> => {
  const { data } = await api.post<{ message: string }>(`/api/videos/${id}/process`);
  return data;
};

export const getStreamUrl = (id: number): string => `/api/videos/${id}/stream`;

export const createSegment = async (
  videoId: number,
  seg: SegmentCreateData
): Promise<VideoSegmentInfo> => {
  const { data } = await api.post<VideoSegmentInfo>(`/api/videos/${videoId}/segments`, seg);
  return data;
};

export const updateSegment = async (
  segmentId: number,
  seg: SegmentUpdateData
): Promise<VideoSegmentInfo> => {
  const { data } = await api.put<VideoSegmentInfo>(`/api/videos/segments/${segmentId}`, seg);
  return data;
};

export const deleteSegment = async (segmentId: number): Promise<void> => {
  await api.delete(`/api/videos/segments/${segmentId}`);
};

export const upsertNote = async (
  segmentId: number,
  content: string
): Promise<SegmentNoteInfo> => {
  const { data } = await api.post<SegmentNoteInfo>(
    `/api/videos/segments/${segmentId}/notes`,
    { content }
  );
  return data;
};

export const updateProgress = async (
  segmentId: number,
  progress: SegmentProgressUpdateData
): Promise<SegmentProgressInfo> => {
  const { data } = await api.put<SegmentProgressInfo>(
    `/api/videos/segments/${segmentId}/progress`,
    progress
  );
  return data;
};