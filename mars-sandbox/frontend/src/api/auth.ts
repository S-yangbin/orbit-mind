import { api } from "./client";
import type { UserStatus } from "../types";

export const login = async (username: string, password: string) => {
  return api.post("/api/auth/login", { username, password });
};

export const logout = async () => {
  return api.post("/api/auth/logout");
};

export const getAuthStatus = async (): Promise<UserStatus> => {
  const { data } = await api.get<UserStatus>("/api/auth/me");
  return data;
};
