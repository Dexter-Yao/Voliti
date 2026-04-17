# ABOUTME: CLI profile 装载测试
# ABOUTME: 固定 full profile 必须包含 lite 10 个场景与扩展 6 个场景

from __future__ import annotations

from pathlib import Path

from voliti_eval.cli import filter_seeds, load_profile_seeds
from voliti_eval.config import EvalConfig


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
