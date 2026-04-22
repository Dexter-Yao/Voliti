# ABOUTME: 配置加载模块
# ABOUTME: 从 TOML/YAML 文件和环境变量加载评估运行配置

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_EVAL_ROOT = Path(__file__).resolve().parent.parent.parent  # eval/


@dataclass
class ModelConfig:
    """单个 LLM 角色的配置。"""

    provider: str
    deployment: str
    temperature: float = 1.0
    reasoning_effort: str = "high"


@dataclass
class EvalConfig:
    """评估运行的完整配置。"""

    root: Path = field(default_factory=lambda: _EVAL_ROOT)
    server_url: str = "http://localhost:2025"
    assistant_id: str = "coach"
    max_turns_default: int = 20
    turn_timeout_seconds: int = 300
    seed_directory: Path = field(default_factory=lambda: _EVAL_ROOT / "seeds")
    seed_directory_smoke: Path = field(default_factory=lambda: _EVAL_ROOT / "seeds_smoke")
    output_directory: Path = field(default_factory=lambda: _EVAL_ROOT / "output")
    auditor_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(provider="azure_openai", deployment="gpt-5.4")
    )
    judge_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            provider="azure_openai", deployment="gpt-5.4", temperature=0.3
        )
    )
    model_labels: dict[str, str] = field(default_factory=dict)
    seed_directory_lite: Path = field(default_factory=lambda: _EVAL_ROOT / "seeds_lite")
    profile_manifest_path: Path = field(default_factory=lambda: _EVAL_ROOT / "config" / "profiles.yaml")
    max_concurrency: int = 10


@dataclass(frozen=True)
class ProfileDefinition:
    """单个 profile 的显式定义。"""

    name: str
    description: str
    seed_files: list[Path]


def load_config(
    eval_root: Path | None = None,
    *,
    server_url: str | None = None,
    assistant_id: str | None = None,
    max_turns: int | None = None,
    max_concurrency: int | None = None,
    output_dir: Path | None = None,
) -> EvalConfig:
    """从配置文件加载并合并 CLI 覆盖参数。

    优先级：CLI 参数 > defaults.yaml > 硬编码默认值。
    """
    root = eval_root or _EVAL_ROOT

    # 加载 .env
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # 加载 defaults.yaml
    defaults_path = root / "config" / "defaults.yaml"
    defaults: dict[str, Any] = {}
    if defaults_path.exists():
        with open(defaults_path) as f:
            defaults = yaml.safe_load(f) or {}

    # 加载 models.toml
    models_path = root / "config" / "models.toml"
    models: dict[str, Any] = {}
    if models_path.exists():
        with open(models_path, "rb") as f:
            models = tomllib.load(f)

    # 构建 ModelConfig
    auditor_cfg = models.get("auditor", {})
    judge_cfg = models.get("judge", {})

    config = EvalConfig(
        root=root,
        server_url=server_url or defaults.get("server_url", "http://localhost:2025"),
        assistant_id=assistant_id or defaults.get("assistant_id", "coach"),
        max_turns_default=max_turns or defaults.get("max_turns_default", 20),
        turn_timeout_seconds=defaults.get("turn_timeout_seconds", 300),
        seed_directory=root / defaults.get("seed_directory", "seeds/"),
        seed_directory_smoke=root / defaults.get("seed_directory_smoke", "seeds_smoke/"),
        output_directory=output_dir or root / defaults.get("output_directory", "output/"),
        model_labels=defaults.get("model_labels", {}),
        seed_directory_lite=root / defaults.get("seed_directory_lite", "seeds_lite/"),
        profile_manifest_path=root / defaults.get("profile_manifest", "config/profiles.yaml"),
        max_concurrency=max_concurrency or defaults.get("max_concurrency", 10),
        auditor_model=ModelConfig(
            provider=auditor_cfg.get("provider", "azure_openai"),
            deployment=auditor_cfg.get("deployment", "gpt-5.4"),
            temperature=auditor_cfg.get("temperature", 1.0),
            reasoning_effort=auditor_cfg.get("reasoning_effort", "high"),
        ),
        judge_model=ModelConfig(
            provider=judge_cfg.get("provider", "azure_openai"),
            deployment=judge_cfg.get("deployment", "gpt-5.4"),
            temperature=judge_cfg.get("temperature", 0.3),
            reasoning_effort=judge_cfg.get("reasoning_effort", "high"),
        ),
    )

    return config


def load_profile_manifest(config: EvalConfig) -> dict[str, ProfileDefinition]:
    """加载 smoke/lite/full profile 显式定义。"""
    manifest_path = config.profile_manifest_path
    if not manifest_path.exists():
        raise ValueError(f"Profile manifest not found: {manifest_path}")

    with open(manifest_path) as f:
        raw = yaml.safe_load(f) or {}

    profiles_raw = raw.get("profiles")
    if not isinstance(profiles_raw, dict) or not profiles_raw:
        raise ValueError("Profile manifest must define a non-empty 'profiles' mapping")

    profiles: dict[str, ProfileDefinition] = {}
    for name, payload in profiles_raw.items():
        if not isinstance(payload, dict):
            raise ValueError(f"Profile '{name}' must be a mapping")
        description = payload.get("description", "")
        seed_files_raw = payload.get("seed_files", [])
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Profile '{name}' must define a non-empty description")
        if not isinstance(seed_files_raw, list) or not seed_files_raw:
            raise ValueError(f"Profile '{name}' must define a non-empty seed_files list")

        seed_files: list[Path] = []
        seen_files: set[Path] = set()
        for relative_path in seed_files_raw:
            if not isinstance(relative_path, str) or not relative_path.strip():
                raise ValueError(f"Profile '{name}' contains an invalid seed path")
            resolved = (config.root / relative_path).resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            seed_files.append(resolved)
        profiles[name] = ProfileDefinition(
            name=name,
            description=description.strip(),
            seed_files=seed_files,
        )
    return profiles


def load_seed(path: Path) -> Any:
    """加载单个 seed YAML 文件。"""
    from voliti_eval.models import Seed

    with open(path) as f:
        data = yaml.safe_load(f)
    return Seed.model_validate(data)


def load_seeds(seed_dir: Path) -> list[Any]:
    """加载并解析 seed 目录下的所有 YAML 文件。

    返回按文件名排序的 Seed 对象列表。
    """
    seeds: list[Any] = []
    yaml_files = sorted(seed_dir.glob("*.yaml"))

    for path in yaml_files:
        seeds.append(load_seed(path))

    return seeds
