import { api } from "./client";
import type { NodeListResponse, NodeCommandRequest, NodeCommandResponse } from "../types";

export const fetchNodes = async (stale = 180): Promise<NodeListResponse> => {
  const { data } = await api.get<NodeListResponse>("/api/nodes", {
    params: { stale },
  });
  return data;
};

export const deleteNode = async (nodeId: string): Promise<void> => {
  await api.delete(`/api/nodes/${nodeId}`);
};

export const executeNodeCommand = async (
  nodeId: string,
  payload: NodeCommandRequest
): Promise<NodeCommandResponse> => {
  const { data } = await api.post<NodeCommandResponse>(
    `/api/nodes/${nodeId}/command`,
    payload
  );
  return data;
};
