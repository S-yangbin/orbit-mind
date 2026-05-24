import { api } from "./client";
import type { ScanStatus } from "../types";

export const triggerScan = async (): Promise<{ status: string; message: string }> => {
  const { data } = await api.post("/api/scan");
  return data;
};

export const getScanStatus = async (): Promise<ScanStatus> => {
  const { data } = await api.get<ScanStatus>("/api/scan/status");
  return data;
};
