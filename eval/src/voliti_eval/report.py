# ABOUTME: HTML 评估报告生成器
# ABOUTME: 渲染单模型报告和多模型对比报告为单文件 HTML

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from voliti_eval.auditor import AUDITOR_SYSTEM_PROMPT
from voliti_eval.judge import SCORING_RUBRIC
from voliti_eval.models import EvalResult

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def generate_report(eval_result: EvalResult, output_dir: Path) -> Path:
    """渲染单模型 HTML 评估报告。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")

    seen: set[str] = set()
    for sr in eval_result.seed_results:
        seen.update(sr.score_card.scores.keys())
    all_dimensions = sorted(seen)

    html = template.render(
        run_id=eval_result.run_id,
        started_at=eval_result.started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if eval_result.started_at else "",
        seed_count=len(eval_result.seed_results),
        config=eval_result.config_snapshot,
        seed_results=eval_result.seed_results,
        all_dimensions=all_dimensions,
        auditor_prompt_template=AUDITOR_SYSTEM_PROMPT,
        judge_rubric=SCORING_RUBRIC,
    )

    report_path = output_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info("Report generated: %s", report_path)
    return report_path


def generate_comparison_report(
    results: dict[str, list[EvalResult]],
    model_labels: dict[str, str],
    output_dir: Path,
) -> Path:
    """渲染多模型对比 HTML 报告。

    Args:
        results: model_id → [EvalResult per run]
        model_labels: model_id → 显示名（如 "GPT-5.4"）
        output_dir: 输出目录
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("comparison.html.j2")

    model_ids = list(results.keys())

    # 收集所有 seed ID 和维度 ID
    seed_ids: list[str] = []
    seed_names: dict[str, str] = {}
    all_dimensions: set[str] = set()

    for model_id, runs in results.items():
        for run in runs:
            for sr in run.seed_results:
                if sr.seed.id not in seed_names:
                    seed_ids.append(sr.seed.id)
                    seed_names[sr.seed.id] = sr.seed.name
                all_dimensions.update(sr.score_card.scores.keys())

    seed_ids = sorted(set(seed_ids))
    dim_ids = sorted(all_dimensions)

    # 构建对比数据矩阵
    # matrix[model_id][seed_id][dim_id] = [passed_in_run_1, passed_in_run_2, ...]
    matrix: dict[str, dict[str, dict[str, list[bool]]]] = {}
    for model_id, runs in results.items():
        matrix[model_id] = {}
        for run in runs:
            for sr in run.seed_results:
                if sr.seed.id not in matrix[model_id]:
                    matrix[model_id][sr.seed.id] = {}
                for dim_id, dim_score in sr.score_card.scores.items():
                    if dim_id not in matrix[model_id][sr.seed.id]:
                        matrix[model_id][sr.seed.id][dim_id] = []
                    matrix[model_id][sr.seed.id][dim_id].append(dim_score.passed)

    # 计算 pass@k 和 pass^k
    def pass_at_k(bools: list[bool]) -> bool:
        return any(bools)

    def pass_all_k(bools: list[bool]) -> bool:
        return all(bools)

    def pass_count(bools: list[bool]) -> str:
        return f"{sum(bools)}/{len(bools)}"

    # 计算每 seed 每模型的 pass rate 中位数
    seed_pass_rates: dict[str, dict[str, list[float]]] = {}
    for model_id, runs in results.items():
        seed_pass_rates[model_id] = {}
        for run in runs:
            for sr in run.seed_results:
                if sr.seed.id not in seed_pass_rates[model_id]:
                    seed_pass_rates[model_id][sr.seed.id] = []
                seed_pass_rates[model_id][sr.seed.id].append(sr.score_card.pass_rate)

    # 瓶颈诊断
    bottlenecks: dict[str, list[dict[str, Any]]] = {
        "prompt": [],     # 两模型均失败
        "model": [],      # 仅一个模型失败
        "resolved": [],   # 两模型均通过
    }
    for dim_id in dim_ids:
        model_pass_all: dict[str, bool] = {}
        model_pass_any: dict[str, bool] = {}
        for model_id in model_ids:
            all_bools: list[bool] = []
            for seed_id in seed_ids:
                bools = matrix.get(model_id, {}).get(seed_id, {}).get(dim_id, [])
                all_bools.extend(bools)
            if all_bools:
                model_pass_all[model_id] = all(all_bools)
                model_pass_any[model_id] = any(all_bools)
            else:
                model_pass_all[model_id] = True
                model_pass_any[model_id] = True

        if all(model_pass_all.values()):
            bottlenecks["resolved"].append({"dim": dim_id})
        elif not any(model_pass_all.values()):
            bottlenecks["prompt"].append({"dim": dim_id})
        else:
            winners = [m for m, v in model_pass_all.items() if v]
            losers = [m for m, v in model_pass_all.items() if not v]
            bottlenecks["model"].append({
                "dim": dim_id,
                "winners": winners,
                "losers": losers,
            })

    html = template.render(
        model_ids=model_ids,
        model_labels=model_labels,
        seed_ids=seed_ids,
        seed_names=seed_names,
        dim_ids=dim_ids,
        matrix=matrix,
        seed_pass_rates=seed_pass_rates,
        bottlenecks=bottlenecks,
        results=results,
        pass_at_k=pass_at_k,
        pass_all_k=pass_all_k,
        pass_count=pass_count,
        num_runs=max(len(runs) for runs in results.values()),
    )

    report_path = output_dir / "comparison.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info("Comparison report generated: %s", report_path)
    return report_path
