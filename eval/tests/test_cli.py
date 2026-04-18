# ABOUTME: CLI profile 装载测试
# ABOUTME: 固定 full profile 必须包含 lite 10 个场景与全部扩展场景

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from voliti_eval.cli import filter_seeds, load_profile_seeds
from voliti_eval.config import EvalConfig, load_seeds


def test_load_profile_seeds_full_includes_lite_and_extensions() -> None:
    config = EvalConfig(
        seed_directory=Path("/tmp/full"),
        seed_directory_lite=Path("/tmp/lite"),
    )

    seeds = load_profile_seeds(
        config,
        "full",
        seed_loader=lambda directory: (
            [
                {"id": "L01_onboarding_quick_minimum_dataset"},
                {"id": "L10_grounded_daily_guidance"},
            ]
            if directory == config.seed_directory_lite
            else [
                {"id": "11_onboarding_reentry_gap_fill"},
                {"id": "16_a2ui_reject_skip_resilience"},
            ]
        ),
    )

    assert [seed["id"] for seed in seeds] == [
        "L01_onboarding_quick_minimum_dataset",
        "L10_grounded_daily_guidance",
        "11_onboarding_reentry_gap_fill",
        "16_a2ui_reject_skip_resilience",
    ]


def test_filter_seeds_supports_full_ids_and_prefixes() -> None:
    seeds = [
        {"id": "L01_onboarding_quick_minimum_dataset"},
        {"id": "14_chapter_transition_and_identity_review"},
    ]

    selected = filter_seeds(seeds, "L01,14")

    assert [seed["id"] for seed in selected] == [
        "L01_onboarding_quick_minimum_dataset",
        "14_chapter_transition_and_identity_review",
    ]


def test_load_seeds_rejects_unknown_dimensions(tmp_path: Path) -> None:
    seed_path = tmp_path / "17_future_self_dialogue_trigger.yaml"
    seed_path.write_text(
        """
id: "17_future_self_dialogue_trigger"
name: "Future Self Dialogue Trigger"
description: "Invalid dimension seed"
entry_mode: "coaching"
persona:
  name: "砚舟"
  background: "identity drift"
  personality: "克制"
  language: "zh"
goal: "Trigger intervention"
initial_message: "我不知道想成为什么样的人了。"
user_outcome: "用户感到困惑被接住，并被引入一次合适的未来自我对话。"
allowed_good_variants:
  - "可以先简短确认状态，再进入未来自我问句。"
manual_review_checks:
  - "人工检查干预是否显得过于模板化。"
auditor_policy:
  latent_facts: []
  reveal_rules: []
  a2ui_plan: []
  challenge_rules: []
  stop_rules:
    min_user_turns: 3
    complete_when: ["done"]
    continue_until: ["done"]
judge_dimensions:
  - "unknown_dimension"
scoring_focus:
  primary:
    - "contract_store_schema"
  secondary: []
""".strip(),
        encoding="utf-8",
    )

    try:
        load_seeds(tmp_path)
    except ValueError as exc:
        assert "Unknown eval dimensions" in str(exc)
    else:
        raise AssertionError("load_seeds should reject unknown dimensions")


def test_cli_dry_run_surfaces_seed_validation_failure(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    (seed_dir / "bad.yaml").write_text(
        """
id: "18_scenario_rehearsal_trigger"
name: "Scenario Rehearsal Trigger"
description: "Invalid dimension seed"
entry_mode: "coaching"
persona:
  name: "林迟"
  background: "家庭聚餐"
  personality: "愿意配合"
  language: "zh"
goal: "Trigger intervention"
initial_message: "想提前准备一下。"
user_outcome: "用户感到自己正在被帮助着为一个具体场景做准备。"
allowed_good_variants:
  - "可以先确认具体风险点，再进入预演。"
manual_review_checks:
  - "人工检查文案是否显得太模板化。"
auditor_policy:
  latent_facts: []
  reveal_rules: []
  a2ui_plan: []
  challenge_rules: []
  stop_rules:
    min_user_turns: 3
    complete_when: ["done"]
    continue_until: ["done"]
judge_dimensions:
  - "unknown_dimension"
scoring_focus:
  primary: []
  secondary: []
""".strip(),
        encoding="utf-8",
    )

    def _fake_load_config(*args, **kwargs):
        return EvalConfig(
            seed_directory=seed_dir,
            seed_directory_lite=seed_dir,
            output_directory=tmp_path / "output",
        )

    monkeypatch.setattr("voliti_eval.cli.load_config", _fake_load_config)

    result = runner.invoke(
        __import__("voliti_eval.cli", fromlist=["main"]).main,
        ["--dry-run", "--profile", "full"],
    )

    assert result.exit_code != 0
    assert "Unknown eval dimensions" in result.output


def test_cli_forwards_runs_to_single_model_mode(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    captured: dict[str, int] = {}
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    (seed_dir / "ok.yaml").write_text(
        """
id: "17_future_self_dialogue_trigger"
name: "Future self"
description: "Valid seed"
entry_mode: "coaching"
persona:
  name: "砚舟"
  background: "identity drift"
  personality: "克制"
  language: "zh"
goal: "Trigger intervention"
initial_message: "我不知道想成为什么样的人了。"
user_outcome: "用户感到困惑被接住，并被引入一次合适的未来自我对话。"
allowed_good_variants:
  - "可以先简短确认状态，再进入未来自我问句。"
manual_review_checks:
  - "人工检查干预是否显得过于模板化。"
auditor_policy:
  latent_facts: []
  reveal_rules: []
  a2ui_plan: []
  challenge_rules: []
  stop_rules:
    min_user_turns: 3
    complete_when: ["done"]
    continue_until: ["done"]
judge_dimensions:
  - "coach_state_before_strategy"
scoring_focus:
  primary:
    - "intervention_kind_selection"
    - "coach_state_before_strategy"
  secondary: []
""".strip(),
        encoding="utf-8",
    )

    def _fake_load_config(*args, **kwargs):
        return EvalConfig(
            seed_directory=seed_dir,
            seed_directory_lite=seed_dir,
            output_directory=tmp_path / "output",
        )

    async def _fake_run(seeds, config, *, profile, runs):
        captured["runs"] = runs

    monkeypatch.setattr("voliti_eval.cli.load_config", _fake_load_config)
    monkeypatch.setattr("voliti_eval.cli._run", _fake_run)

    result = runner.invoke(
        __import__("voliti_eval.cli", fromlist=["main"]).main,
        ["--profile", "full", "--runs", "3"],
    )

    assert result.exit_code == 0
    assert captured["runs"] == 3


def test_cli_rejects_runs_less_than_one() -> None:
    runner = CliRunner()

    result = runner.invoke(
        __import__("voliti_eval.cli", fromlist=["main"]).main,
        ["--runs", "0"],
    )

    assert result.exit_code != 0
    assert "x>=1" in result.output or "1 <= x" in result.output
