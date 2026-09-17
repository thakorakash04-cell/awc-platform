"""
Assistive RYB (Red-Yellow-Black) Tissue Segmentation Engine
Extracts visual tissue breakdown (Granulation, Slough, Eschar) with visual mask overlay.
"""

import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple


def segment_wound_tissue(image: Image.Image) -> Tuple[Dict[str, int], Image.Image]:
    """
    Performs color-space tissue segmentation into RYB categories:
    - Red: Vascular granulation tissue
    - Yellow: Fibrinous slough
    - Black: Necrotic eschar
    - Pink/White: Epithelial edge / calloused margin
    Returns (percentage_dict, overlay_pil_image).
    """
    img_rgb = image.convert("RGB")
    arr = np.array(img_rgb)
    h, w, _ = arr.shape

    # Focus on central ROI (assume wound occupies center 70% of frame)
    margin_y, margin_x = int(h * 0.15), int(w * 0.15)
    roi = arr[margin_y : h - margin_y, margin_x : w - margin_x]

    r, g, b = roi[:, :, 0].astype(float), roi[:, :, 1].astype(float), roi[:, :, 2].astype(float)

    # Color space heuristics:
    # Red Granulation: High R, lower G and B, R - G > 25
    red_mask = (r > 110) & (r > g + 20) & (r > b + 20)

    # Yellow Slough: High R and G (yellow/tan), low B
    yellow_mask = (r > 130) & (g > 110) & (b < 120) & ~red_mask

    # Black Eschar: Very low intensity across all channels
    black_mask = (r < 65) & (g < 65) & (b < 65)

    # Remaining tissue is epithelial / periwound
    total_wound_pixels = np.sum(red_mask | yellow_mask | black_mask)
    if total_wound_pixels == 0:
        total_wound_pixels = 1  # prevent div by zero

    red_pct = int(round((np.sum(red_mask) / total_wound_pixels) * 100))
    yellow_pct = int(round((np.sum(yellow_mask) / total_wound_pixels) * 100))
    black_pct = int(round((np.sum(black_mask) / total_wound_pixels) * 100))

    # Normalize to 100%
    rem = 100 - (red_pct + yellow_pct + black_pct)
    if rem > 0:
        red_pct += rem
    elif rem < 0:
        red_pct = max(0, red_pct + rem)

    percentages = {
        "granulation_red": red_pct,
        "slough_yellow": yellow_pct,
        "eschar_black": black_pct,
    }

    # Generate Visual Mask Overlay
    overlay = arr.copy()
    roi_overlay = overlay[margin_y : h - margin_y, margin_x : w - margin_x]

    # Blend colors: Red = [255, 0, 0], Yellow = [255, 255, 0], Black = [50, 50, 50]
    alpha = 0.4
    roi_overlay[red_mask] = (roi_overlay[red_mask] * (1 - alpha) + np.array([220, 20, 60]) * alpha).astype(np.uint8)
    roi_overlay[yellow_mask] = (roi_overlay[yellow_overlay := yellow_mask] * (1 - alpha) + np.array([255, 215, 0]) * alpha).astype(np.uint8)
    roi_overlay[black_mask] = (roi_overlay[black_mask] * (1 - alpha) + np.array([20, 20, 20]) * alpha).astype(np.uint8)

    overlay[margin_y : h - margin_y, margin_x : w - margin_x] = roi_overlay
    overlay_img = Image.fromarray(overlay)

    return percentages, overlay_img
