# ABOUTME: HTML 评估报告生成器
# ABOUTME: 以契约失败与行为失败双视角渲染单模型与多模型报告

from __future__ import annotations

import html
import json
import logging
import re
from statistics import mean
from typing import Any
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from voliti_eval.auditor import AUDITOR_SYSTEM_PROMPT
from voliti_eval.dimensions import (
    DETERMINISTIC_DIMENSIONS,
    get_dimension_lane,
    is_diagnostic_dimension,
    is_runtime_gate_dimension,
    is_user_gate_dimension,
)
from voliti_eval.judge import BEHAVIOR_DIMENSIONS, SCORING_RUBRIC
from voliti_eval.models import DimensionScore, EvalResult, SeedResult

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_UNORDERED_LIST_RE = re.compile(r"^[-*]\s+(.*)$")
_ORDERED_LIST_RE = re.compile(r"^\d+\.\s+(.*)$")
_BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")


def _pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _display_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{round(value * 100)}%"


def _render_inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _render_markdown_html(text: str) -> Markup:
    if not text:
        return Markup("")

    lines = text.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    paragraph: list[str] = []
    unordered_list: list[str] = []
    ordered_list: list[str] = []
    quote_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append("<p>" + "<br>".join(_render_inline_markdown(line) for line in paragraph) + "</p>")
            paragraph.clear()

    def flush_unordered_list() -> None:
        if unordered_list:
            items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in unordered_list)
            blocks.append(f"<ul>{items}</ul>")
            unordered_list.clear()

    def flush_ordered_list() -> None:
        if ordered_list:
            items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in ordered_list)
            blocks.append(f"<ol>{items}</ol>")
            ordered_list.clear()

    def flush_quote() -> None:
        if quote_lines:
            items = "".join(f"<p>{_render_inline_markdown(item)}</p>" for item in quote_lines)
            blocks.append(f"<blockquote>{items}</blockquote>")
            quote_lines.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_unordered_list()
            flush_ordered_list()
            flush_quote()
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            flush_paragraph()
            flush_unordered_list()
            flush_ordered_list()
            flush_quote()
            level = len(heading_match.group(1))
            content = _render_inline_markdown(heading_match.group(2))
            blocks.append(f"<h{level}>{content}</h{level}>")
            continue

        quote_match = _BLOCKQUOTE_RE.match(stripped)
        if quote_match:
            flush_paragraph()
            flush_unordered_list()
            flush_ordered_list()
            quote_lines.append(quote_match.group(1))
            continue
        flush_quote()

        unordered_match = _UNORDERED_LIST_RE.match(stripped)
        if unordered_match:
            flush_paragraph()
            flush_ordered_list()
            unordered_list.append(unordered_match.group(1))
            continue
        flush_unordered_list()

        ordered_match = _ORDERED_LIST_RE.match(stripped)
        if ordered_match:
            flush_paragraph()
            flush_unordered_list()
            ordered_list.append(ordered_match.group(1))
            continue
        flush_ordered_list()

        paragraph.append(stripped)

    flush_paragraph()
    flush_unordered_list()
    flush_ordered_list()
    flush_quote()

    return Markup("".join(blocks))


def _dimension_category(dimension_id: str) -> str:
    return get_dimension_lane(dimension_id)


def _score_sort_key(item: tuple[str, DimensionScore]) -> tuple[int, str]:
    dimension_id, _ = item
    order = {"user_gate": 0, "runtime_gate": 1, "diagnostic": 2}
    return (order[_dimension_category(dimension_id)], dimension_id)


def _score_payload(dimension_id: str, score: DimensionScore) -> dict[str, Any]:
    return {
        "dimension_id": dimension_id,
        "passed": score.passed,
        "justification": score.justification,
        "evidence_turns": score.evidence_turns,
        "failure_severity": score.failure_severity,
        "score_source": score.score_source,
        "category": _dimension_category(dimension_id),
    }


def _pass_rate(scores: list[DimensionScore]) -> float | None:
    if not scores:
        return None
    return round(sum(1 for score in scores if score.passed) / len(scores), 2)


def _mean_defined(values: list[float | None]) -> float | None:
    defined = [value for value in values if value is not None]
    if not defined:
        return None
    return round(mean(defined), 2)


