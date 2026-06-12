export interface Tag {
  id: number;
  name: string;
  page_count?: number;
}

export interface Page {
  id: number;
  slug: string;
  title: string;
  description: string;
  thumbnail: string | null;
  entry_file: string;
  is_customized: number;
  category: string;
  created_at: string;
  updated_at: string;
  synced_at: string;
  tags: Tag[];
}

export interface PageListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Page[];
}

export interface ScanStatus {
  is_running: boolean;
  last_scan_at: string | null;
  last_result: string | null;
}

export interface UserStatus {
  authenticated: boolean;
}

export interface NodeInfo {
  node_id: string;
  hostname: string;
  ip: string;
  platform: string;
  version: string;
  status: "online" | "offline";
  last_heartbeat_at: string | null;
  uptime_seconds: number;
  uptime: string;
}

export interface NodeListResponse {
  total: number;
  online: number;
  offline: number;
  nodes: NodeInfo[];
}

export interface NodeCommandRequest {
  command: string;
  timeout?: number;
}

export interface NodeCommandResponse {
  request_id: string;
  node_id: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
}

// --- Videos ---
export interface VideoInfo {
  id: number;
  title: string;
  filename: string;
  file_path: string;
  file_size: number;
  duration: number | null;
  status: "pending" | "processing" | "ready" | "error";
  transcription_json: string | null;
  oss_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  segments: VideoSegmentInfo[];
  segment_count?: number;
  mastered_count?: number;
}

export interface VideoSegmentInfo {
  id: number;
  video_id: number;
  title: string;
  segment_type: "intro" | "qa" | "explanation" | "outro" | "other";
  start_time: number;
  end_time: number;
  transcription: string | null;
  sort_order: number;
  notes: SegmentNoteInfo[];
  progress: SegmentProgressInfo | null;
}

export interface SegmentNoteInfo {
  id: number;
  segment_id: number;
  content: string;
  note_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface SegmentProgressInfo {
  id: number;
  segment_id: number;
  mastered: number;
  loop_count: number;
  last_practiced_at: string | null;
}

export interface VideoUploadResponse {
  id: number;
  title: string;
  filename: string;
  file_size: number;
  status: string;
  message: string;
}

export interface VideoListResponse {
  total: number;
  page: number;
  page_size: number;
  items: VideoInfo[];
}

export interface SegmentCreateData {
  title: string;
  segment_type?: string;
  start_time: number;
  end_time: number;
  transcription?: string;
  sort_order?: number;
}

export interface SegmentUpdateData {
  title?: string;
  segment_type?: string;
  start_time?: number;
  end_time?: number;
  transcription?: string;
  sort_order?: number;
}

export interface SegmentProgressUpdateData {
  mastered?: number;
  loop_count?: number;
  last_practiced_at?: string;
}

// --- Meals ---
export interface FamilyMember {
  id: number;
  name: string;
  role: string;
  avatar: string;
  preferences: { likes: string[]; dislikes: string[]; note: string } | null;
  allergies: string[] | null;
  board_color: string | null;
  liked_dishes: { dish_id: number; dish_name: string; like_count: number; last_liked_at: string | null }[] | null;
  created_at: string;
  updated_at: string;
}

export interface FamilyMemberCreate {
  name: string;
  avatar?: string;
  board_color?: string;
}

export interface FamilyMemberUpdate {
  name?: string;
  avatar?: string;
  preferences?: { likes: string[]; dislikes: string[]; note: string };
  allergies?: string[];
  board_color?: string;
}

export interface Dish {
  id: number;
  name: string;
  category: string;
  ingredients: string[];
  recipe: string | null;
  tags: string[];
  origin: string;
  photo_count: number;
  created_at: string;
}

export interface DishListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Dish[];
}

export interface DishCreateData {
  name: string;
  category?: string;
  ingredients?: string[];
  recipe?: string;
  tags?: string[];
}

export interface MealPlanItemDish {
  id: number;
  name: string;
  category: string;
  ingredients: string[];
  recipe?: string;
}

export interface MealPlanItem {
  id: number;
  date: string;
  meal_type: "breakfast" | "lunch" | "dinner";
  dish: MealPlanItemDish;
  sort_order: number;
  is_manual: number;
  source?: "log" | "plan" | null;
}

export interface MealPlan {
  id: number;
  week_start_date: string;
  status: "draft" | "confirmed" | "log";
  items: MealPlanItem[];
  created_at: string;
  updated_at: string;
}

export interface RecognizedDish {
  name: string;
  matched: boolean;
  dish_id: number | null;
  category: string | null;
}

export interface PhotoRecognizeResult {
  image_path: string;
  recognized_dishes: RecognizedDish[];
  date: string;
  meal_type: string;
}

export interface MealLogDish {
  dish_id: number | null;
  name: string;
}

