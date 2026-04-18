# ABOUTME: Skill references/theory.md 与 docs/experiential-interventions 真相源一致性校验
# ABOUTME: 防止 backend/skills/ 下的复制品与 docs/experiential-interventions/ 静默 drift

import hashlib
from pathlib import Path

import pytest

from voliti.store_contract import COACH_SKILLS_ROOT

_REPO_ROOT = COACH_SKILLS_ROOT.parent.parent.parent
_DOCS_SOURCE_DIR = _REPO_ROOT / "docs" / "experiential-interventions"

_SKILL_TO_SOURCE: dict[str, str] = {
    "future-self-dialogue": "01_future_self_dialogue.md",
    "scenario-rehearsal": "02_scenario_rehearsal.md",
    "metaphor-collaboration": "03_metaphor_collaboration.md",
    "cognitive-reframing": "04_cognitive_reframing.md",
}


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("skill_name", "source_filename"),
    list(_SKILL_TO_SOURCE.items()),
)
def test_theory_md_matches_truth_source(skill_name: str, source_filename: str) -> None:
    """backend/skills/coach/<name>/references/theory.md 必须与真相源逐字节一致。

    docs/experiential-interventions/0X_*.md 为学术分册真相源；
    backend/skills/coach/<name>/references/theory.md 是其物理复制，供 Coach
    的只读 FilesystemBackend 挂载。本测试在 CI 中捕获真相源更新未同步到
    backend 复制品的情况。
    """
    source = _DOCS_SOURCE_DIR / source_filename
    destination = COACH_SKILLS_ROOT / skill_name / "references" / "theory.md"

    assert source.exists(), f"Truth source missing: {source}"
    assert destination.exists(), f"Backend copy missing: {destination}"

    source_hash = _hash_file(source)
    dest_hash = _hash_file(destination)
    assert source_hash == dest_hash, (
        f"theory.md out of sync for skill '{skill_name}'.\n"
        f"  source:      {source}\n"
        f"  destination: {destination}\n"
        f"Re-copy the source to the destination to resolve."
    )


def test_all_four_skills_have_skill_md() -> None:
    """四份 skill 目录必须都有 SKILL.md（中间件依赖此文件加载元数据）。"""
    for skill_name in _SKILL_TO_SOURCE:
        skill_md = COACH_SKILLS_ROOT / skill_name / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md missing for skill '{skill_name}': {skill_md}"


def test_scenario_rehearsal_has_dialogue_examples() -> None:
    """仅 scenario-rehearsal 有学术对话样本来源，此文件必须存在。"""
    dialogue_path = (
        COACH_SKILLS_ROOT / "scenario-rehearsal" / "references" / "dialogue-examples.md"
    )
    assert dialogue_path.exists(), f"dialogue-examples.md missing: {dialogue_path}"


def test_other_skills_do_not_have_dialogue_examples() -> None:
    """其余三手法研究中未找到可引用的学术对话样本，不应有 dialogue-examples.md。"""
    for skill_name in ("future-self-dialogue", "metaphor-collaboration", "cognitive-reframing"):
        dialogue_path = (
            COACH_SKILLS_ROOT / skill_name / "references" / "dialogue-examples.md"
        )
        assert not dialogue_path.exists(), (
            f"Unexpected dialogue-examples.md present for skill '{skill_name}'. "
            f"Research found no citable academic sample — this file should not exist."
        )
