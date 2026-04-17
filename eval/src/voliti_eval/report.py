# ABOUTME: HTML 评估报告生成器
# ABOUTME: 以契约失败与行为失败双视角渲染单模型与多模型报告

from __future__ import annotations

import json
import logging
from pathlib import Path
from statistics import mean
from typing import Any

from jinja2 import Environment, FileSystemLoader

from voliti_eval.auditor import AUDITOR_SYSTEM_PROMPT
from voliti_eval.graders import DETERMINISTIC_DIMENSIONS
from voliti_eval.judge import BEHAVIOR_DIMENSIONS, SCORING_RUBRIC
from voliti_eval.models import DimensionScore, EvalResult, SeedResult

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _is_contract_dimension(dimension_id: str) -> bool:
    return dimension_id in DETERMINISTIC_DIMENSIONS or dimension_id.startswith("contract_")


def _dimension_category(dimension_id: str) -> str:
    return "contract" if _is_contract_dimension(dimension_id) else "behavior"


def _score_sort_key(item: tuple[str, DimensionScore]) -> tuple[int, str]:
    dimension_id, _ = item
    return (0 if _is_contract_dimension(dimension_id) else 1, dimension_id)


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


def _pass_rate(scores: list[DimensionScore]) -> float:
    if not scores:
        return 0.0
    return round(sum(1 for score in scores if score.passed) / len(scores), 2)


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
        files.append({"key": key, "content": artifact.content})
    return files


