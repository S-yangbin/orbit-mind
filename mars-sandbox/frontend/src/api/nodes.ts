import { api } from "./client";
import type { NodeListResponse } from "../types";

export const fetchNodes = async (stale = 180): Promise<NodeListResponse> => {
  const { data } = await api.get<NodeListResponse>("/api/nodes", {
    params: { stale },
  });
  return data;
};

export const deleteNode = async (nodeId: string): Promise<void> => {
  await api.delete(`/api/nodes/${nodeId}`);
};