def _profile_context(config_snapshot: dict[str, Any], seed_count: int) -> dict[str, Any]:
    seed_ids = config_snapshot.get("profile_seed_ids", [])
    return {
        "name": config_snapshot.get("profile_name", "unknown"),
        "description": config_snapshot.get("profile_description", ""),
        "seed_count": config_snapshot.get("profile_seed_count", seed_count),
        "seed_ids": seed_ids if isinstance(seed_ids, list) else [],
    }


def _runtime_context(config_snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "server_url": config_snapshot.get("server_url", ""),
        "assistant_id": config_snapshot.get("assistant_id", ""),
        "auditor_model": config_snapshot.get("auditor_model", ""),
        "judge_model": config_snapshot.get("judge_model", ""),
        "max_concurrency": config_snapshot.get("max_concurrency"),
    }


def _run_output_paths(run: EvalResult, seed_id: str) -> tuple[str, str]:
    subdir = str(run.config_snapshot.get("report_output_subdir", "")).strip("/")
    prefix = f"{subdir}/" if subdir else ""
    return (
        f"{prefix}transcripts/{seed_id}.json",
        f"{prefix}scores/{seed_id}.json",
    )


def _manual_follow_up_notes(seed_result: SeedResult) -> list[str]:
    notes: list[str] = []
    if seed_result.seed.id == "17_future_self_dialogue_trigger":
        notes.append("Future Self 对话是否真正有帮助，当前刻意不做自动 gate，需人工复核。")
    if seed_result.seed.id == "19_metaphor_collaboration_trigger":
        notes.append("隐喻协作是否真正有帮助，当前刻意不做自动 gate，需人工复核。")
    return notes


def _build_run_snapshot(run: EvalResult, seed_result: SeedResult) -> dict[str, Any]:
    transcript_path, score_path = _run_output_paths(run, seed_result.seed.id)
    return {
        "run_id": run.run_id,
        "execution_status": seed_result.score_card.execution_status,
        "blocking_reason": seed_result.score_card.blocking_reason,
        "pass_rate": seed_result.score_card.pass_rate,
        "user_gate_met": seed_result.score_card.user_gate_met,
        "runtime_gate_met": seed_result.score_card.runtime_gate_met,
        "must_pass_met": seed_result.score_card.must_pass_met,
        "gate_pass_k": seed_result.score_card.must_pass_met,
        "end_reason": seed_result.transcript.end_reason,
        "transcript_path": transcript_path,
        "score_path": score_path,
    }


def _build_relevant_final_files(seed_result: SeedResult) -> list[dict[str, str]]:
    keys = (
        seed_result.seed.expected_artifacts.relevant_final_files
        or seed_result.seed.expected_artifacts.required_keys
        or sorted(seed_result.store_after.files)
    )
    files: list[dict[str, str]] = []
    for key in keys:
        artifact = seed_result.store_after.files.get(key)
        if artifact is None:
            continue
        files.append(
            {
                "key": key,
                "content": artifact.content,
                "is_markdown": key.endswith(".md") or key.endswith(".markdown"),
            }
        )
    return files


