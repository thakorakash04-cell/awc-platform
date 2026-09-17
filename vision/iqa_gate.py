"""
Image Quality Assessment (IQA) Pre-flight Gate
Validates focus blur, specular glare, and illumination before feature extraction.
"""

import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple


def evaluate_image_quality(image: Image.Image) -> Dict[str, Any]:
    """Evaluates smartphone wound photo quality to prevent AI misclassification."""
    img_np = np.array(image.convert("RGB"))
    h, w, _ = img_np.shape

    # 1. Resolution Check
    min_res_ok = h >= 300 and w >= 300

    # 2. Exposure & Luminance
    gray = np.mean(img_np, axis=2)
    mean_lum = np.mean(gray)
    is_underexposed = mean_lum < 40
    is_overexposed = mean_lum > 220

    # 3. Specular Glare Detection (Saturated pixels > 245 across R, G, B)
    glare_mask = (img_np[:, :, 0] > 245) & (img_np[:, :, 1] > 245) & (img_np[:, :, 2] > 245)
    glare_ratio = np.sum(glare_mask) / (h * w)
    has_excessive_glare = glare_ratio > 0.08  # Over 8% specular glare

    # 4. Blur / Sharpness Check (Laplacian Variance approximation)
    # Fast 2D discrete Laplacian filter
    laplacian_kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
    # Compute center gradient
    gy, gx = np.gradient(gray)
    sharpness_score = float(np.var(gx) + np.var(gy))
    is_blurry = sharpness_score < 40.0

    passed_all = min_res_ok and not is_underexposed and not is_overexposed and not has_excessive_glare and not is_blurry

    rejection_reasons = []
    if not min_res_ok:
        rejection_reasons.append("Image resolution is too low. Please move closer.")
    if is_underexposed:
        rejection_reasons.append("Photo is underexposed / too dark. Please use natural diffused light.")
    if is_overexposed or has_excessive_glare:
        rejection_reasons.append("Excessive flash glare detected. Please turn off direct flash and avoid reflections on moist tissue.")
    if is_blurry:
        rejection_reasons.append("Photo is out of focus / blurry. Please hold camera steady.")

    return {
        "passed": passed_all,
        "sharpness_score": sharpness_score,
        "mean_luminance": mean_lum,
        "glare_ratio_pct": glare_ratio * 100.0,
        "rejection_reasons": rejection_reasons,
        "guidance": (
            "Capture photo perpendicular to the wound in natural light. "
            "Avoid direct flashlight glare on moist surfaces."
            if not passed_all
            else "Image quality passed clinical gate."
        ),
    }
