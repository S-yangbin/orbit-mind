import { api } from "./client";
import type {
  ActivityType,
  ActivityTypeCreate,
  ActivityTypeUpdate,
  WeeklyTemplate,
  WeeklyTemplateCreate,
  DailyScheduleItem,
  DailyScheduleCreate,
  DailyScheduleUpdate,
} from "../types";

// --- Activity Types ---
export const fetchActivityTypes = async (): Promise<ActivityType[]> => {
  const { data } = await api.get<ActivityType[]>("/api/schedule/activity-types");
  return data;
};

export const createActivityType = async (payload: ActivityTypeCreate): Promise<ActivityType> => {
  const { data } = await api.post<ActivityType>("/api/schedule/activity-types", payload);
  return data;
};

export const updateActivityType = async (
  id: number,
  payload: ActivityTypeUpdate
): Promise<ActivityType> => {
  const { data } = await api.put<ActivityType>(`/api/schedule/activity-types/${id}`, payload);
  return data;
};

export const deleteActivityType = async (id: number): Promise<void> => {
  await api.delete(`/api/schedule/activity-types/${id}`);
};

// --- Weekly Template ---
export const fetchActiveTemplate = async (): Promise<WeeklyTemplate | null> => {
  const { data } = await api.get<WeeklyTemplate | null>("/api/schedule/template");
  return data;
};

export const createOrUpdateTemplate = async (
  payload: WeeklyTemplateCreate
): Promise<WeeklyTemplate> => {
  const { data } = await api.post<WeeklyTemplate>("/api/schedule/template", payload);
  return data;
};

// --- Daily Schedule ---
export const fetchDailySchedule = async (
  date?: string
): Promise<DailyScheduleItem[]> => {
  const { data } = await api.get<DailyScheduleItem[]>("/api/schedule/daily", {
    params: date ? { target_date: date } : {},
  });
  return data;
};

export const fetchDailyRange = async (
  start: string,
  end: string
): Promise<DailyScheduleItem[]> => {
  const { data } = await api.get<DailyScheduleItem[]>("/api/schedule/daily/range", {
    params: { start, end },
  });
  return data;
};

export const addDailyItem = async (payload: DailyScheduleCreate): Promise<DailyScheduleItem> => {
  const { data } = await api.post<DailyScheduleItem>("/api/schedule/daily", payload);
  return data;
};

export const updateDailyItem = async (
  id: number,
  payload: DailyScheduleUpdate
): Promise<DailyScheduleItem> => {
  const { data } = await api.put<DailyScheduleItem>(`/api/schedule/daily/${id}`, payload);
  return data;
};

export const deleteDailyItem = async (id: number): Promise<void> => {
  await api.delete(`/api/schedule/daily/${id}`);
};
