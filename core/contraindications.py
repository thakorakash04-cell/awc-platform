"""
Poka-Yoke Clinical Safety Interlocks & Contraindication Matrix
Implements deterministic error-proofing rules preventing hazardous dressing selections.
"""

from typing import Optional, List, Tuple
from core.models import (
    WoundAssessment,
    AWCProduct,
    DressingCategory,
    AdhesiveType,
    ClinicalContraindicationAlert,
    WoundEtiology,
    VascularStatus,
    BioburdenGrade,
    ExudateLevel,
    PeriwoundCondition,
)


def evaluate_clinical_contraindications(assessment: WoundAssessment) -> List[ClinicalContraindicationAlert]:
    """Evaluates all safety rules against the wound assessment and returns active alerts/blocks."""
    alerts: List[ClinicalContraindicationAlert] = []

    # Rule 1: Arterial Ischemia vs. Multi-Layer Compression
    is_ischemic = (
        assessment.vascular_status in [VascularStatus.SEVERE_ISCHEMIA, VascularStatus.BORDERLINE_PAD]
        or (assessment.abpi_value is not None and assessment.abpi_value < 0.8)
        or assessment.etiology == WoundEtiology.ARTERIAL_ULCER
    )
    if is_ischemic:
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-VASC-01",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.MULTI_LAYER_COMPRESSION.value,
                clinical_reason=(
                    "Compression therapy (Class II-IV multi-layer systems) is strictly contraindicated in arterial insufficiency "
                    f"or ABPI < 0.8 (Current ABPI: {assessment.abpi_value if assessment.abpi_value is not None else 'Unverified/Ischemic'}). "
                    "Applying compression over an ischemic limb obliterates microvascular perfusion, precipitating acute necrosis, gangrene, and limb loss."
                ),
                evidence_source="WOCN & Society for Vascular Surgery (SVS) Venous/Arterial Clinical Practice Guidelines",
                suggested_alternative="Non-compressive protective foam, soft silicone contact layer, and urgent vascular revascularization consult.",
            )
        )

    # Rule 2: Infection vs. Occlusive Dressings (Hydrocolloids & Standard Films)
    is_infected = assessment.bioburden_grade in [BioburdenGrade.LOCAL_INFECTION, BioburdenGrade.SPREADING_SYSTEMIC]
    if is_infected:
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-INF-02",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.HYDROCOLLOID_STANDARD.value,
                clinical_reason=(
                    "Occlusive hydrocolloids and non-breathable films are strictly contraindicated in the presence of local or spreading infection. "
                    "Occlusion creates a warm, hypoxic environment that accelerates the proliferation of virulent anaerobic pathogens "
                    "(e.g., Pseudomonas aeruginosa, Clostridium species) and traps toxic bacterial proteases against the wound bed."
                ),
                evidence_source="International Wound Infection Institute (IWII) Consensus Guidelines (2022)",
                suggested_alternative="Breathable antimicrobial foam (Silver / PHMB / Cadexomer Iodine) or gelling fiber with high MVTR cover.",
            )
        )
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-INF-03",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.TRANSPARENT_FILM.value,
                clinical_reason="Standard occlusive films trap purulent exudate in infected wounds.",
                evidence_source="IWII 2022 Guidelines",
                suggested_alternative="Permeable secondary foam or gauze wrap.",
            )
        )

    # Rule 3: Dry / Scant Exudate vs. High-Absorbency Calcium Alginates & Hydrofibers
    if assessment.exudate_level == ExudateLevel.NONE_SCANT:
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-MOIST-04",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.CALCIUM_ALGINATE_SHEET.value,
                clinical_reason=(
                    "Calcium alginates and hydrofibers require significant fluid absorption to activate their sodium-calcium ion exchange "
                    "and transform into a soft gel. On dry or minimally exudative wounds, these fibers dehydrate the bed, adhere tenaciously "
                    "to viable tissue, and tear delicate granulation capillaries upon dressing removal."
                ),
                evidence_source="Winter's Principle of Moist Wound Healing & EWMA Position Document on Exudate Management",
                suggested_alternative="Amorphous hydrogel, hydrogel sheet, or soft silicone wound contact layer to donate/maintain moisture.",
            )
        )
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-MOIST-05",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.SUPERABSORBENT_PAD.value,
                clinical_reason="Superabsorbent polymer pads will severely desiccate a dry wound bed.",
                evidence_source="EWMA Exudate Consensus",
                suggested_alternative="Hydrogel sheet or thin hydrocolloid.",
            )
        )

    # Rule 4: Dry Ischemic Gangrene vs. Autolytic Debriding Hydrogels
    if assessment.eschar_percent > 40 and is_ischemic:
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-DEBRID-06",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.HYDROGEL_AMORPHOUS.value,
                clinical_reason=(
                    "Applying hydrating hydrogels or autolytic debriding agents to stable, dry ischemic gangrene is strictly contraindicated. "
                    "Donating moisture softens stable dry eschar without blood supply to fight bacteria, converting it into lethal wet gangrene."
                ),
                evidence_source="WOCN Clinical Practice Guidelines for Management of Wounds with Arterial Disease",
                suggested_alternative="Paint with povidone-iodine (Betadine) to maintain dry stable eschar; refer for urgent vascular evaluation.",
            )
        )

    # Rule 5: Heavy / Copious Exudate vs. Thin Films & Hydrogels
    if assessment.exudate_level in [ExudateLevel.HEAVY, ExudateLevel.COPIOUS]:
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-MOIST-07",
                severity="WARNING",
                blocked_category=DressingCategory.HYDROGEL_AMORPHOUS.value,
                clinical_reason="Amorphous hydrogels donate moisture and are contraindicated on high-exudate wounds due to risk of fluid overload.",
                evidence_source="WUWHS Consensus on Wound Exudate Management",
                suggested_alternative="Hydrofiber sheet/ribbon, superabsorbent pad, or high-capacity polyurethane foam.",
            )
        )
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-MOIST-08",
                severity="WARNING",
                blocked_category=DressingCategory.HYDROCOLLOID_THIN.value,
                clinical_reason="Thin hydrocolloids have low fluid capacity; high exudate will cause rapid strike-through and maceration.",
                evidence_source="WUWHS Consensus",
                suggested_alternative="Superabsorbent pad or high-capacity bordered foam.",
            )
        )

    # Rule 6: Enzymatic Debrider vs. Heavy Metal Silver Incompatibility
    if assessment.current_enzymatic_debrider:
        alerts.append(
            ClinicalContraindicationAlert(
                rule_id="RULE-CHEM-09",
                severity="CRITICAL_CONTRAINDICATION",
                blocked_category=DressingCategory.ANTIMICROBIAL_SILVER.value,
                clinical_reason=(
                    "Ionic silver dressings and heavy metal compounds precipitate and enzymatically deactivate Collagenase (Santyl). "
                    "Concurrent use renders enzymatic debridement completely ineffective."
                ),
                evidence_source="FDA Drug Labeling for Collagenase Santyl Ointment & Antimicrobial Dressing Compatibility Matrix",
                suggested_alternative="Medical Honey (Leptospermum) or PHMB dressings which do not deactivate collagenase.",
            )
        )

    # Rule 7: Known Allergies Interlocks
    for allergy in assessment.known_allergies:
        allergy_lower = allergy.lower()
        if "silver" in allergy_lower:
            alerts.append(
                ClinicalContraindicationAlert(
                    rule_id="RULE-ALLERGY-SILVER",
                    severity="CRITICAL_CONTRAINDICATION",
                    blocked_category=DressingCategory.ANTIMICROBIAL_SILVER.value,
                    clinical_reason="Patient has a documented hypersensitivity / allergy to silver compounds.",
                    evidence_source="Patient Medical Record Safety Check",
                    suggested_alternative="Cadexomer Iodine (if thyroid normal), Medical Honey, or PHMB.",
                )
            )
        if "iodine" in allergy_lower:
            alerts.append(
                ClinicalContraindicationAlert(
                    rule_id="RULE-ALLERGY-IODINE",
                    severity="CRITICAL_CONTRAINDICATION",
                    blocked_category=DressingCategory.ANTIMICROBIAL_IODINE.value,
                    clinical_reason="Patient has a documented hypersensitivity to iodine compounds.",
                    evidence_source="Patient Medical Record Safety Check",
                    suggested_alternative="Silver antimicrobial or Medical Honey.",
                )
            )
        if "honey" in allergy_lower or "bee" in allergy_lower:
            alerts.append(
                ClinicalContraindicationAlert(
                    rule_id="RULE-ALLERGY-HONEY",
                    severity="CRITICAL_CONTRAINDICATION",
                    blocked_category=DressingCategory.ANTIMICROBIAL_HONEY.value,
                    clinical_reason="Patient has a documented hypersensitivity to bee venom or honey.",
                    evidence_source="Patient Medical Record Safety Check",
                    suggested_alternative="Silver or PHMB antimicrobial dressing.",
                )
            )

    return alerts


