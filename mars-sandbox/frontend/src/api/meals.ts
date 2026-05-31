import { api } from "./client";
import type {
  FamilyMember,
  FamilyMemberUpdate,
  Dish,
  DishListResponse,
  DishCreateData,
  MealPlan,
  MealLog,
  MealLogListResponse,
  MealLogDish,
  PhotoRecognizeResult,
  MealHistoryStats,
} from "../types";

// --- Family Members ---
export const fetchMembers = async (): Promise<FamilyMember[]> => {
  const { data } = await api.get<{ members: FamilyMember[] }>("/api/meals/members");
  return data.members;
};

export const updateMember = async (
  id: number,
  payload: FamilyMemberUpdate
): Promise<FamilyMember> => {
  const { data } = await api.put<FamilyMember>(`/api/meals/members/${id}`, payload);
  return data;
};

// --- Dishes ---
export const fetchDishes = async (
  page = 1,
  pageSize = 50,
  keyword?: string,
  category?: string
): Promise<DishListResponse> => {
  const { data } = await api.get<DishListResponse>("/api/meals/dishes", {
    params: { page, page_size: pageSize, keyword, category },
  });
  return data;
};

export const createDish = async (payload: DishCreateData): Promise<Dish> => {
  const { data } = await api.post<Dish>("/api/meals/dishes", payload);
  return data;
};

// --- Meal Plan ---
export const fetchCurrentPlans = async (): Promise<{ plans: MealPlan[]; datePhotos: Record<string, string> }> => {
  const { data } = await api.get<{ plans: MealPlan[]; date_photos?: Record<string, string> }>("/api/meals/plan/current");
  return { plans: data.plans || [], datePhotos: data.date_photos || {} };
};

export const generatePlan = async (weekStartDate?: string): Promise<MealPlan> => {
  const { data } = await api.post<MealPlan>("/api/meals/plan/generate", {
    week_start_date: weekStartDate,
  });
  return data;
};

export const replacePlanItem = async (
  itemId: number,
  dishId: number
): Promise<void> => {
  await api.put(`/api/meals/plan/items/${itemId}`, { dish_id: dishId });
};

export const removePlanItem = async (itemId: number): Promise<void> => {
  await api.delete(`/api/meals/plan/items/${itemId}`);
};

export const addPlanItem = async (
  dateStr: string,
  mealType: string,
  dishId: number
): Promise<void> => {
  await api.post("/api/meals/plan/items", {
    date: dateStr,
    meal_type: mealType,
    dish_id: dishId,
  });
};

export const confirmPlan = async (): Promise<void> => {
  await api.post("/api/meals/plan/confirm");
};

// --- Photo Recognition ---
export const recognizePhoto = async (
  file: File,
  dateStr?: string,
  mealType?: string
): Promise<PhotoRecognizeResult> => {
  const form = new FormData();
  form.append("image", file);
  if (dateStr) form.append("date", dateStr);
  if (mealType) form.append("meal_type", mealType);

  const { data } = await api.post<PhotoRecognizeResult>(
    "/api/meals/history/recognize",
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
};

// --- Meal History ---
export const createMealLog = async (
  imagePath: string,
  dateStr: string,
  mealType: string,
  dishes: MealLogDish[],
  rating?: number,
  note?: string,
  ratedBy?: string,
  likedBy?: Record<string, number[]>
): Promise<MealLog> => {
  const { data } = await api.post<MealLog>("/api/meals/history", {
    image_path: imagePath,
    date: dateStr,
    meal_type: mealType,
    dishes,
    rating,
    note,
    rated_by: ratedBy,
    liked_by: likedBy,
  });
  return data;
};

export const fetchMealLogs = async (
  page = 1,
  pageSize = 20,
  startDate?: string,
  endDate?: string
): Promise<MealLogListResponse> => {
  const { data } = await api.get<MealLogListResponse>("/api/meals/history", {
    params: { page, page_size: pageSize, start_date: startDate, end_date: endDate },
  });
  return data;
};

export const fetchHistoryStats = async (days = 14): Promise<MealHistoryStats> => {
  const { data } = await api.get<MealHistoryStats>("/api/meals/history/stats", {
    params: { days },
  });
  return data;
};
