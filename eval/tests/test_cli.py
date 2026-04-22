# ABOUTME: CLI profile 装载测试
# ABOUTME: 固定 smoke/lite/full manifest 是 profile 语义的唯一真相源

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from voliti_eval.cli import filter_seeds, load_profile_seeds
from voliti_eval.config import EvalConfig, ProfileDefinition, load_seeds


def test_load_profile_seeds_uses_manifest_membership() -> None:
    config = EvalConfig(
        root=Path("/tmp/eval"),
        seed_directory=Path("/tmp/full"),
        seed_directory_lite=Path("/tmp/lite"),
        profile_manifest_path=Path("/tmp/eval/config/profiles.yaml"),
    )
    profile_manifest = {
        "profiles": {
            "smoke": {
                "description": "链路 smoke",
                "seed_files": [
                    "seeds_smoke/S01_text_roundtrip_sanity.yaml",
                    "seeds_smoke/S02_a2ui_store_roundtrip_sanity.yaml",
                ],
            },
            "lite": {
                "description": "主线核心行为",
                "seed_files": [
                    "seeds_lite/L01_onboarding.yaml",
                    "seeds_lite/L10_chapter_plan_request.yaml",
                ],
            },
            "full": {
                "description": "全面回归",
                "seed_files": [
                    "seeds_lite/L01_onboarding.yaml",
                    "seeds_lite/L10_chapter_plan_request.yaml",
                    "seeds/11_metrics_governance.yaml",
                    "seeds/16_implicit_achievement_discovery.yaml",
                ],
            },
        }
    }

    seeds = load_profile_seeds(
        config,
        "full",
        seed_loader=lambda path: {"id": path.stem},
        manifest_loader=lambda _: {
            name: ProfileDefinition(
                name=name,
                description=payload["description"],
                seed_files=[config.root / relative_path for relative_path in payload["seed_files"]],
            )
            for name, payload in profile_manifest["profiles"].items()
        },
    )

    assert [seed["id"] for seed in seeds] == [
        "L01_onboarding",
        "L10_chapter_plan_request",
        "11_metrics_governance",
        "16_implicit_achievement_discovery",
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


def test_load_seeds_rejects_unknown_pre_state_keys(tmp_path: Path) -> None:
    seed_path = tmp_path / "bad_pre_state.yaml"
    seed_path.write_text(
        """
id: "14_chapter_transition_and_identity_review"
name: "Bad pre_state"
description: "Unknown pre_state keys should fail fast"
entry_mode: "coaching"
persona:
  name: "志远"
  background: "transition"
  personality: "直接"
  language: "zh"
goal: "Check schema"
initial_message: "我想切到下一个阶段。"
user_outcome: "用户的阶段变化被看见。"
allowed_good_variants:
  - "Coach 可以先确认阶段变化。"
manual_review_checks:
  - "人工检查语气是否自然。"
pre_state:
  goal:
    id: "goal_001"
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
  - "coach_action_transparency"
scoring_focus:
  primary:
    - "coach_action_transparency"
  secondary: []
""".strip(),
        encoding="utf-8",
    )

    try:
        load_seeds(tmp_path)
    except ValueError as exc:
        assert "Extra inputs are not permitted" in str(exc)
    else:
        raise AssertionError("load_seeds should reject unknown pre_state keys")


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
        manifest_path = tmp_path / "profiles.yaml"
        manifest_path.write_text(
            yaml.safe_dump(
                {
                    "profiles": {
                        "full": {
                            "description": "全面回归",
                            "seed_files": ["seeds/bad.yaml"],
                        },
                        "lite": {
                            "description": "主线核心行为",
                            "seed_files": ["seeds/bad.yaml"],
                        },
                        "smoke": {
                            "description": "超轻链路",
                            "seed_files": ["seeds/bad.yaml"],
                        },
                    }
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return EvalConfig(
            root=tmp_path,
            seed_directory=seed_dir,
            seed_directory_lite=seed_dir,
            profile_manifest_path=manifest_path,
            output_directory=tmp_path / "output",
        )

    monkeypatch.setattr("voliti_eval.cli.load_config", _fake_load_config)

    result = runner.invoke(
        __import__("voliti_eval.cli", fromlist=["main"]).main,
        ["--dry-run", "--profile", "full"],
    )

    assert result.exit_code != 0
    assert "Unknown eval dimensions" in result.output


def test_cli_supports_smoke_profile_via_manifest(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    eval_root = tmp_path / "eval"
    smoke_dir = eval_root / "seeds_smoke"
    lite_dir = eval_root / "seeds_lite"
    full_dir = eval_root / "seeds"
    config_dir = eval_root / "config"
    smoke_dir.mkdir(parents=True)
    lite_dir.mkdir()
    full_dir.mkdir()
    config_dir.mkdir()

    smoke_seed = """
id: "S01_text_roundtrip_sanity"
name: "Text Roundtrip Sanity"
description: "Smoke seed"
entry_mode: "coaching"
persona:
  name: "烟岚"
  background: "smoke"
  personality: "直接"
  language: "zh"
goal: "Check text path"
initial_message: "先帮我看一下我现在是什么状态。"
user_outcome: "用户感到状态先被接住。"
allowed_good_variants:
  - "Coach 可以先镜像状态。"
manual_review_checks:
  - "人工检查语气是否自然。"
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
    - "coach_state_before_strategy"
  secondary: []
""".strip()
    (smoke_dir / "S01_text_roundtrip_sanity.yaml").write_text(smoke_seed, encoding="utf-8")
    (smoke_dir / "S02_a2ui_store_roundtrip_sanity.yaml").write_text(
        smoke_seed.replace("S01_text_roundtrip_sanity", "S02_a2ui_store_roundtrip_sanity"),
        encoding="utf-8",
    )
    (lite_dir / "L01_onboarding.yaml").write_text(smoke_seed.replace("S01_text_roundtrip_sanity", "L01_seed"), encoding="utf-8")
    (full_dir / "11_metrics_governance.yaml").write_text(smoke_seed.replace("S01_text_roundtrip_sanity", "11_seed"), encoding="utf-8")
    (config_dir / "profiles.yaml").write_text(
        yaml.safe_dump(
            {
                "profiles": {
                    "smoke": {
                        "description": "超轻链路",
                        "seed_files": [
                            "seeds_smoke/S01_text_roundtrip_sanity.yaml",
                            "seeds_smoke/S02_a2ui_store_roundtrip_sanity.yaml",
                        ],
                    },
                    "lite": {
                        "description": "主线核心行为",
                        "seed_files": ["seeds_lite/L01_onboarding.yaml"],
                    },
                    "full": {
                        "description": "全面回归",
                        "seed_files": [
                            "seeds_lite/L01_onboarding.yaml",
                            "seeds/11_metrics_governance.yaml",
                        ],
                    },
                }
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    def _fake_load_config(*args, **kwargs):
        return EvalConfig(
            root=eval_root,
            seed_directory=full_dir,
            seed_directory_lite=lite_dir,
            profile_manifest_path=config_dir / "profiles.yaml",
            output_directory=eval_root / "output",
        )

    monkeypatch.setattr("voliti_eval.cli.load_config", _fake_load_config)

    result = runner.invoke(
        __import__("voliti_eval.cli", fromlist=["main"]).main,
        ["--dry-run", "--profile", "smoke"],
    )

    assert result.exit_code == 0
    assert "Profile: smoke" in result.output
    assert "Seeds: 2/2 selected" in result.output
    assert "S01_text_roundtrip_sanity" in result.output
    assert "S02_a2ui_store_roundtrip_sanity" in result.output


def test_cli_forwards_concurrency_override_and_prints_it(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    observed: dict[str, object] = {}

    def _fake_load_config(*args, **kwargs):
        observed["max_concurrency"] = kwargs.get("max_concurrency")
        observed["server_url"] = kwargs.get("server_url")
        manifest_path = tmp_path / "profiles.yaml"
        manifest_path.write_text(
            yaml.safe_dump(
                {
                    "profiles": {
                        "smoke": {
                            "description": "超轻链路",
                            "seed_files": ["seeds/S01_text_roundtrip_sanity.yaml"],
                        },
                        "lite": {
                            "description": "主线核心行为",
                            "seed_files": ["seeds/S01_text_roundtrip_sanity.yaml"],
                        },
                        "full": {
                            "description": "全面回归",
                            "seed_files": ["seeds/S01_text_roundtrip_sanity.yaml"],
                        },
                    }
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        seed_dir = tmp_path / "seeds"
        seed_dir.mkdir(exist_ok=True)
        (seed_dir / "S01_text_roundtrip_sanity.yaml").write_text(
            """
id: "S01_text_roundtrip_sanity"
name: "Text Roundtrip Sanity"
description: "Smoke seed"
entry_mode: "coaching"
persona:
  name: "烟岚"
  background: "smoke"
  personality: "直接"
  language: "zh"
goal: "Check text path"
initial_message: "先帮我看一下我现在是什么状态。"
user_outcome: "用户感到状态先被接住。"
allowed_good_variants:
  - "Coach 可以先镜像状态。"
manual_review_checks:
  - "人工检查语气是否自然。"
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
    - "coach_state_before_strategy"
  secondary: []
""".strip(),
            encoding="utf-8",
        )
        return EvalConfig(
            root=tmp_path,
            seed_directory=seed_dir,
            seed_directory_lite=seed_dir,
            profile_manifest_path=manifest_path,
            output_directory=tmp_path / "output",
            max_concurrency=kwargs["max_concurrency"],
            server_url=kwargs["server_url"],
        )

    monkeypatch.setattr("voliti_eval.cli.load_config", _fake_load_config)

    result = runner.invoke(
        __import__("voliti_eval.cli", fromlist=["main"]).main,
        [
            "--dry-run",
            "--profile",
            "smoke",
            "--server-url",
            "http://localhost:2121",
            "--concurrency",
            "7",
        ],
    )

    assert result.exit_code == 0
    assert observed["max_concurrency"] == 7
    assert observed["server_url"] == "http://localhost:2121"
    assert "Concurrency: 7" in result.output


def test_smoke_a2ui_seed_keeps_pressing_until_onboarding_completion() -> None:
    eval_root = Path(__file__).resolve().parents[1]
    seed_path = eval_root / "seeds_smoke" / "S02_a2ui_store_roundtrip_sanity.yaml"

    payload = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
    stop_rules = payload["auditor_policy"]["stop_rules"]

    assert "onboarding_complete_written" in stop_rules["complete_when"]
    assert "onboarding_complete_written" in stop_rules["continue_until"]


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
        (tmp_path / "profiles.yaml").write_text(
            yaml.safe_dump(
                {
                    "profiles": {
                        "full": {
                            "description": "全面回归",
                            "seed_files": ["seeds/ok.yaml"],
                        },
                        "lite": {
                            "description": "主线核心行为",
                            "seed_files": ["seeds/ok.yaml"],
                        },
                        "smoke": {
                            "description": "超轻链路",
                            "seed_files": ["seeds/ok.yaml"],
                        },
                    }
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return EvalConfig(
            root=tmp_path,
            seed_directory=seed_dir,
            seed_directory_lite=seed_dir,
            profile_manifest_path=tmp_path / "profiles.yaml",
            output_directory=tmp_path / "output",
        )

    async def _fake_run(seeds, config, *, profile, runs, profile_snapshot):
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
