# ABOUTME: CLI 入口，解析参数并调用评估编排器
# ABOUTME: 支持 full/lite 两种评估 profile 和多模型对比模式

from __future__ import annotations

import asyncio
import functools
import json
import logging
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import click

from voliti_eval.config import EvalConfig, load_config, load_seeds
from voliti_eval.judge import Judge, SCORING_RUBRIC_LITE
from voliti_eval.models import EvalResult, Seed
from voliti_eval.report import generate_comparison_report, generate_report
from voliti_eval.runner import run_evaluation
from voliti_eval.transcript import save_transcript

# lite profile 参数
_LITE_MIN_TURNS_BEFORE_END = 4


@click.command()
@click.option("--seeds", default="all", help="逗号分隔的 seed ID（如 01,03,06）或 'all'")
@click.option("--server-url", default=None, help="LangGraph dev server URL")
@click.option("--assistant-id", default=None, help="LangGraph assistant ID")
@click.option("--output", "output_dir", default=None, type=click.Path(), help="输出目录")
@click.option("--max-turns", default=None, type=int, help="覆盖所有 seed 的 max_turns")
@click.option("--dry-run", is_flag=True, help="仅验证 seed 配置，不运行对话")
@click.option("--verbose", is_flag=True, help="详细日志")
@click.option("--compare", is_flag=True, help="对多个模型运行相同 seed 并生成对比报告")
@click.option("--models", default=None, help="逗号分隔的 assistant ID（如 'coach,coach_qwen'）")
@click.option("--runs", default=1, type=int, help="每个 seed 重复运行次数（统计可靠性）")
@click.option(
    "--profile",
    default="lite",
    type=click.Choice(["full", "lite"]),
    help="评估 Profile：lite（10 维 10 seed，默认）或 full（15 维 16 seed）",
)
def main(
    seeds: str,
    server_url: str | None,
    assistant_id: str | None,
    output_dir: str | None,
    max_turns: int | None,
    dry_run: bool,
    verbose: bool,
    compare: bool,
    models: str | None,
    runs: int,
    profile: str,
) -> None:
    """Voliti Coach Agent 行为评估工具。"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    eval_root = Path(__file__).resolve().parent.parent.parent
    output_path = Path(output_dir) if output_dir else None

    config = load_config(
        eval_root,
        server_url=server_url,
        assistant_id=assistant_id,
        max_turns=max_turns,
        output_dir=output_path,
    )

    # 根据 profile 选择 seed 目录
    is_lite = profile == "lite"
    seed_dir = config.seed_directory_lite if is_lite else config.seed_directory

    all_seeds = load_seeds(seed_dir)
    if not all_seeds:
        click.echo(f"错误：未找到任何 seed YAML 文件（{seed_dir}）", err=True)
        sys.exit(1)

    # 过滤 seed
    selected: list[Seed]
    if seeds == "all":
        selected = all_seeds
    else:
        seed_ids = {s.strip() for s in seeds.split(",")}
        selected = [s for s in all_seeds if s.id in seed_ids or s.id.split("_")[0] in seed_ids]
        if not selected:
            click.echo(f"错误：未匹配到任何 seed（输入: {seeds}）", err=True)
            click.echo(f"可用 seed: {', '.join(s.id for s in all_seeds)}", err=True)
            sys.exit(1)

    click.echo(f"Profile: {profile}")
    click.echo(f"Seeds: {len(selected)}/{len(all_seeds)} selected")
    for s in selected:
        click.echo(f"  {s.id} — {s.name}")

    if dry_run:
        click.echo("\n✓ Dry run: 所有 seed 配置有效")
        for s in selected:
            click.echo(f"\n[{s.id}] {s.name}")
            click.echo(f"  Persona: {s.persona.name} ({s.persona.language})")
            click.echo(f"  Max turns: {s.max_turns}")
            click.echo(f"  Pre-state: {'yes' if s.pre_state else 'no (onboarding)'}")
            click.echo(f"  Must-Pass: {', '.join(s.scoring_focus.primary)}")
        if compare:
            model_ids = [m.strip() for m in (models or "coach,coach_qwen").split(",")]
            click.echo(f"\n对比模式: {model_ids} × {runs} runs")
        return

    if compare:
        model_ids = [m.strip() for m in (models or "coach,coach_qwen").split(",")]
        asyncio.run(_run_compare(selected, config, model_ids, runs, is_lite=is_lite))
    else:
        asyncio.run(_run(selected, config, is_lite=is_lite))


async def _run(seeds: list[Seed], config: EvalConfig, *, is_lite: bool = False) -> None:
    """异步执行单模型评估流程。"""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    label = "lite" if is_lite else "full"
    output_dir = config.output_directory / f"{timestamp}_{label}"
    transcripts_dir = output_dir / "transcripts"
    scores_dir = output_dir / "scores"

    judge = Judge(config.judge_model, timeout=config.turn_timeout_seconds)
    judge_fn = (
        functools.partial(judge.score, rubric_override=SCORING_RUBRIC_LITE)
        if is_lite
        else judge.score
    )
    rubric_for_report = SCORING_RUBRIC_LITE if is_lite else None

    click.echo(f"\n开始评估 → {output_dir}")
    click.echo(f"Server: {config.server_url}")
    click.echo(f"Assistant: {config.assistant_id}")
    click.echo()

    result = await run_evaluation(
        seeds, config, judge_fn=judge_fn, output_dir=str(output_dir),
        min_turns_before_end=_LITE_MIN_TURNS_BEFORE_END if is_lite else None,
    )

    _save_results(result, transcripts_dir, scores_dir)

    report_path = generate_report(result, output_dir, judge_rubric=rubric_for_report)
    click.echo(f"\n报告已生成: {report_path}")

    _print_summary([result])


async def _run_compare(
    seeds: list[Seed],
    config: EvalConfig,
    model_ids: list[str],
    runs_per_model: int,
    *,
    is_lite: bool = False,
) -> None:
    """对多个模型顺序运行评估，生成对比报告。"""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    label = "lite" if is_lite else "full"
    compare_dir = config.output_directory / f"compare_{timestamp}_{label}"

    judge = Judge(config.judge_model, timeout=config.turn_timeout_seconds)
    judge_fn = (
        functools.partial(judge.score, rubric_override=SCORING_RUBRIC_LITE)
        if is_lite
        else judge.score
    )
    rubric_for_report = SCORING_RUBRIC_LITE if is_lite else None

    click.echo(f"\n开始多模型对比 → {compare_dir}")
    click.echo(f"Server: {config.server_url}")
    click.echo(f"Models: {model_ids}")
    click.echo(f"Runs per model: {runs_per_model}")
    click.echo()

    all_results: dict[str, list[EvalResult]] = {}

    for model_id in model_ids:
        label = config.model_labels.get(model_id, model_id)
        click.echo(f"\n{'=' * 50}")
        click.echo(f"模型: {label} (assistant_id={model_id})")
        click.echo(f"{'=' * 50}")

        model_config = replace(config, assistant_id=model_id)
        model_results: list[EvalResult] = []

        for run_idx in range(1, runs_per_model + 1):
            click.echo(f"\n--- Run {run_idx}/{runs_per_model} ---")
            run_dir = compare_dir / model_id / f"run_{run_idx}"
            transcripts_dir = run_dir / "transcripts"
            scores_dir = run_dir / "scores"

            result = await run_evaluation(
                seeds, model_config, judge_fn=judge_fn, output_dir=str(run_dir),
                min_turns_before_end=_LITE_MIN_TURNS_BEFORE_END if is_lite else None,
            )
            _save_results(result, transcripts_dir, scores_dir)
            model_results.append(result)

        # 为每个模型生成独立报告（使用最后一次 run 的结果）
        model_report_dir = compare_dir / model_id
        generate_report(model_results[-1], model_report_dir, judge_rubric=rubric_for_report)

        all_results[model_id] = model_results

    # 生成对比报告
    comparison_path = generate_comparison_report(
        all_results, config.model_labels, compare_dir,
    )
    click.echo(f"\n对比报告已生成: {comparison_path}")

    # 打印所有模型的总结
    click.echo(f"\n{'=' * 60}")
    click.echo("多模型对比完成")
    for model_id, results in all_results.items():
        label = config.model_labels.get(model_id, model_id)
        click.echo(f"\n  [{label}] ({len(results)} runs)")
        _print_summary(results, indent=4)
    click.echo(f"{'=' * 60}")


def _save_results(
    result: EvalResult,
    transcripts_dir: Path,
    scores_dir: Path,
) -> None:
    """保存 transcript 和评分文件。"""
    for sr in result.seed_results:
        save_transcript(sr.transcript, transcripts_dir)

        scores_dir.mkdir(parents=True, exist_ok=True)
        score_path = scores_dir / f"{sr.seed.id}.json"
        score_data = sr.score_card.model_dump(mode="json")
        score_path.write_text(
            json.dumps(score_data, ensure_ascii=False, indent=2), encoding="utf-8",
        )


def _print_summary(results: list[EvalResult], indent: int = 2) -> None:
    """打印评估结果摘要。"""
    prefix = " " * indent
    for result in results:
        for sr in result.seed_results:
            status = "✓" if sr.score_card.must_pass_met and sr.score_card.pass_rate >= 0.7 else "!"
            click.echo(
                f"{prefix}[{status}] {sr.seed.id} — "
                f"pass {sr.score_card.pass_rate:.0%} "
                f"must={'✓' if sr.score_card.must_pass_met else '✗'} "
                f"({sr.transcript.end_reason})"
            )
