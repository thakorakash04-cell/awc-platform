"""
Human-in-the-Loop (HITL) Controller
Manages visual feature suggestions and enforces human clinical sign-off.
"""

from typing import Dict, Any
from core.models import ExudateLevel, WoundDepthType


def map_visual_features_to_clinical_form(percentages: Dict[str, int]) -> Dict[str, Any]:
    """Suggests baseline clinical parameters from image heuristics for human review."""
    red = percentages.get("granulation_red", 100)
    yellow = percentages.get("slough_yellow", 0)
    black = percentages.get("eschar_black", 0)

    # Heuristic moisture estimate (yellow/slough wounds typically exude more)
    if yellow > 30:
        suggested_exudate = ExudateLevel.HEAVY
    elif red > 70:
        suggested_exudate = ExudateLevel.MODERATE
    elif black > 50:
        suggested_exudate = ExudateLevel.NONE_SCANT
    else:
        suggested_exudate = ExudateLevel.MINIMAL

    return {
        "granulation_percent": red,
        "slough_percent": yellow,
        "eschar_percent": black,
        "suggested_exudate": suggested_exudate,
    }
