# ABOUTME: Witness Card 图片 prompt 组装脚本
# ABOUTME: 复用统一视觉体系与见证定位，将结构化字段收束为最终图片 prompt

from __future__ import annotations

from typing import Literal


EmotionalTone = Literal["growth", "warmth", "strength", "breakthrough"]

_WARM_STYLE = (
    "Warm parchment background (#F5F1EB, like aged cream paper) with subtle "
    "handmade paper texture. Deep obsidian black (#1A1A1A) as primary contrast "
    "element. Organic brushwork, watercolor accents. Feels like a hand-written "
    "letter: personal, warm, unhurried."
)

_COOL_STYLE = (
    "Warm dark background (#2A2520, like aged dark paper) with subtle aged paper "
    "texture. Low-saturation cool blue (#8AACB8, muted teal) with soft halos. "
    "Eastern ink painting meets star atlas aesthetic. Feels precise, steady, "
    "objective, and quietly strong."
)

_TECHNICAL = (
    "Medium format film aesthetic with subtle organic grain. Natural side "
    "lighting, soft and diffused. Non-photorealistic rendering. Illustration "
    "and painting style throughout. Generous negative space, at least 40 percent "
    "of the frame left as breathable paper space."
)

_NEGATIVE = (
    "This image must not contain: photorealistic rendering, text overlays, "
    "typography, words or letters, colorful or vibrant palettes, busy "
    "compositions, motivational graphics, medical blue, bright green/yellow/"
    "orange, gamification elements (badges, stars, explosions), fitness "
    "influencer photography, stock photo people, cartoon or emoji style, high "
    "saturation, 3D effects, realistic human faces. Keep the palette desaturated "
    "and muted."
)


def _style_for_tone(emotional_tone: EmotionalTone) -> str:
    if emotional_tone in {"strength", "breakthrough"}:
        return _COOL_STYLE
    return _WARM_STYLE


def build_witness_card_prompt(
    *,
    achievement_title: str,
    emotional_tone: EmotionalTone,
    evidence_summary: str,
    scene_anchors: list[str],
    user_quote: str = "",
) -> str:
    """根据结构化字段生成最终图片 prompt。"""
    scene_anchor_text = ", ".join(scene_anchors)
    quote_text = (
        f'User language to honor in the atmosphere: "{user_quote}".'
        if user_quote
        else "No direct user quote is required in the image."
    )
    return "\n\n".join(
        [
            (
                f"[SCENE]\nCreate a Witness Card scene for this achieved milestone: "
                f"{achievement_title}. The scene must depict a quiet, specific, "
                f"already-earned moment anchored in these details: {scene_anchor_text}. "
                f"Evidence of the achievement: {evidence_summary}. Favor behavioral "
                f"traces, objects, timing, and atmosphere over explicit action shots. "
                f"Avoid faces; silhouettes, hands, backs, thresholds, and environmental "
                f"details are preferred. {quote_text}"
            ),
            f"[STYLE]\n{_style_for_tone(emotional_tone)}",
            f"[TECHNICAL]\n{_TECHNICAL}",
            f"[NEGATIVE]\n{_NEGATIVE}",
        ]
    )