def _build_tool_call_rows(seed_result: SeedResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for call in seed_result.tool_calls:
        rows.append(
            {
                "turn_index": call.turn_index,
                "name": call.name,
                "arguments": json.dumps(call.arguments or {}, ensure_ascii=False, indent=2),
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
    contract_failures = [
        row for row in sorted_scores if row["category"] == "contract" and not row["passed"]
    ]
    behavior_failures = [
        row for row in sorted_scores if row["category"] == "behavior" and not row["passed"]
    ]
    contract_scores = [
        seed_result.score_card.scores[row["dimension_id"]]
        for row in sorted_scores
        if row["category"] == "contract"
    ]
    behavior_scores = [
        seed_result.score_card.scores[row["dimension_id"]]
        for row in sorted_scores
        if row["category"] == "behavior"
    ]
    return {
        "seed_result": seed_result,
        "seed_id": seed_result.seed.id,
        "seed_name": seed_result.seed.name,
        "entry_mode": seed_result.seed.entry_mode,
        "turn_count": seed_result.transcript.turn_count,
        "end_reason": seed_result.transcript.end_reason,
        "pass_rate_pct": round(seed_result.score_card.pass_rate * 100),
        "contract_pass_rate": _pass_rate(contract_scores),
        "behavior_pass_rate": _pass_rate(behavior_scores),
        "must_pass_met": seed_result.score_card.must_pass_met,
        "overall_assessment": seed_result.score_card.overall_assessment,
        "critical_failures": seed_result.score_card.critical_failures,
        "scores": sorted_scores,
        "contract_failures": contract_failures,
        "behavior_failures": behavior_failures,
        "tool_calls": _build_tool_call_rows(seed_result),
        "store_diff_entries": _build_store_diff_rows(seed_result),
        "relevant_final_files": _build_relevant_final_files(seed_result),
    }


def build_report_context(eval_result: EvalResult) -> dict[str, Any]:
    """构建单模型报告的模板上下文。"""
    seed_rows = [_build_seed_row(seed_result) for seed_result in eval_result.seed_results]
    all_scores = [
        score
        for seed_result in eval_result.seed_results
        for score in seed_result.score_card.scores.values()
    ]
    contract_scores = [score for score_id, score in _iter_scores(eval_result) if _is_contract_dimension(score_id)]
    behavior_scores = [score for score_id, score in _iter_scores(eval_result) if not _is_contract_dimension(score_id)]
    contract_failures = [row for row in seed_rows if row["contract_failures"]]
    behavior_failures = [row for row in seed_rows if row["behavior_failures"]]

    return {
        "run_id": eval_result.run_id,
        "started_at": (
            eval_result.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if eval_result.started_at
            else ""
        ),
        "seed_count": len(eval_result.seed_results),
        "config": eval_result.config_snapshot,
        "summary": {
            "overall_pass_rate": _pass_rate(all_scores),
            "contract_pass_rate": _pass_rate(contract_scores),
            "behavior_pass_rate": _pass_rate(behavior_scores),
            "contract_failure_count": sum(len(row["contract_failures"]) for row in seed_rows),
            "behavior_failure_count": sum(len(row["behavior_failures"]) for row in seed_rows),
            "must_pass_success_count": sum(1 for row in seed_rows if row["must_pass_met"]),
        },
        "seed_rows": seed_rows,
        "contract_failure_rows": contract_failures,
        "behavior_failure_rows": behavior_failures,
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
        all_scores = [
            score
            for seed_result in seed_results
            for score in seed_result.score_card.scores.values()
        ]
        contract_scores = [
            score
            for seed_result in seed_results
            for dimension_id, score in seed_result.score_card.scores.items()
            if _is_contract_dimension(dimension_id)
        ]
        behavior_scores = [
            score
            for seed_result in seed_results
            for dimension_id, score in seed_result.score_card.scores.items()
            if not _is_contract_dimension(dimension_id)
        ]
        model_summaries.append(
            {
                "model_id": model_id,
                "label": model_labels.get(model_id, model_id),
                "run_count": len(results[model_id]),
                "overall_pass_rate": _pass_rate(all_scores),
                "contract_pass_rate": _pass_rate(contract_scores),
                "behavior_pass_rate": _pass_rate(behavior_scores),
                "must_pass_rate": round(
                    sum(1 for seed_result in seed_results if seed_result.score_card.must_pass_met)
                    / len(seed_results),
                    2,
                )
                if seed_results
                else 0.0,
                "average_seed_pass_rate": round(
                    mean(seed_result.score_card.pass_rate for seed_result in seed_results),
                    2,
                )
                if seed_results
                else 0.0,
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
            contract_scores = [
                score
                for _, seed_result in matching
                for dimension_id, score in seed_result.score_card.scores.items()
                if _is_contract_dimension(dimension_id)
            ]
            behavior_scores = [
                score
                for _, seed_result in matching
                for dimension_id, score in seed_result.score_card.scores.items()
                if not _is_contract_dimension(dimension_id)
            ]
            per_model_rows.append(
                {
                    "model_id": model_id,
                    "label": model_labels.get(model_id, model_id),
                    "average_pass_rate": round(
                        mean(seed_result.score_card.pass_rate for _, seed_result in matching),
                        2,
                    )
                    if matching
                    else 0.0,
                    "contract_pass_rate": _pass_rate(contract_scores),
                    "behavior_pass_rate": _pass_rate(behavior_scores),
                    "runs": [
                        {
                            "run_id": run_id,
                            "pass_rate": seed_result.score_card.pass_rate,
                            "must_pass_met": seed_result.score_card.must_pass_met,
                            "end_reason": seed_result.transcript.end_reason,
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
    for dimension_id in sorted(dimension_ids, key=lambda item: (0 if _is_contract_dimension(item) else 1, item)):
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
                "score_source": "deterministic" if _is_contract_dimension(dimension_id) else "llm",
                "models": per_model_rows,
            }
        )

    return {
        "model_ids": model_ids,
        "model_summaries": model_summaries,
        "seed_rows": seed_rows,
        "dimension_rows": dimension_rows,
        "results": results,
    }


def generate_report(
    eval_result: EvalResult,
    output_dir: Path,
) -> Path:
    """渲染单模型 HTML 评估报告。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")

    html = template.render(**build_report_context(eval_result))

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