def _build_tool_call_rows(seed_result: SeedResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for call in seed_result.tool_calls:
        rows.append(
            {
                "turn_index": call.turn_index,
                "name": call.name,
                "arguments": _pretty_json(call.arguments or {}),
            }
        )
    return rows


def _build_store_diff_rows(seed_result: SeedResult) -> list[dict[str, Any]]:
    return [
        {
            "key": entry.key,
            "change_type": entry.change_type,
            "before_content": entry.before_content,
            "after_content": entry.after_content,
        }
        for entry in seed_result.store_diff.entries
    ]


def _build_seed_row(seed_result: SeedResult) -> dict[str, Any]:
    sorted_scores = [
        _score_payload(dimension_id, score)
        for dimension_id, score in sorted(
            seed_result.score_card.scores.items(),
            key=_score_sort_key,
        )
    ]
    user_gate_failures = [
        row for row in sorted_scores if row["category"] == "user_gate" and not row["passed"]
    ]
    runtime_gate_failures = [
        row for row in sorted_scores if row["category"] == "runtime_gate" and not row["passed"]
    ]
    diagnostic_failures = [
        row for row in sorted_scores if row["category"] == "diagnostic" and not row["passed"]
    ]
    failed_dimension_ids = [row["dimension_id"] for row in sorted_scores if not row["passed"]]
    core_evidence_turns = sorted(
        {
            turn_index
            for row in sorted_scores
            if row["category"] in {"user_gate", "runtime_gate"} and not row["passed"]
            for turn_index in row["evidence_turns"]
        }
    )
    return {
        "seed_result": seed_result,
        "seed_id": seed_result.seed.id,
        "seed_name": seed_result.seed.name,
        "entry_mode": seed_result.seed.entry_mode,
        "turn_count": seed_result.transcript.turn_count,
        "end_reason": seed_result.transcript.end_reason,
        "execution_status": seed_result.score_card.execution_status,
        "blocking_reason": seed_result.score_card.blocking_reason,
        "pass_rate": seed_result.score_card.pass_rate,
        "user_gate_pass_rate": seed_result.score_card.user_gate_pass_rate,
        "runtime_gate_pass_rate": seed_result.score_card.runtime_gate_pass_rate,
        "diagnostic_pass_rate": seed_result.score_card.diagnostic_pass_rate,
        "must_pass_met": seed_result.score_card.must_pass_met,
        "user_gate_met": seed_result.score_card.user_gate_met,
        "runtime_gate_met": seed_result.score_card.runtime_gate_met,
        "assessed_dimension_count": seed_result.score_card.assessed_dimension_count,
        "user_gate_assessed_count": seed_result.score_card.user_gate_assessed_count,
        "runtime_gate_assessed_count": seed_result.score_card.runtime_gate_assessed_count,
        "diagnostic_assessed_count": seed_result.score_card.diagnostic_assessed_count,
        "overall_assessment": seed_result.score_card.overall_assessment,
        "critical_failures": seed_result.score_card.critical_failures,
        "failed_dimension_ids": failed_dimension_ids,
        "core_evidence_turns": core_evidence_turns,
        "scores": sorted_scores,
        "user_gate_failures": user_gate_failures,
        "runtime_gate_failures": runtime_gate_failures,
        "diagnostic_failures": diagnostic_failures,
        "tool_calls": _build_tool_call_rows(seed_result),
        "store_diff_entries": _build_store_diff_rows(seed_result),
        "relevant_final_files": _build_relevant_final_files(seed_result),
        "auditor_prompt_rendered": seed_result.transcript.metadata.get("auditor_prompt_rendered", ""),
        "auditor_policy": seed_result.seed.auditor_policy.model_dump(mode="json"),
        "expected_behaviors": seed_result.seed.expected_behaviors.model_dump(mode="json"),
        "expected_artifacts": seed_result.seed.expected_artifacts.model_dump(mode="json"),
        "user_outcome": seed_result.seed.user_outcome,
        "allowed_good_variants": seed_result.seed.allowed_good_variants,
        "manual_review_checks": seed_result.seed.manual_review_checks,
        "manual_follow_up_notes": _manual_follow_up_notes(seed_result),
        "judge_requested_dimensions": seed_result.score_card.judge_requested_dimensions,
        "judge_dimension_definitions": seed_result.score_card.judge_dimension_definitions,
        "judge_prompt_rendered": seed_result.score_card.judge_prompt_rendered,
        "scoring_focus": seed_result.seed.scoring_focus.model_dump(mode="json"),
    }


def _build_stability_context(run_history: list[EvalResult]) -> dict[str, Any] | None:
    if len(run_history) <= 1:
        return None

    per_seed_runs: dict[str, list[tuple[str, SeedResult]]] = {}
    for run in run_history:
        for seed_result in run.seed_results:
            per_seed_runs.setdefault(seed_result.seed.id, []).append((run.run_id, seed_result))

    def _pass_k(values: list[bool]) -> bool:
        return any(values)

    def _all_pass(values: list[bool]) -> bool:
        return all(values)

    user_gate_pass_k = [
        _pass_k([item.score_card.user_gate_met for _, item in seed_runs])
        for seed_runs in per_seed_runs.values()
    ]
    runtime_gate_pass_k = [
        _pass_k([item.score_card.runtime_gate_met for _, item in seed_runs])
        for seed_runs in per_seed_runs.values()
    ]
    overall_gate_pass_k = [
        _pass_k([item.score_card.must_pass_met for _, item in seed_runs])
        for seed_runs in per_seed_runs.values()
    ]
    stable_gate_pass = [
        _all_pass([item.score_card.must_pass_met for _, item in seed_runs])
        for seed_runs in per_seed_runs.values()
    ]
    flake_count = sum(
        1
        for seed_runs in per_seed_runs.values()
        if len({item.score_card.must_pass_met for _, item in seed_runs}) > 1
    )
    return {
        "run_count": len(run_history),
        "user_gate_pass_k": round(sum(user_gate_pass_k) / len(user_gate_pass_k), 2) if user_gate_pass_k else 0.0,
        "runtime_gate_pass_k": round(sum(runtime_gate_pass_k) / len(runtime_gate_pass_k), 2) if runtime_gate_pass_k else 0.0,
        "overall_gate_pass_k": round(sum(overall_gate_pass_k) / len(overall_gate_pass_k), 2) if overall_gate_pass_k else 0.0,
        "stable_gate_pass_rate": round(sum(stable_gate_pass) / len(stable_gate_pass), 2) if stable_gate_pass else 0.0,
        "flake_count": flake_count,
        "per_seed_runs": {
            seed_id: [
                _build_run_snapshot(run, seed_result)
                for run in run_history
                for current_seed_result in run.seed_results
                if current_seed_result.seed.id == seed_id
                for seed_result in [current_seed_result]
            ]
            for seed_id in per_seed_runs
        },
    }


def build_report_context(eval_result: EvalResult, *, run_history: list[EvalResult] | None = None) -> dict[str, Any]:
    """构建单模型报告的模板上下文。"""
    seed_rows = [_build_seed_row(seed_result) for seed_result in eval_result.seed_results]
    stability = _build_stability_context(run_history or [eval_result])
    if stability is not None:
        for row in seed_rows:
            history_rows = stability["per_seed_runs"].get(row["seed_id"], [])
            row["run_history"] = history_rows
            row["latest_run"] = history_rows[-1] if history_rows else None
            row["gate_flaky"] = len(
                {(item["execution_status"], item["must_pass_met"]) for item in history_rows}
            ) > 1
            row["gate_pass_k"] = any(item["must_pass_met"] for item in history_rows)
    else:
        for row in seed_rows:
            row["run_history"] = []
            row["gate_flaky"] = False
            row["gate_pass_k"] = row["must_pass_met"]
            row["latest_run"] = _build_run_snapshot(eval_result, row["seed_result"])

    all_scores = [
        score
        for seed_result in eval_result.seed_results
        for score in seed_result.score_card.scores.values()
    ]
    user_gate_scores = [score for score_id, score in _iter_scores(eval_result) if is_user_gate_dimension(score_id)]
    runtime_gate_scores = [score for score_id, score in _iter_scores(eval_result) if is_runtime_gate_dimension(score_id)]
    diagnostic_scores = [score for score_id, score in _iter_scores(eval_result) if is_diagnostic_dimension(score_id)]
    user_gate_failures = [row for row in seed_rows if row["user_gate_failures"]]
    runtime_gate_failures = [row for row in seed_rows if row["runtime_gate_failures"]]
    diagnostic_failures = [row for row in seed_rows if row["diagnostic_failures"]]
    execution_blocker_rows = [
        row for row in seed_rows if row["execution_status"] == "blocked"
    ]

    return {
        "run_id": eval_result.run_id,
        "started_at": (
            eval_result.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if eval_result.started_at
            else ""
        ),
        "seed_count": len(eval_result.seed_results),
        "config": eval_result.config_snapshot,
        "profile": _profile_context(eval_result.config_snapshot, len(eval_result.seed_results)),
        "runtime": _runtime_context(eval_result.config_snapshot),
        "summary": {
            "overall_pass_rate": _pass_rate(all_scores),
            "user_gate_pass_rate": _pass_rate(user_gate_scores),
            "runtime_gate_pass_rate": _pass_rate(runtime_gate_scores),
            "diagnostic_pass_rate": _pass_rate(diagnostic_scores),
            "execution_blocker_count": len(execution_blocker_rows),
            "user_gate_failure_count": sum(len(row["user_gate_failures"]) for row in seed_rows),
            "runtime_gate_failure_count": sum(len(row["runtime_gate_failures"]) for row in seed_rows),
            "diagnostic_failure_count": sum(len(row["diagnostic_failures"]) for row in seed_rows),
            "must_pass_success_count": sum(1 for row in seed_rows if row["must_pass_met"]),
        },
        "seed_rows": seed_rows,
        "execution_blocker_rows": execution_blocker_rows,
        "user_gate_failure_rows": user_gate_failures,
        "runtime_gate_failure_rows": runtime_gate_failures,
        "diagnostic_failure_rows": diagnostic_failures,
        "stability": stability,
        "auditor_prompt_template": AUDITOR_SYSTEM_PROMPT,
        "judge_rubric": SCORING_RUBRIC,
    }


def build_comparison_summary(
    results: dict[str, list[EvalResult]],
    model_labels: dict[str, str],
) -> dict[str, Any]:
    """构建多模型对比报告所需的双轴统计。"""
    model_ids = list(results.keys())
    seed_meta: dict[str, str] = {}
    seed_order: list[str] = []
    dimension_ids: set[str] = set()

    for model_runs in results.values():
        for run in model_runs:
            for seed_result in run.seed_results:
                if seed_result.seed.id not in seed_meta:
                    seed_meta[seed_result.seed.id] = seed_result.seed.name
                    seed_order.append(seed_result.seed.id)
                dimension_ids.update(seed_result.score_card.scores.keys())

    model_summaries: list[dict[str, Any]] = []
    for model_id in model_ids:
        seed_results = [
            seed_result
            for run in results[model_id]
            for seed_result in run.seed_results
        ]
        completed_seed_results = [
            seed_result for seed_result in seed_results if seed_result.score_card.execution_status == "completed"
        ]
        blocked_seed_results = [
            seed_result for seed_result in seed_results if seed_result.score_card.execution_status == "blocked"
        ]
        all_scores = [
            score
            for seed_result in completed_seed_results
            for score in seed_result.score_card.scores.values()
        ]
        user_gate_scores = [
            score
            for seed_result in completed_seed_results
            for dimension_id, score in seed_result.score_card.scores.items()
            if is_user_gate_dimension(dimension_id)
        ]
        runtime_gate_scores = [
            score
            for seed_result in completed_seed_results
            for dimension_id, score in seed_result.score_card.scores.items()
            if is_runtime_gate_dimension(dimension_id)
        ]
        diagnostic_scores = [
            score
            for seed_result in completed_seed_results
            for dimension_id, score in seed_result.score_card.scores.items()
            if is_diagnostic_dimension(dimension_id)
        ]
        model_summaries.append(
            {
                "model_id": model_id,
                "label": model_labels.get(model_id, model_id),
                "run_count": len(results[model_id]),
                "overall_pass_rate": _pass_rate(all_scores),
                "user_gate_pass_rate": _pass_rate(user_gate_scores),
                "runtime_gate_pass_rate": _pass_rate(runtime_gate_scores),
                "diagnostic_pass_rate": _pass_rate(diagnostic_scores),
                "blocked_count": len(blocked_seed_results),
                "must_pass_rate": (
                    round(
                        sum(1 for seed_result in completed_seed_results if seed_result.score_card.must_pass_met)
                        / len(completed_seed_results),
                        2,
                    )
                    if completed_seed_results
                    else None
                ),
                "average_seed_pass_rate": _mean_defined(
                    [seed_result.score_card.pass_rate for seed_result in completed_seed_results]
                ),
            }
        )

    seed_rows: list[dict[str, Any]] = []
    for seed_id in seed_order:
        per_model_rows: list[dict[str, Any]] = []
        for model_id in model_ids:
            matching: list[tuple[str, SeedResult]] = [
                (run.run_id, seed_result)
                for run in results[model_id]
                for seed_result in run.seed_results
                if seed_result.seed.id == seed_id
            ]
            completed_matching = [
                (run_id, seed_result)
                for run_id, seed_result in matching
                if seed_result.score_card.execution_status == "completed"
            ]
            user_gate_scores = [
                score
                for _, seed_result in completed_matching
                for dimension_id, score in seed_result.score_card.scores.items()
                if is_user_gate_dimension(dimension_id)
            ]
            runtime_gate_scores = [
                score
                for _, seed_result in completed_matching
                for dimension_id, score in seed_result.score_card.scores.items()
                if is_runtime_gate_dimension(dimension_id)
            ]
            diagnostic_scores = [
                score
                for _, seed_result in completed_matching
                for dimension_id, score in seed_result.score_card.scores.items()
                if is_diagnostic_dimension(dimension_id)
            ]
            per_model_rows.append(
                {
                    "model_id": model_id,
                    "label": model_labels.get(model_id, model_id),
                    "average_pass_rate": _mean_defined(
                        [seed_result.score_card.pass_rate for _, seed_result in completed_matching]
                    ),
                    "user_gate_pass_rate": _pass_rate(user_gate_scores),
                    "runtime_gate_pass_rate": _pass_rate(runtime_gate_scores),
                    "diagnostic_pass_rate": _pass_rate(diagnostic_scores),
                    "blocked_count": sum(
                        1
                        for _, seed_result in matching
                        if seed_result.score_card.execution_status == "blocked"
                    ),
                    "runs": [
                        {
                            "run_id": run_id,
                            "pass_rate": seed_result.score_card.pass_rate,
                            "execution_status": seed_result.score_card.execution_status,
                            "blocking_reason": seed_result.score_card.blocking_reason,
                            "user_gate_met": seed_result.score_card.user_gate_met,
                            "runtime_gate_met": seed_result.score_card.runtime_gate_met,
                            "must_pass_met": seed_result.score_card.must_pass_met,
                            "end_reason": seed_result.transcript.end_reason,
                            "transcript_path": _run_output_paths(
                                next(run for run in results[model_id] if run.run_id == run_id),
                                seed_result.seed.id,
                            )[0],
                            "score_path": _run_output_paths(
                                next(run for run in results[model_id] if run.run_id == run_id),
                                seed_result.seed.id,
                            )[1],
                        }
                        for run_id, seed_result in matching
                    ],
                }
            )
        seed_rows.append(
            {
                "seed_id": seed_id,
                "seed_name": seed_meta.get(seed_id, ""),
                "models": per_model_rows,
            }
        )

    dimension_rows: list[dict[str, Any]] = []
    for dimension_id in sorted(
        dimension_ids,
        key=lambda item: (0 if is_user_gate_dimension(item) else 1 if is_runtime_gate_dimension(item) else 2, item),
    ):
        per_model_rows = []
        for model_id in model_ids:
            scores = [
                score
                for run in results[model_id]
                for seed_result in run.seed_results
                for candidate_id, score in seed_result.score_card.scores.items()
                if candidate_id == dimension_id
            ]
            per_model_rows.append(
                {
                    "model_id": model_id,
                    "label": model_labels.get(model_id, model_id),
                    "pass_rate": _pass_rate(scores),
                    "pass_count": sum(1 for score in scores if score.passed),
                    "total_count": len(scores),
                }
            )
        dimension_rows.append(
            {
                "dimension_id": dimension_id,
                "category": _dimension_category(dimension_id),
                "score_source": "deterministic" if dimension_id in DETERMINISTIC_DIMENSIONS else "llm",
                "models": per_model_rows,
            }
        )

    return {
        "model_ids": model_ids,
        "profile": _profile_context(
            next(
                (
                    run.config_snapshot
                    for model_runs in results.values()
                    for run in model_runs
                ),
                {},
            ),
            len(seed_order),
        ),
        "runtime": _runtime_context(
            next(
                (
                    run.config_snapshot
                    for model_runs in results.values()
                    for run in model_runs
                ),
                {},
            )
        ),
        "model_summaries": model_summaries,
        "seed_rows": seed_rows,
        "dimension_rows": dimension_rows,
        "results": results,
    }


def generate_report(
    eval_result: EvalResult,
    output_dir: Path,
    *,
    run_history: list[EvalResult] | None = None,
) -> Path:
    """渲染单模型 HTML 评估报告。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    env.filters["display_percent"] = _display_percent
    env.filters["pretty_json"] = _pretty_json
    env.filters["markdown_html"] = _render_markdown_html
    template = env.get_template("report.html.j2")

    html = template.render(**build_report_context(eval_result, run_history=run_history))

    report_path = output_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info("Report generated: %s", report_path)
    return report_path


def generate_comparison_report(
    results: dict[str, list[EvalResult]],
    model_labels: dict[str, str],
    output_dir: Path,
) -> Path:
    """渲染多模型对比 HTML 报告。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    env.filters["display_percent"] = _display_percent
    template = env.get_template("comparison.html.j2")

    html = template.render(**build_comparison_summary(results, model_labels))

    report_path = output_dir / "comparison.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info("Comparison report generated: %s", report_path)
    return report_path


def _iter_scores(eval_result: EvalResult) -> list[tuple[str, DimensionScore]]:
    return [
        (dimension_id, score)
        for seed_result in eval_result.seed_results
        for dimension_id, score in seed_result.score_card.scores.items()
    ]
