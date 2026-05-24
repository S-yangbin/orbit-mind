import { api } from "./client";
import type { Tag } from "../types";

export const fetchTags = async (): Promise<Tag[]> => {
  const { data } = await api.get<Tag[]>("/api/tags");
  return data;
};

export const createTag = async (name: string): Promise<Tag> => {
  const { data } = await api.post<Tag>("/api/tags", { name });
  return data;
};

export const updateTag = async (id: number, name: string): Promise<Tag> => {
  const { data } = await api.put<Tag>(`/api/tags/${id}`, { name });
  return data;
};

export const deleteTag = async (id: number): Promise<void> => {
  await api.delete(`/api/tags/${id}`);
};
