import { api } from "./client";
import type { PageListResponse, Page } from "../types";

export const fetchPages = async (params: {
  q?: string;
  tag?: string;
  sort?: string;
  order?: string;
  page?: number;
  page_size?: number;
}): Promise<PageListResponse> => {
  const { data } = await api.get<PageListResponse>("/api/pages", { params });
  return data;
};

export const fetchPage = async (id: number): Promise<Page> => {
  const { data } = await api.get<Page>(`/api/pages/${id}`);
  return data;
};

export const updatePage = async (
  id: number,
  body: { title?: string; description?: string; tags?: string[] }
): Promise<Page> => {
  const { data } = await api.put<Page>(`/api/pages/${id}`, body);
  return data;
};

export const deletePage = async (id: number): Promise<void> => {
  await api.delete(`/api/pages/${id}`);
};
