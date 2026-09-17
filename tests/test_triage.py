"""
Unit tests for Clinical and Layperson Triage Logic
"""

import pytest
from core.models import (
    WoundAssessment,
    WoundEtiology,
    ExudateLevel,
    WoundDepthType,
    BioburdenGrade,
    VascularStatus,
    TriageSeverity,
)
from core.triage import evaluate_clinical_triage, evaluate_layperson_red_flags


def test_exposed_bone_triggers_emergency_hard_stop():
    assessment = WoundAssessment(
        etiology=WoundEtiology.PRESSURE_INJURY,
        exudate_level=ExudateLevel.MODERATE,
        depth_type=WoundDepthType.EXPOSED_BONE_TENDON,
    )
    result = evaluate_clinical_triage(assessment)
    assert result.severity == TriageSeverity.TIER_1_EMERGENCY_HARD_STOP
    assert not result.allow_product_browsing
    assert any("bone" in rf.lower() for rf in result.triggered_red_flags)


def test_severe_ischemia_triggers_emergency():
    assessment = WoundAssessment(
        etiology=WoundEtiology.ARTERIAL_ULCER,
        exudate_level=ExudateLevel.NONE_SCANT,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        vascular_status=VascularStatus.SEVERE_ISCHEMIA,
        abpi_value=0.42,
    )
    result = evaluate_clinical_triage(assessment)
    assert result.severity == TriageSeverity.TIER_1_EMERGENCY_HARD_STOP
    assert not result.allow_product_browsing


def test_diabetic_foot_ulcer_triggers_urgent_referral():
    assessment = WoundAssessment(
        etiology=WoundEtiology.DIABETIC_FOOT_ULCER,
        exudate_level=ExudateLevel.MODERATE,
        depth_type=WoundDepthType.FULL_THICKNESS_SHALLOW,
    )
    result = evaluate_clinical_triage(assessment)
    assert result.severity == TriageSeverity.TIER_2_URGENT_REFERRAL
    assert result.allow_product_browsing


def test_layperson_red_flags_fever_and_bone():
    res = evaluate_layperson_red_flags(
        has_fever_or_chills=True,
        has_spreading_redness=False,
        has_exposed_bone_tendon=True,
        is_black_foul_smelling=False,
        has_cold_numb_foot=False,
        wound_cause="scrape",
        duration_weeks=1,
    )
    assert res.severity == TriageSeverity.TIER_1_EMERGENCY_HARD_STOP
    assert not res.allow_product_browsing