def is_product_contraindicated(
    product: AWCProduct, active_alerts: List[ClinicalContraindicationAlert]
) -> Tuple[bool, Optional[ClinicalContraindicationAlert]]:
    """Checks if a specific product is blocked by any active contraindication alert."""
    blocked_categories = {a.blocked_category for a in active_alerts if a.severity == "CRITICAL_CONTRAINDICATION"}

    if product.category.value in blocked_categories:
        matching_alert = next((a for a in active_alerts if a.blocked_category == product.category.value), None)
        return True, matching_alert

    # Check antimicrobial category if applicable
    if product.active_antimicrobial:
        if "Silver" in product.active_antimicrobial and DressingCategory.ANTIMICROBIAL_SILVER.value in blocked_categories:
            alert = next((a for a in active_alerts if a.blocked_category == DressingCategory.ANTIMICROBIAL_SILVER.value), None)
            return True, alert
        if "Iodine" in product.active_antimicrobial and DressingCategory.ANTIMICROBIAL_IODINE.value in blocked_categories:
            alert = next((a for a in active_alerts if a.blocked_category == DressingCategory.ANTIMICROBIAL_IODINE.value), None)
            return True, alert
        if "Honey" in product.active_antimicrobial and DressingCategory.ANTIMICROBIAL_HONEY.value in blocked_categories:
            alert = next((a for a in active_alerts if a.blocked_category == DressingCategory.ANTIMICROBIAL_HONEY.value), None)
            return True, alert

    return False, None
