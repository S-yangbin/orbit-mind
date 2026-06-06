import { api } from "./client";
import type { BoardMessage, BoardMessageListResponse, BoardMessageCreate, BoardMessageUpdate } from "../types";

export const fetchMessages = async (): Promise<BoardMessage[]> => {
  const { data } = await api.get<BoardMessageListResponse>("/api/board/messages");
  return data.items;
};

export const createMessage = async (payload: BoardMessageCreate): Promise<BoardMessage> => {
  const { data } = await api.post<BoardMessage>("/api/board/messages", payload);
  return data;
};

export const updateMessage = async (id: number, payload: BoardMessageUpdate): Promise<BoardMessage> => {
  const { data } = await api.put<BoardMessage>(`/api/board/messages/${id}`, payload);
  return data;
};

export const deleteMessage = async (id: number): Promise<void> => {
  await api.delete(`/api/board/messages/${id}`);
};

export const togglePin = async (id: number): Promise<BoardMessage> => {
  const { data } = await api.put<BoardMessage>(`/api/board/messages/${id}/pin`);
  return data;
};
