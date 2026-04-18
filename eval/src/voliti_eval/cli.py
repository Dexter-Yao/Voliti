# ABOUTME: CLI 入口，解析参数并调用评估编排器
# ABOUTME: 保留 lite/full 与 compare 外壳，但内部统一为混合评分架构

from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, TypeVar

import click

from voliti_eval.config import EvalConfig, load_config, load_seeds
from voliti_eval.judge import Judge
from voliti_eval.models import EvalResult, Seed
from voliti_eval.report import generate_comparison_report, generate_report
from voliti_eval.runner import run_evaluation
from voliti_eval.transcript import save_transcript

SeedLike = TypeVar("SeedLike")


def _seed_id(seed: SeedLike) -> str:
    if isinstance(seed, dict):
        return str(seed["id"])
    return str(getattr(seed, "id"))


def _seed_name(seed: SeedLike) -> str:
    if isinstance(seed, dict):
        return str(seed["name"])
    return str(getattr(seed, "name"))


def load_profile_seeds(
    config: EvalConfig,
    profile: str,
    *,
    seed_loader: Callable[[Path], list[SeedLike]] = load_seeds,
) -> list[SeedLike]:
    """按 profile 加载 seed。

    `full` 语义为 lite 10 个基础场景 + 全部扩展场景。
    """
    if profile == "lite":
        return list(seed_loader(config.seed_directory_lite))
    if profile != "full":
        raise ValueError(f"Unsupported profile: {profile}")

    combined: list[SeedLike] = []
    seen_ids: set[str] = set()
    for directory in (config.seed_directory_lite, config.seed_directory):
        for seed in seed_loader(directory):
            seed_id = _seed_id(seed)
            if seed_id in seen_ids:
                continue
            seen_ids.add(seed_id)
            combined.append(seed)
    return combined


def filter_seeds(all_seeds: list[SeedLike], selector: str) -> list[SeedLike]:
    """按 seed ID 或前缀过滤种子列表。"""
    if selector == "all":
        return list(all_seeds)

    seed_ids = {item.strip() for item in selector.split(",") if item.strip()}
    return [
        seed
        for seed in all_seeds
        if _seed_id(seed) in seed_ids or _seed_id(seed).split("_")[0] in seed_ids
    ]


@click.command()
@click.option("--seeds", default="all", help="逗号分隔的 seed ID（如 L01,14）或 'all'")
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
    help="评估 Profile：lite（10 seed，默认）或 full（lite 10 + 全部扩展）",
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

    try:
        all_seeds = load_profile_seeds(config, profile)
    except ValueError as exc:
        click.echo(f"错误：{exc}", err=True)
        sys.exit(1)
    if not all_seeds:
        click.echo(f"错误：未找到任何 seed YAML 文件（profile={profile}）", err=True)
        sys.exit(1)

    selected = filter_seeds(all_seeds, seeds)
    if not selected:
        click.echo(f"错误：未匹配到任何 seed（输入: {seeds}）", err=True)
        click.echo(f"可用 seed: {', '.join(_seed_id(seed) for seed in all_seeds)}", err=True)
        sys.exit(1)

    click.echo(f"Profile: {profile}")
    click.echo(f"Seeds: {len(selected)}/{len(all_seeds)} selected")
    for seed in selected:
        click.echo(f"  {_seed_id(seed)} — {_seed_name(seed)}")

    if dry_run:
        _print_dry_run(selected, compare, models, runs)
        return

    if compare:
        model_ids = [model.strip() for model in (models or "coach,coach_qwen").split(",") if model.strip()]
        asyncio.run(_run_compare(selected, config, model_ids, runs, profile=profile))
    else:
        asyncio.run(_run(selected, config, profile=profile))


def _print_dry_run(
    seeds: list[Seed],
    compare: bool,
    models: str | None,
    runs: int,
) -> None:
    click.echo("\n✓ Dry run: 所有 seed 配置有效")
    for seed in seeds:
        click.echo(f"\n[{seed.id}] {seed.name}")
        click.echo(f"  Entry mode: {seed.entry_mode}")
        click.echo(f"  Persona: {seed.persona.name} ({seed.persona.language})")
        click.echo(f"  Max turns: {seed.max_turns}")
        click.echo(f"  Required artifacts: {', '.join(seed.expected_artifacts.required_keys) or 'none'}")
        click.echo(f"  Judge dimensions: {', '.join(seed.judge_dimensions) or 'none'}")
        click.echo(f"  Must-pass: {', '.join(seed.scoring_focus.primary) or 'none'}")
    if compare:
        model_ids = [model.strip() for model in (models or "coach,coach_qwen").split(",") if model.strip()]
        click.echo(f"\n对比模式: {model_ids} × {runs} runs")


async def _run(seeds: list[Seed], config: EvalConfig, *, profile: str) -> None:
    """异步执行单模型评估流程。"""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_dir = config.output_directory / f"{timestamp}_{profile}"
    transcripts_dir = output_dir / "transcripts"
    scores_dir = output_dir / "scores"

    judge = Judge(config.judge_model, timeout=config.turn_timeout_seconds)

    click.echo(f"\n开始评估 → {output_dir}")
    click.echo(f"Server: {config.server_url}")
    click.echo(f"Assistant: {config.assistant_id}")
    click.echo()

    result = await run_evaluation(
        seeds,
        config,
        judge_fn=judge.score,
        output_dir=str(output_dir),
    )

    _save_results(result, transcripts_dir, scores_dir)

    report_path = generate_report(result, output_dir)
    click.echo(f"\n报告已生成: {report_path}")

    _print_summary([result])


async def _run_compare(
    seeds: list[Seed],
    config: EvalConfig,
    model_ids: list[str],
    runs_per_model: int,
    *,
    profile: str,
) -> None:
    """对多个模型顺序运行评估，生成对比报告。"""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    compare_dir = config.output_directory / f"compare_{timestamp}_{profile}"

    judge = Judge(config.judge_model, timeout=config.turn_timeout_seconds)

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
                seeds,
                model_config,
                judge_fn=judge.score,
                output_dir=str(run_dir),
            )
            _save_results(result, transcripts_dir, scores_dir)
            model_results.append(result)

        generate_report(model_results[-1], compare_dir / model_id)
        all_results[model_id] = model_results

    comparison_path = generate_comparison_report(all_results, config.model_labels, compare_dir)
    click.echo(f"\n对比报告已生成: {comparison_path}")

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
    for seed_result in result.seed_results:
        save_transcript(seed_result.transcript, transcripts_dir)

        scores_dir.mkdir(parents=True, exist_ok=True)
        score_path = scores_dir / f"{seed_result.seed.id}.json"
        score_data = seed_result.score_card.model_dump(mode="json")
        score_path.write_text(
            json.dumps(score_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _print_summary(results: list[EvalResult], indent: int = 2) -> None:
    """打印评估结果摘要。"""
    prefix = " " * indent
    for result in results:
        for seed_result in result.seed_results:
            status = (
                "✓"
                if seed_result.score_card.must_pass_met and seed_result.score_card.pass_rate >= 0.7
                else "!"
            )
            click.echo(
                f"{prefix}[{status}] {seed_result.seed.id} — "
                f"pass {seed_result.score_card.pass_rate:.0%} "
                f"must={'✓' if seed_result.score_card.must_pass_met else '✗'} "
                f"({seed_result.transcript.end_reason})"
            )
