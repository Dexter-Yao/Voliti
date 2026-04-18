// ABOUTME: Mirror Store 契约解析器
// ABOUTME: 把各 Store item 的文件封装值还原为前端投影视图所需的数据对象

export interface ChapterData {
  id?: string;
  chapter_number: number;
  goal_id: string;
  title: string;
  milestone: string;
  start_date: string;
  planned_end_date: string;
  status?: string;
  process_goals: Array<{
    key: string;
    description: string;
    target: string;
    metric_key: string;
  }>;
}

export interface GoalData {
  id: string;
  description: string;
  north_star_target: {
    key: string;
    baseline: number;
    target: number;
    unit: string;
  };
  start_date: string;
  target_date: string;
  status: string;
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

export interface MirrorData {
  chapter: ChapterData | null;
  copingPlans: CopingPlan[];
  dashboardConfig: DashboardConfigData | null;
  identity_statement: string | null;
  goal: GoalData | null;
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

interface BuildMirrorDataInput {
  chapterValue?: Record<string, unknown> | null;
  copingPlansValue?: Record<string, unknown> | null;
  dashboardConfigValue?: Record<string, unknown> | null;
  goalValue?: Record<string, unknown> | null;
  profileValue?: Record<string, unknown> | null;
}

export function buildMirrorDataFromStoreValues(input: BuildMirrorDataInput): MirrorData {
  const chapter = parseJsonFileValue<ChapterData>(input.chapterValue);
  const dashboardConfig = parseJsonFileValue<DashboardConfigData>(input.dashboardConfigValue);
  const goal = parseJsonFileValue<GoalData>(input.goalValue);
  const profileMarkdown = unwrapFileValue(input.profileValue);
  const copingMarkdown = unwrapFileValue(input.copingPlansValue);

  return {
    chapter,
    copingPlans: copingMarkdown ? parseCopingPlans(copingMarkdown) : [],
    dashboardConfig,
    identity_statement: profileMarkdown ? parseIdentityStatement(profileMarkdown) : null,
    goal,
  };
}