export interface MealLog {
  id: number;
  date: string;
  meal_type: "breakfast" | "lunch" | "dinner";
  image_path: string;
  dishes: MealLogDish[];
  rating: number | null;
  note: string | null;
  rated_by: string | null;
  liked_by: Record<string, number[]>;
  created_at: string;
}

export interface MealLogListResponse {
  total: number;
  page: number;
  page_size: number;
  items: MealLog[];
}

export interface MealHistoryStats {
  period: { start: string; end: string };
  total_meals: number;
  unique_dishes: number;
  repeat_rate: number;
  top_repeated: { dish_id: number | null; name: string; count: number; category: string }[];
  daily_counts: { date: string; dish_count: number; unique_count: number }[];
}

// --- Board Messages ---
export interface BoardMessage {
  id: number;
  content: string;
  author: string;
  color: string;
  pinned: number;
  expires_at: string | null;
  acknowledged_by: number[];
  created_at: string;
}

export interface BoardMessageListResponse {
  items: BoardMessage[];
}

export interface BoardMessageCreate {
  content: string;
  author?: string;
  color?: string;
  expires_at?: string | null;
}

export interface BoardMessageUpdate {
  content?: string;
  author?: string;
  color?: string;
  expires_at?: string | null;
}

// --- Dashboard ---
export interface DashboardMealPlanItem {
  id: number;
  date: string;
  meal_type: "breakfast" | "lunch" | "dinner";
  dish: {
    id: number;
    name: string;
    category: string;
    photo: string | null;
  };
  sort_order: number;
  is_manual: number;
}

export interface DashboardMealPlan {
  id: number;
  week_start_date: string;
  status: string;
  items: DashboardMealPlanItem[];
}

export interface DashboardRecentMeal {
  id: number;
  date: string;
  meal_type: string;
  image_path: string;
  dishes: { dish_id?: number; name: string }[];
}

export interface DashboardTravelPage {
  id: number;
  slug: string;
  title: string;
  description: string;
  thumbnail: string | null;
  entry_file: string;
  updated_at: string | null;
}

export interface DashboardFamilyMember {
  id: number;
  name: string;
  avatar: string;
  board_color: string | null;
}

export interface WeatherInfo {
  temp: number;
  feels_like?: number;
  description: string;
  icon: string;
  city: string;
}

export interface WeatherForecastItem {
  date: string;
  icon: string;
  temp_max: number;
  temp_min: number;
  description: string;
}

export interface DashboardData {
  meal_plans: DashboardMealPlan[];
  recent_meals: DashboardRecentMeal[];
  travel_pages: DashboardTravelPage[];
  messages: BoardMessage[];
  family_members: DashboardFamilyMember[];
  weather: WeatherInfo | null;
  weather_forecast: WeatherForecastItem[] | null;
  background_image: string | null;
  today_schedule: TodayScheduleItem[];
}

export interface DashboardWsMessage {
  type: string;
  timestamp?: string;
  data?: DashboardData;
  message?: BoardMessage | { id: number };
  message_id?: number;
  member_id?: number;
  acknowledged_by?: number[];
}

// --- Learning Plan (Children's Daily Schedule) ---

export interface ActivityType {
  id: number;
  name: string;
  icon: string;
  category: string;
  color: string;
  is_preset: number;
  sort_order: number;
  child_id: number | null;
  created_at: string;
}

export interface ActivityTypeCreate {
  name: string;
  icon?: string;
  category?: string;
  color?: string;
}

export interface ActivityTypeUpdate {
  name?: string;
  icon?: string;
  category?: string;
  color?: string;
  sort_order?: number;
}

export interface WeeklyTemplateDayItem {
  day_of_week: number;  // 0=Monday ... 6=Sunday
  activity_type_id: number;
  sort_order: number;
}

export interface WeeklyTemplate {
  id: number;
  name: string;
  child_id: number | null;
  is_active: number;
  days: WeeklyTemplateDayItem[];
  created_at: string;
  updated_at: string;
}

export interface WeeklyTemplateCreate {
  name?: string;
  days: WeeklyTemplateDayItem[];
}

export interface ScheduleActivityTypeInfo {
  id: number;
  name: string;
  icon: string;
  color: string;
}

export interface DailyScheduleItem {
  id: number;
  date: string;
  activity_type_id: number;
  activity_type: ScheduleActivityTypeInfo | null;
  completed: number;
  completed_at: string | null;
  completion_note: string | null;
  sort_order: number;
  is_override: number;
  created_at: string;
}

export interface DailyScheduleCreate {
  date: string;
  activity_type_id: number;
  sort_order?: number;
}

export interface DailyScheduleUpdate {
  completed?: number;
  completion_note?: string;
}

export interface TodayScheduleItem {
  id: number;
  date: string;
  activity_type: ScheduleActivityTypeInfo | null;
  completed: number;
  completed_at: string | null;
  completion_note: string | null;
  sort_order: number;
  is_override: number;
}

