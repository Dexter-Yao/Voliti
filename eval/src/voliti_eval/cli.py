# ABOUTME: CLI 入口，解析参数并调用评估编排器
# ABOUTME: 支持运行全部/指定 seed、dry-run 验证、输出目录指定

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import click

from voliti_eval.config import EvalConfig, load_config, load_seeds
from voliti_eval.judge import Judge
from voliti_eval.models import Seed
from voliti_eval.report import generate_report
from voliti_eval.runner import run_evaluation
from voliti_eval.transcript import save_transcript


@click.command()
@click.option("--seeds", default="all", help="逗号分隔的 seed ID（如 01,03,06）或 'all'")
@click.option("--server-url", default=None, help="LangGraph dev server URL")
@click.option("--assistant-id", default=None, help="LangGraph assistant ID")
@click.option("--output", "output_dir", default=None, type=click.Path(), help="输出目录")
@click.option("--max-turns", default=None, type=int, help="覆盖所有 seed 的 max_turns")
@click.option("--dry-run", is_flag=True, help="仅验证 seed 配置，不运行对话")
@click.option("--verbose", is_flag=True, help="详细日志")
def main(
    seeds: str,
    server_url: str | None,
    assistant_id: str | None,
    output_dir: str | None,
    max_turns: int | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Voliti Coach Agent 行为评估工具。"""
    # 配置日志
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # 加载配置
    eval_root = Path(__file__).resolve().parent.parent.parent
    output_path = Path(output_dir) if output_dir else None

    config = load_config(
        eval_root,
        server_url=server_url,
        assistant_id=assistant_id,
        max_turns=max_turns,
        output_dir=output_path,
    )

    # 加载 seed
    all_seeds = load_seeds(config.seed_directory)
    if not all_seeds:
        click.echo("错误：未找到任何 seed YAML 文件", err=True)
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

    click.echo(f"Seeds: {len(selected)}/{len(all_seeds)} selected")
    for s in selected:
        click.echo(f"  {s.id} — {s.name}")

    if dry_run:
        click.echo("\n✓ Dry run: 所有 seed 配置有效")
        # 输出 seed 摘要
        for s in selected:
            click.echo(f"\n[{s.id}] {s.name}")
            click.echo(f"  Persona: {s.persona.name} ({s.persona.language})")
            click.echo(f"  Max turns: {s.max_turns}")
            click.echo(f"  Pre-state: {'yes' if s.pre_state else 'no (onboarding)'}")
            click.echo(f"  Primary focus: {', '.join(s.scoring_focus.primary)}")
        return

    # 运行评估
    asyncio.run(_run(selected, config))


async def _run(seeds: list[Seed], config: EvalConfig) -> None:
    """异步执行评估流程。"""
    # 创建输出目录
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_dir = config.output_directory / timestamp
    transcripts_dir = output_dir / "transcripts"
    scores_dir = output_dir / "scores"

    # 创建 Judge
    judge = Judge(config.judge_model)

    click.echo(f"\n开始评估 → {output_dir}")
    click.echo(f"Server: {config.server_url}")
    click.echo(f"Auditor: {config.auditor_model.deployment} (reasoning={config.auditor_model.reasoning_effort})")
    click.echo(f"Judge: {config.judge_model.deployment} (reasoning={config.judge_model.reasoning_effort})")
    click.echo()

    result = await run_evaluation(seeds, config, judge_fn=judge.score, output_dir=str(output_dir))

    # 保存 transcript 和评分
    for sr in result.seed_results:
        t_path = save_transcript(sr.transcript, transcripts_dir)
        click.echo(f"  Transcript: {t_path}")

        # 保存评分
        scores_dir.mkdir(parents=True, exist_ok=True)
        score_path = scores_dir / f"{sr.seed.id}.json"
        score_data = sr.score_card.model_dump(mode="json")
        score_path.write_text(json.dumps(score_data, ensure_ascii=False, indent=2), encoding="utf-8")
        click.echo(f"  Score: {score_path} (avg={sr.score_card.weighted_average})")

    # 生成报告
    report_path = generate_report(result, output_dir)
    click.echo(f"\n报告已生成: {report_path}")

    # 总结
    click.echo("\n" + "=" * 50)
    click.echo("评估完成")
    for sr in result.seed_results:
        status = "✓" if sr.score_card.weighted_average >= 3.5 else "!"
        click.echo(f"  [{status}] {sr.seed.id} — avg {sr.score_card.weighted_average:.1f} ({sr.transcript.end_reason})")
    click.echo("=" * 50)
