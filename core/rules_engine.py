"""
Deterministic Clinical Decision Support (CDS) Rules Engine
Maps 12-parameter wound assessments to validated AWC treatment plans.
"""

from typing import List, Optional
from core.models import (
    WoundAssessment,
    RecommendationResult,
    RecommendationItem,
    AWCProduct,
    DressingCategory,
    DressingRole,
    ExudateLevel,
    WoundDepthType,
    BioburdenGrade,
    VascularStatus,
    PeriwoundCondition,
)
from core.triage import evaluate_clinical_triage
from core.contraindications import evaluate_clinical_contraindications, is_product_contraindicated
from data.catalog_manager import get_catalog


def process_clinical_assessment(assessment: WoundAssessment) -> RecommendationResult:
    """Core rules engine mapping clinical assessment to AWC products."""
    # 1. Evaluate Triage Circuit Breaker
    triage = evaluate_clinical_triage(assessment)
    result = RecommendationResult(triage=triage)

    if not triage.allow_product_browsing:
        return result  # Hard Stop - Emergency

    # 2. Evaluate Safety Interlocks & Contraindications
    active_alerts = evaluate_clinical_contraindications(assessment)
    result.active_contraindications = active_alerts

    # 3. Fetch Full Product Catalog
    catalog = get_catalog()
    all_products = catalog.get_all_products()

    # Safe Filter Function
    def filter_safe_products(products: List[AWCProduct]) -> List[AWCProduct]:
        return [p for p in products if not is_product_contraindicated(p, active_alerts)[0]]

    safe_products = filter_safe_products(all_products)

    # 4. Deterministic Clinical Logic
    # 4A. Determine Cavity Packing Requirement
    needs_cavity_filler = (
        assessment.depth_type in [WoundDepthType.DEEP_CAVITY, WoundDepthType.UNDERMINING_TUNNELING]
        or assessment.has_undermining_tunneling
        or assessment.depth_cm >= 0.5
    )

    if needs_cavity_filler:
        fillers = [p for p in safe_products if p.role == DressingRole.CAVITY_FILLER]
        best_filler = None

        # If infected/bioburden -> use Antimicrobial cavity filler
        if assessment.bioburden_grade in [BioburdenGrade.LOCAL_INFECTION, BioburdenGrade.CRITICAL_COLONIZATION]:
            anti_fillers = [f for f in fillers if f.category == DressingCategory.ANTIMICROBIAL_SILVER and "Rope" in f.brand_name]
            best_filler = anti_fillers[0] if anti_fillers else (fillers[0] if fillers else None)
        # If heavy exudate -> Alginate/Hydrofiber rope
        else:
            abs_fillers = [f for f in fillers if f.category in [DressingCategory.HYDROFIBER_RIBBON, DressingCategory.CALCIUM_ALGINATE_ROPE]]
            best_filler = abs_fillers[0] if abs_fillers else (fillers[0] if fillers else None)

        if best_filler:
            result.cavity_filler = RecommendationItem(
                product=best_filler,
                match_score=95.0,
                match_rationale=[
                    "Wound depth and/or tunneling requires specialized dead-space management.",
                    "Prevents superficial closure over a cavity (avoids abscess formation).",
                    "Rope/Ribbon format allows intact single-piece removal."
                ],
                role_in_care_plan="Cavity Packing Filler",
                recommended_change_frequency=f"Every {best_filler.wear_time_recommended_days} days or when saturated.",
                secondary_dressing_required=True,
            )

    # 4B. Determine Primary Wound Contact / Antimicrobial Layer
    primary_options = [p for p in safe_products if p.role in [DressingRole.PRIMARY, DressingRole.COMPOSITE]]
    best_primary = None
    rationale = []

    if assessment.bioburden_grade in [BioburdenGrade.LOCAL_INFECTION, BioburdenGrade.SPREADING_SYSTEMIC, BioburdenGrade.CRITICAL_COLONIZATION]:
        # Infection protocol
        if assessment.exudate_level in [ExudateLevel.HEAVY, ExudateLevel.COPIOUS, ExudateLevel.MODERATE]:
            primaries = [p for p in primary_options if p.category == DressingCategory.ANTIMICROBIAL_SILVER and p.format == "sheet"]
            if not primaries:
                # Fallback to foam or superabsorbent if silver is blocked
                if assessment.periwound_state == PeriwoundCondition.FRAGILE_AGED:
                    primaries = [p for p in primary_options if p.category == DressingCategory.POLYURETHANE_FOAM_NON_BORDERED]
                else:
                    primaries = [p for p in primary_options if p.category == DressingCategory.SUPERABSORBENT_PAD]
            best_primary = primaries[0] if primaries else None
            rationale = ["Ionic silver targets local bioburden safely (or secondary absorbent if antimicrobial contraindicated).", "Surfactant handles biofilm matrices."]
        else:
            # Low exudate / biofilm
            primaries = [p for p in primary_options if p.category == DressingCategory.ANTIMICROBIAL_IODINE]
            best_primary = primaries[0] if primaries else None
            rationale = ["Cadexomer iodine absorbs slough and provides sustained antimicrobial release.", "Safe for low-moderate exudate beds."]
    elif assessment.exudate_level == ExudateLevel.NONE_SCANT:
        # Moisture donor required
        primaries = [p for p in primary_options if p.category == DressingCategory.HYDROGEL_AMORPHOUS]
        best_primary = primaries[0] if primaries else None
        rationale = ["Dry wound requires moisture donation to promote autolytic debridement.", "Prevents desiccation of viable tissue."]
    elif assessment.exudate_level in [ExudateLevel.HEAVY, ExudateLevel.COPIOUS]:
        # Heavy exudate management
        if assessment.periwound_state == PeriwoundCondition.FRAGILE_AGED:
            primaries = [p for p in primary_options if p.category == DressingCategory.POLYURETHANE_FOAM_NON_BORDERED]
            best_primary = primaries[0] if primaries else None
            rationale = ["Non-bordered foam absorbs high exudate vertically.", "Eliminates adhesive trauma (MARSI) to fragile periwound skin."]
        else:
            primaries = [p for p in primary_options if p.category == DressingCategory.SUPERABSORBENT_PAD]
            best_primary = primaries[0] if primaries else None
            rationale = ["Superabsorbent polymer locks massive exudate away to prevent severe periwound maceration."]
    else:
        # Standard Moderate exudate (Workhorse Foam)
        primaries = [p for p in primary_options if p.category == DressingCategory.POLYURETHANE_FOAM_BORDERED]
        best_primary = primaries[0] if primaries else None
        rationale = ["Composite foam manages moderate exudate while protecting from shear.", "Silicone border prevents blistering."]

    if best_primary:
        # Check if it needs a secondary cover
        needs_cover = best_primary.role == DressingRole.PRIMARY or not best_primary.waterproof_barrier

        result.optimal_primary = RecommendationItem(
            product=best_primary,
            match_score=92.5,
            match_rationale=rationale,
            role_in_care_plan="Primary Dressing (or Composite)" if not needs_cover else "Primary Wound Contact Layer",
            recommended_change_frequency=f"Change every {best_primary.wear_time_recommended_days} days or if leakage occurs.",
            secondary_dressing_required=needs_cover,
            suggested_secondary_type="Bordered foam or gauze wrap" if needs_cover else None
        )

        # 4C. Determine Secondary Cover (if needed)
        if needs_cover:
            secondaries = [p for p in safe_products if p.role == DressingRole.COMPOSITE and p.category == DressingCategory.POLYURETHANE_FOAM_BORDERED]
            best_secondary = secondaries[0] if secondaries else None
            if best_secondary:
                result.secondary_cover = RecommendationItem(
                    product=best_secondary,
                    match_score=90.0,
                    match_rationale=["Provides waterproof outer barrier.", "Absorbs strike-through from primary / cavity packing."],
                    role_in_care_plan="Secondary Cover Dressing",
                    recommended_change_frequency=f"Change as needed or every {best_secondary.wear_time_recommended_days} days.",
                    secondary_dressing_required=False,
                )

    # 4D. Periwound Skin Protectant
    if assessment.periwound_state in [PeriwoundCondition.FRAGILE_AGED, PeriwoundCondition.MACERATED, PeriwoundCondition.EXCORIATED_DENUDED]:
        protectants = [p for p in safe_products if p.category == DressingCategory.SKIN_BARRIER_FILM]
        if protectants:
            result.skin_protectant = RecommendationItem(
                product=protectants[0],
                match_score=98.0,
                match_rationale=[
                    f"Selected due to {assessment.periwound_state.value} periwound skin.",
                    "Provides cyanoacrylate barrier against corrosive exudate and adhesive stripping."
                ],
                role_in_care_plan="Periwound Skin Protectant",
                recommended_change_frequency="Reapply every 48-72 hours or at each dressing change.",
                secondary_dressing_required=False,
            )

    # 4E. Advanced Clinical Step-Up (Rx Biologics / Collagen)
    is_infected = assessment.bioburden_grade in [BioburdenGrade.LOCAL_INFECTION, BioburdenGrade.SPREADING_SYSTEMIC, BioburdenGrade.CRITICAL_COLONIZATION]
    if not is_infected and assessment.exudate_level != ExudateLevel.HEAVY:
         collagens = [p for p in safe_products if p.category == DressingCategory.COLLAGEN_MATRIX]
         if collagens:
             result.step_up_rx_option = RecommendationItem(
                 product=collagens[0],
                 match_score=85.0,
                 match_rationale=[
                     "Advanced Rx option for stalled chronic wounds (stimulates stalled fibroblasts).",
                     "Binds destructive MMP enzymes found in chronic non-healing ulcers."
                 ],
                 role_in_care_plan="Advanced Physiologic Modulator (Physician Order Only)",
                 recommended_change_frequency="Change every 2-3 days under secondary cover.",
                 secondary_dressing_required=True,
             )

    # Generate Handoff Summary
    result.change_protocol_summary = (
        "Cleanse wound with sterile saline. "
        + ("Apply barrier film to periwound skin, allow to dry. " if result.skin_protectant else "")
        + ("Pack cavity loosely with ribbon to 80% volume, leaving small tail. " if result.cavity_filler else "")
        + (f"Apply {result.optimal_primary.product.brand_name} directly to wound bed. " if result.optimal_primary else "")
        + (f"Cover entirely with {result.secondary_cover.product.brand_name} ensuring 2-inch border. " if result.secondary_cover else "")
        + "Do not wrap tightly around limbs to avoid tourniquet effect."
    )

    return result
