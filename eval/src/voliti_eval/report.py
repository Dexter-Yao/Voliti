# ABOUTME: HTML 评估报告生成器
# ABOUTME: 渲染对话记录、评分可视化、内嵌 base64 图片为单文件 HTML

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from voliti_eval.auditor import AUDITOR_SYSTEM_PROMPT
from voliti_eval.judge import SCORING_RUBRIC
from voliti_eval.models import EvalResult

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def generate_report(eval_result: EvalResult, output_dir: Path) -> Path:
    """渲染 HTML 评估报告。

    Args:
        eval_result: 完整评估结果。
        output_dir: 输出目录。

    Returns:
        生成的 HTML 文件路径。
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")

    # 收集所有出现过的评分维度
    all_dimensions: list[str] = []
    seen: set[str] = set()
    for sr in eval_result.seed_results:
        for dim_id in sr.score_card.scores:
            if dim_id not in seen:
                all_dimensions.append(dim_id)
                seen.add(dim_id)

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
