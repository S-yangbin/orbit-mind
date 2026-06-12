import { api } from "./client";
import type { StarReward, StarRewardCreate, StarSummary } from "../types";

export const fetchStarSummary = async (): Promise<StarSummary> => {
  const { data } = await api.get<StarSummary>("/api/stars/summary");
  return data;
};

export const fetchStars = async (params?: {
  date?: string;
  page?: number;
  page_size?: number;
}): Promise<StarReward[]> => {
  const { data } = await api.get<StarReward[]>("/api/stars", { params });
  return data;
};

export const createStar = async (payload: StarRewardCreate): Promise<StarReward> => {
  const { data } = await api.post<StarReward>("/api/stars", payload);
  return data;
};

export const redeemStar = async (id: number): Promise<StarReward> => {
  const { data } = await api.post<StarReward>(`/api/stars/${id}/redeem`);
  return data;
};

export const deleteStar = async (id: number): Promise<void> => {
  await api.delete(`/api/stars/${id}`);
};
