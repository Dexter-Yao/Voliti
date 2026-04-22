// ABOUTME: Mirror Store 契约解析器
// ABOUTME: PlanDocument / PlanView / CopingPlan / DashboardConfig / WitnessCard 的 TS 投影与辅助解析

export interface PlanProcessGoal {
  name: string;
  why_this_goal: string | null;
  weekly_target_days: number;
  weekly_total_days: number;
  how_to_measure: string;
  examples: string[];
}

export interface PlanRhythmItem {
  value: string;
  tooltip: string;
}

export interface PlanDailyRhythm {
  meals: PlanRhythmItem;
  training: PlanRhythmItem;
  sleep: PlanRhythmItem;
}

export interface PlanChapter {
  chapter_index: number;
  name: string;
  why_this_chapter: string;
  previous_chapter_id: string | null;
  revision_of: string | null;
  start_date: string;
  end_date: string;
  milestone: string;
  process_goals: PlanProcessGoal[];
  daily_rhythm: PlanDailyRhythm;
  daily_calorie_range: [number, number];
  daily_protein_grams_range: [number, number];
  weekly_training_count: number;
}

export interface PlanTarget {
  metric: string;
  baseline: number;
  goal_value: number;
  duration_weeks: number;
  rate_kg_per_week: number;
}

export interface PlanLinkedLifeSign {
  id: string;
  name: string;
  relevant_chapters: number[];
}

export interface PlanLinkedMarker {
  id: string;
  name: string;
  date: string;
  impacts_chapter: number;
  note: string | null;
}

export interface PlanCurrentWeek {
  updated_at: string;
  source: "coach_inferred" | "user_reported";
  goals_status: Array<{
    goal_name: string;
    days_met: number;
    days_expected: number;
  }>;
  highlights: string | null;
  concerns: string | null;
}

export interface PlanDocumentData {
  plan_id: string;
  status: "active" | "completed" | "paused" | "archived";
  version: number;
  predecessor_version: number | null;
  supersedes_plan_id: string | null;
  change_summary: string | null;
  target_summary: string;
  overall_narrative: string;
  started_at: string;
  planned_end_at: string;
  created_at: string;
  revised_at: string;
  target: PlanTarget;
  chapters: PlanChapter[];
  linked_lifesigns: PlanLinkedLifeSign[];
  linked_markers: PlanLinkedMarker[];
  current_week: PlanCurrentWeek | null;
}

export interface PlanViewEvent {
  id: string;
  name: string;
  event_date: string;
  urgency: number;
  description: string | null;
  is_past: boolean;
  risk_level: string | null;
}

export interface PlanViewMapState {
  flag_ratio: number;
  events: PlanViewEvent[];
}

export interface PlanViewWeekFreshness {
  days_since_update: number;
  level: "fresh" | "stale" | "very_stale";
}

export interface PlanViewDayTemplateItem {
  label: string;
  value: string;
  tooltip: string;
}

export interface PlanViewWatchItem {
  kind: "lifesign" | "marker";
  id: string;
  name: string;
  event_date: string | null;
  risk_level: string | null;
  note: string | null;
  relevant_chapters: number[] | null;
  trigger: string | null;
  coping_response: string | null;
}

export interface PlanViewData {
  plan_phase: "before_start" | "in_chapter" | "after_end";
  active_chapter_index: number | null;
  week_index: number;
  day_progress: [number, number];
  active_chapter_day_progress: [number, number];
  days_left_in_chapter: number;
  map_state: PlanViewMapState;
  week_view: Array<{
    goal_name: string;
    days_met: number;
    days_expected: number;
  }>;
  week_freshness: PlanViewWeekFreshness | null;
  day_template: PlanViewDayTemplateItem[];
  watch_list: PlanViewWatchItem[];
}

export interface DashboardConfigData {
  north_star: {
    key: string;
    label: string;
    type: string;
    unit?: string;
    delta_direction?: string;
    scale_max?: number;
    ratio_denominator?: number;
  };
  support_metrics: Array<{
    key: string;
    label: string;
    type: string;
    unit?: string;
    order?: number;
    scale_max?: number;
    ratio_denominator?: number;
  }>;
  user_goal?: string | null;
}

export interface CopingPlan {
  id?: string;
  trigger: string;
  coping_response: string;
  status?: string;
}

export interface WitnessCard {
  id: string;
  src: string;
  alt: string;
  createdAt: string;
  narrative: string;
  achievementType: string;
}

export function unwrapFileValue(value: Record<string, unknown> | null | undefined): string {
  const content = value?.content;
  if (Array.isArray(content) && content.every((line) => typeof line === "string")) {
    return content.join("\n");
  }
  return "";
}

export function parseJsonFileValue<T>(
  value: Record<string, unknown> | null | undefined,
): T | null {
  try {
    return JSON.parse(unwrapFileValue(value)) as T;
  } catch {
    return null;
  }
}

export function parseCopingPlans(markdown: string): CopingPlan[] {
  const plans: CopingPlan[] = [];
  const lines = markdown.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("-") && !trimmed.startsWith("*")) continue;
    const text = trimmed.replace(/^[-*]\s*/, "");
    const arrowIdx = text.indexOf("→");
    if (arrowIdx >= 0) {
      plans.push({
        trigger: text.slice(0, arrowIdx).trim(),
        coping_response: text.slice(arrowIdx + 1).trim(),
      });
    } else {
      plans.push({ trigger: text, coping_response: "" });
    }
  }

  return plans;
}

export function parseIdentityStatement(markdown: string): string | null {
  for (const line of markdown.split("\n")) {
    const match = line.match(/^(?:-\s*)?identity_statement:\s*(.+)$/);
    if (match) return match[1].trim();
  }
  return null;
}

interface StoreWitnessCardItem {
  key: string;
  value: Record<string, unknown> | null;
  createdAt?: string;
  updatedAt?: string;
}

function readStringValue(
  value: Record<string, unknown> | null,
  key: string,
): string {
  const raw = value?.[key];
  return typeof raw === "string" ? raw : "";
}

function resolveWitnessCardCreatedAt(item: StoreWitnessCardItem): string {
  const value = item.value;
  const timestamp = readStringValue(value, "timestamp");
  if (timestamp) return timestamp;
  if (typeof item.updatedAt === "string" && item.updatedAt) return item.updatedAt;
  if (typeof item.createdAt === "string" && item.createdAt) return item.createdAt;
  return "";
}

export function buildAcceptedWitnessCardsFromStoreItems(
  items: StoreWitnessCardItem[],
): WitnessCard[] {
  return items
    .filter((item) => readStringValue(item.value, "status") === "accepted")
    .map((item) => {
      const value = item.value;
      const src = readStringValue(value, "imageData");
      const alt = readStringValue(value, "achievement_title") || "见证卡";
      const narrative = readStringValue(value, "narrative");
      const achievementType =
        readStringValue(value, "achievement_type") || "explicit";
      const createdAt = resolveWitnessCardCreatedAt(item);

      if (!src || !createdAt) return null;

      return {
        id: item.key,
        src,
        alt,
        createdAt,
        narrative,
        achievementType,
      };
    })
    .filter((card): card is WitnessCard => card !== null)
    .sort(
      (a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt),
    );
}
