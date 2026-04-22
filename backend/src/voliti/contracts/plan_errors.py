# ABOUTME: Plan 契约校验错误消息 formatter
# ABOUTME: Pydantic ValidationError → Coach 可操作中文消息（定位 + 解释 + 修复建议）

from __future__ import annotations

from typing import Callable

from pydantic import ValidationError


def format_plan_write_error(exc: ValidationError) -> str:
    """将 Plan 契约的 ValidationError 渲染为 Coach 可读的中文消息。

    6 条 @model_validator 约束抛出的 ValueError 使用 pipe-delimited payload，
    在此处映射为 domain-specific 定位 / 解释 / 修复建议；其余字段级错误走通用 fallback。
    """
    lines = ["Plan 校验未通过，未写入。"]
    for err in exc.errors():
        domain_msg = _try_domain_format(err)
        lines.append(domain_msg if domain_msg is not None else _fallback_format(err))
    return "\n".join(lines)


def _try_domain_format(err: dict) -> str | None:
    if err.get("type") != "value_error":
        return None
    raw = str(err.get("msg", "")).strip()
    # Pydantic v2 prefixes raised ValueError with "Value error, "
    payload = raw.removeprefix("Value error, ").strip()
    parts = payload.split("|")
    if not parts:
        return None
    key = parts[0]
    kv: dict[str, str] = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k] = v
    formatter = _DOMAIN_FORMATTERS.get(key)
    return formatter(kv) if formatter else None


def _fallback_format(err: dict) -> str:
    field_path = " → ".join(str(loc) for loc in err.get("loc", [])) or "(根级别)"
    msg = err.get("msg", "")
    current_val = err.get("input", "<未提供>")
    return f"  • 字段 `{field_path}`：{msg}（当前值：{current_val!r}）"


# ── domain formatters（对应 plan.py 的 6 条 @model_validator 约束）──────


def _fmt_timeline_discontinuous(kv: dict[str, str]) -> str:
    i = kv.get("i", "?")
    prev_end = kv.get("prev_end", "?")
    next_start = kv.get("next_start", "?")
    expected_next_start = kv.get("expected_next_start", "?")
    try:
        ch_prev = str(int(i) + 1)
        ch_next = str(int(i) + 2)
    except ValueError:
        ch_prev = "?"
        ch_next = "?"
    return (
        f"  字段：chapters[{i}].end_date\n"
        f"  问题：Chapter {ch_prev} 结束日期（{prev_end}）与 Chapter {ch_next} 开始日期（{next_start}）不连续。\n"
        f"        下一章必须从上一章结束后的次日开始（期望开始日：{expected_next_start}）。\n"
        f"  修复：将 Chapter {ch_next} 的 start_date 改为 {expected_next_start}，或同步调整 Chapter {ch_prev} 的 end_date。"
    )


def _fmt_chapter_index_not_monotonic(kv: dict[str, str]) -> str:
    actual = kv.get("actual", "?")
    expected = kv.get("expected", "?")
    return (
        f"  字段：chapters[*].chapter_index\n"
        f"  问题：chapter_index 序列 {actual} 不连续。\n"
        f"        应从 1 开始每章 +1：{expected}。\n"
        f"  修复：按顺序重新编号每个 chapter 的 chapter_index。"
    )


def _fmt_plan_end_before_last_chapter(kv: dict[str, str]) -> str:
    plan_end = kv.get("plan_end", "?")
    last_end = kv.get("last_chapter_end", "?")
    return (
        f"  字段：planned_end_at\n"
        f"  问题：Plan 计划结束日期（{plan_end}）早于最后一章结束日期（{last_end}）。\n"
        f"        Plan 时长应覆盖所有 chapter。\n"
        f"  修复：将 planned_end_at 改为不早于 {last_end}，或缩短最后一章的 end_date。"
    )


def _fmt_goal_name_unknown(kv: dict[str, str]) -> str:
    requested = kv.get("requested", "?")
    available = kv.get("available", "[]")
    return (
        f"  字段：current_week.goals_status[*].goal_name\n"
        f"  问题：goal_name '{requested}' 不在任何 chapter 的 process_goals 中。\n"
        f"        可用 goal_name：{available}。\n"
        f"  修复：使用上述可用名之一；若确实需要新 process_goal，请先通过 revise_plan 更新 chapter。"
    )


def _fmt_linked_lifesign_chapter_out_of_range(kv: dict[str, str]) -> str:
    index = kv.get("index", "?")
    invalid = kv.get("invalid", "?")
    max_idx = kv.get("max_idx", "?")
    return (
        f"  字段：linked_lifesigns[{index}].relevant_chapters\n"
        f"  问题：包含无效 chapter_index {invalid}，有效范围：1-{max_idx}。\n"
        f"  修复：仅引用已存在的 chapter_index。"
    )


def _fmt_linked_marker_chapter_out_of_range(kv: dict[str, str]) -> str:
    index = kv.get("index", "?")
    invalid = kv.get("invalid", "?")
    max_idx = kv.get("max_idx", "?")
    return (
        f"  字段：linked_markers[{index}].impacts_chapter\n"
        f"  问题：impacts_chapter = {invalid} 不在有效范围 1-{max_idx} 内。\n"
        f"  修复：指向一个存在的 chapter_index。"
    )


_DOMAIN_FORMATTERS: dict[str, Callable[[dict[str, str]], str]] = {
    "chapters_timeline_discontinuous": _fmt_timeline_discontinuous,
    "chapters_index_not_monotonic": _fmt_chapter_index_not_monotonic,
    "plan_end_before_last_chapter": _fmt_plan_end_before_last_chapter,
    "goal_name_unknown": _fmt_goal_name_unknown,
    "linked_lifesign_chapter_out_of_range": _fmt_linked_lifesign_chapter_out_of_range,
    "linked_marker_chapter_out_of_range": _fmt_linked_marker_chapter_out_of_range,
}
