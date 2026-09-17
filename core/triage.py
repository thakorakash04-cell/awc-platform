"""
Clinical Triage & Red-Flag Circuit Breaker
Implements IEC 62366-1 Usability & Patient Safety Interlocks.
"""

from typing import List, Dict, Any, Optional
from core.models import (
    TriageResult,
    TriageSeverity,
    WoundAssessment,
    LaypersonAssessment,
    WoundDepthType,
    BioburdenGrade,
    VascularStatus,
    WoundEtiology,
)


def evaluate_clinical_triage(assessment: WoundAssessment) -> TriageResult:
    """Evaluates comprehensive clinical inputs for emergency red-flags and urgent escalations."""
    red_flags: List[str] = []
    is_emergency = False
    is_urgent = False

    # Tier 1: Emergency Triggers (Immediate 911 / ER)
    if assessment.depth_type == WoundDepthType.EXPOSED_BONE_TENDON:
        red_flags.append("Visible exposed bone, tendon, joint capsule, or surgical hardware (High osteomyelitis risk)")
        is_emergency = True

    if assessment.bioburden_grade == BioburdenGrade.SPREADING_SYSTEMIC:
        red_flags.append("Systemic infection or spreading cellulitis (>2cm erythema, fever, rigors, or sepsis risk)")
        is_emergency = True

    if assessment.vascular_status == VascularStatus.SEVERE_ISCHEMIA:
        red_flags.append("Severe critical limb ischemia (ABPI < 0.5, pulseless, pale/cyanotic extremity)")
        is_emergency = True

    if assessment.abpi_value is not None and assessment.abpi_value < 0.5:
        red_flags.append(f"Severely low Ankle-Brachial Index (ABPI = {assessment.abpi_value:.2f} < 0.50)")
        is_emergency = True

    # Tier 2: Urgent Wound Care Referrals (24-48 hours)
    if assessment.etiology == WoundEtiology.DIABETIC_FOOT_ULCER:
        red_flags.append("Diabetic neuropathic foot ulcer requiring offloading (TCC), vascular screening, and debridement")
        is_urgent = True

    if assessment.etiology == WoundEtiology.ATYPICAL_VASCULITIC:
        red_flags.append("Suspicion of atypical vasculitic, calciphylaxis, or malignant ulcer requiring punch biopsy")
        is_urgent = True

    if assessment.has_undermining_tunneling:
        red_flags.append("Undermining / tunneling tracts requiring structured cavity packing and debridement")
        is_urgent = True

    # Formulate Triage Output
    if is_emergency:
        sbar = (
            f"SITUATION: Patient presents with acute high-risk wound escalation.\n"
            f"BACKGROUND: Evaluated etiology: {assessment.etiology.value}. Anatomical location: {assessment.anatomical_location}.\n"
            f"ASSESSMENT: Emergency red flags triggered:\n"
            + "\n".join([f"  - {rf}" for rf in red_flags])
            + f"\nRECOMMENDATION: Immediate emergency evaluation required. Withhold autonomous dressing selection. Sepsis/ischemia/osteomyelitis workup indicated."
        )
        return TriageResult(
            severity=TriageSeverity.TIER_1_EMERGENCY_HARD_STOP,
            triggered_red_flags=red_flags,
            patient_action_message=(
                "CRITICAL EMERGENCY ALERT: Immediate medical evaluation is required. "
                "This wound shows signs of deep structural involvement, spreading infection, or acute vascular compromise. "
                "Do NOT attempt to treat this wound at home with standard dressings. "
                "Please proceed immediately to the nearest Emergency Room or call 911."
            ),
            clinical_summary_sbar=sbar,
            allow_product_browsing=False,
        )

    if is_urgent:
        sbar = (
            f"SITUATION: Chronic or complex wound requiring specialist clinical evaluation.\n"
            f"BACKGROUND: Etiology: {assessment.etiology.value}. Depth: {assessment.depth_cm} cm.\n"
            f"ASSESSMENT: Urgent clinical markers:\n"
            + "\n".join([f"  - {rf}" for rf in red_flags])
            + f"\nRECOMMENDATION: Referral to Wound Care Center / Podiatry / Vascular Specialist within 24-48 hours. Safe interim protective dressing recommended."
        )
        return TriageResult(
            severity=TriageSeverity.TIER_2_URGENT_REFERRAL,
            triggered_red_flags=red_flags,
            patient_action_message=(
                "SPECIALIST EVALUATION RECOMMENDED: This wound has complex clinical factors "
                "(such as diabetes, deep cavity, or atypical features) that require professional evaluation by a "
                "wound care specialist, podiatrist, or vascular physician within 24 to 48 hours. "
                "The system provides safe interim protective recommendations below."
            ),
            clinical_summary_sbar=sbar,
            allow_product_browsing=True,
        )

    return TriageResult(
        severity=TriageSeverity.SAFE_FOR_SELECTION,
        triggered_red_flags=[],
        patient_action_message="Assessment complete: Safe to proceed with clinical dressing selection.",
        clinical_summary_sbar=None,
        allow_product_browsing=True,
    )


