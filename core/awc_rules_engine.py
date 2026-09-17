"""
AWC Clinical Rules Engine (Powered by User's AWCare Dataset)
Provides deterministic product filtering, safety contraindication checks, and clinical protocol generation.
"""

from typing import List, Dict, Any, Optional
from data.awc_data_manager import get_awc_data_manager


def evaluate_awc_query(
    wound_type: Optional[str] = "All",
    indication: Optional[str] = "All",
    exudate_level: Optional[str] = "All",
    application: Optional[str] = "All",
    dressing_type: Optional[str] = "All",
    healing_phase: Optional[str] = "All",
    has_emergency_flags: bool = False,
    emergency_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates clinical parameters against the user's AWC dataset.
    Returns matched primary, secondary, and alternative products, along with contraindications.
    """
    dm = get_awc_data_manager()

    # 1. Emergency Safety Check
    if has_emergency_flags:
        return {
            "is_emergency": True,
            "emergency_reason": emergency_reason or "Emergency clinical red-flag detected.",
            "primary_matches": [],
            "secondary_matches": [],
            "all_matches": [],
            "contraindication_alerts": [],
            "total_count": 0,
        }

    # 2. Query exact matching products
    matches = dm.filter_products(
        wound_type=wound_type if wound_type != "All" else None,
        indication=indication if indication != "All" else None,
        exudate=exudate_level if exudate_level != "All" else None,
        application=application if application != "All" else None,
        dressing_type=dressing_type if dressing_type != "All" else None,
        healing_phase=healing_phase if healing_phase != "All" else None,
    )

    # If no strict match, fallback gracefully with partial matching (e.g. relax dressing_type or application)
    fallback_used = False
    if not matches and (dressing_type != "All" or application != "All"):
        matches = dm.filter_products(
            wound_type=wound_type if wound_type != "All" else None,
            indication=indication if indication != "All" else None,
            exudate=exudate_level if exudate_level != "All" else None,
        )
        fallback_used = True

    # Categorize into Primary vs Secondary
    primary_list = []
    secondary_list = []
    other_list = []

    for p in matches:
        dtype = p.get("dressing_type", "").lower()
        if "primary" in dtype:
            primary_list.append(p)
        elif "secondary" in dtype:
            secondary_list.append(p)
        else:
            other_list.append(p)

    # Extract active contraindication warnings from matched products
    contraindications_found = []
    for p in matches:
        contra = p.get("contraindications", "")
        if contra and contra.lower() != "nan" and contra not in contraindications_found:
            contraindications_found.append({
                "product_name": p["product_name"],
                "warning": contra
            })

    return {
        "is_emergency": False,
        "fallback_used": fallback_used,
        "primary_matches": primary_list,
        "secondary_matches": secondary_list,
        "all_matches": matches,
        "contraindication_alerts": contraindications_found,
        "total_count": len(matches),
    }
