# ABOUTME: Transcript 序列化与持久化
# ABOUTME: 将 Transcript 模型保存为 JSON 文件并从 JSON 加载

from __future__ import annotations

import json
from pathlib import Path

from voliti_eval.models import Transcript


def save_transcript(transcript: Transcript, output_dir: Path) -> Path:
    """将 Transcript 保存为 JSON 文件。

    文件名格式：{seed_id}.json
    Returns: 写入的文件路径。
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{transcript.seed_id}.json"
    data = transcript.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_transcript(path: Path) -> Transcript:
    """从 JSON 文件加载 Transcript。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Transcript.model_validate(data)