def evaluate_layperson_red_flags(
    has_fever_or_chills: bool,
    has_spreading_redness: bool,
    has_exposed_bone_tendon: bool,
    is_black_foul_smelling: bool,
    has_cold_numb_foot: bool,
    wound_cause: str,
    duration_weeks: int,
) -> TriageResult:
    """Evaluates layperson questionnaire answers for critical emergency triggers."""
    red_flags: List[str] = []
    is_emergency = False
    is_urgent = False

    if has_exposed_bone_tendon:
        red_flags.append("You can see white shiny tendon, bone, or deep structures in the wound.")
        is_emergency = True

    if has_fever_or_chills:
        red_flags.append("Fever, shaking chills, severe weakness, or feeling generally sick.")
        is_emergency = True

    if has_spreading_redness:
        red_flags.append("Redness or swelling is rapidly spreading more than an inch from the wound edges.")
        is_emergency = True

    if has_cold_numb_foot:
        red_flags.append("Foot or leg feels cold to the touch, pale/blue, numb, or has severe pain when lying flat.")
        is_emergency = True

    if is_black_foul_smelling:
        red_flags.append("Wound has black, mushy tissue with a strong foul odor (possible gangrene).")
        is_emergency = True

    # Urgent triggers
    if "diabetes" in wound_cause.lower():
        red_flags.append("Any new open sore on the foot in a person with diabetes requires doctor evaluation.")
        is_urgent = True

    if duration_weeks >= 4:
        red_flags.append(f"Wound has not healed after {duration_weeks} weeks (chronic stalled wound).")
        is_urgent = True

    if is_emergency:
        sbar = (
            f"SITUATION: Patient reports acute wound warning signs via triage tool.\n"
            f"REPORTED SYMPTOMS:\n"
            + "\n".join([f"  - {rf}" for rf in red_flags])
            + f"\nACTION TAKEN: Directed patient to emergency care. Product selection halted."
        )
        return TriageResult(
            severity=TriageSeverity.TIER_1_EMERGENCY_HARD_STOP,
            triggered_red_flags=red_flags,
            patient_action_message=(
                "EMERGENCY MEDICAL ATTENTION REQUIRED: Your answers indicate signs that could point to a "
                "serious deep infection, poor blood flow, or tissue risk. "
                "Applying over-the-counter bandages without an emergency doctor exam can be dangerous. "
                "Please go to the nearest Emergency Room or Urgent Care Center immediately."
            ),
            clinical_summary_sbar=sbar,
            allow_product_browsing=False,
        )

    if is_urgent:
        sbar = (
            f"SITUATION: Patient reports chronic or diabetic foot ulcer.\n"
            f"DURATION: {duration_weeks} weeks. Cause: {wound_cause}.\n"
            f"REPORTED FINDINGS:\n"
            + "\n".join([f"  - {rf}" for rf in red_flags])
            + f"\nRECOMMENDATION: Schedule in-person clinical appointment within 24-48 hours."
        )
        return TriageResult(
            severity=TriageSeverity.TIER_2_URGENT_REFERRAL,
            triggered_red_flags=red_flags,
            patient_action_message=(
                "DOCTOR VISIT RECOMMENDED: Because this wound is linked to diabetes or has lasted more than "
                "a month without healing, it needs a professional exam by a doctor or wound specialist within 1 to 2 days. "
                "Below are safe, gentle protective bandages you can use while waiting for your appointment."
            ),
            clinical_summary_sbar=sbar,
            allow_product_browsing=True,
        )

    return TriageResult(
        severity=TriageSeverity.SAFE_FOR_SELECTION,
        triggered_red_flags=[],
        patient_action_message="No emergency red flags reported. Safe to view recommended dressings.",
        clinical_summary_sbar=None,
        allow_product_browsing=True,
    )
