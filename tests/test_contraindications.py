"""
Unit tests for Contraindication Matrix & Safety Interlocks
"""

import pytest
from core.models import (
    WoundAssessment,
    WoundEtiology,
    ExudateLevel,
    WoundDepthType,
    BioburdenGrade,
    VascularStatus,
    PeriwoundCondition,
    DressingCategory,
)
from core.contraindications import evaluate_clinical_contraindications


def test_arterial_ischemia_blocks_compression():
    assessment = WoundAssessment(
        etiology=WoundEtiology.ARTERIAL_ULCER,
        exudate_level=ExudateLevel.NONE_SCANT,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        vascular_status=VascularStatus.SEVERE_ISCHEMIA,
        abpi_value=0.45,
    )
    alerts = evaluate_clinical_contraindications(assessment)
    blocked = [a.blocked_category for a in alerts if a.severity == "CRITICAL_CONTRAINDICATION"]
    assert DressingCategory.MULTI_LAYER_COMPRESSION.value in blocked


def test_infection_blocks_occlusive_hydrocolloids():
    assessment = WoundAssessment(
        etiology=WoundEtiology.VENOUS_LEG_ULCER,
        exudate_level=ExudateLevel.MODERATE,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        bioburden_grade=BioburdenGrade.LOCAL_INFECTION,
    )
    alerts = evaluate_clinical_contraindications(assessment)
    blocked = [a.blocked_category for a in alerts if a.severity == "CRITICAL_CONTRAINDICATION"]
    assert DressingCategory.HYDROCOLLOID_STANDARD.value in blocked
    assert DressingCategory.TRANSPARENT_FILM.value in blocked


def test_dry_wound_blocks_calcium_alginates():
    assessment = WoundAssessment(
        etiology=WoundEtiology.PRESSURE_INJURY,
        exudate_level=ExudateLevel.NONE_SCANT,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
    )
    alerts = evaluate_clinical_contraindications(assessment)
    blocked = [a.blocked_category for a in alerts if a.severity == "CRITICAL_CONTRAINDICATION"]
    assert DressingCategory.CALCIUM_ALGINATE_SHEET.value in blocked


def test_enzymatic_debrider_blocks_silver():
    assessment = WoundAssessment(
        etiology=WoundEtiology.PRESSURE_INJURY,
        exudate_level=ExudateLevel.MODERATE,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        current_enzymatic_debrider=True,
    )
    alerts = evaluate_clinical_contraindications(assessment)
    blocked = [a.blocked_category for a in alerts if a.severity == "CRITICAL_CONTRAINDICATION"]
    assert DressingCategory.ANTIMICROBIAL_SILVER.value in blocked


def test_allergy_interlock_blocks_silver():
    assessment = WoundAssessment(
        etiology=WoundEtiology.VENOUS_LEG_ULCER,
        exudate_level=ExudateLevel.MODERATE,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        known_allergies=["silver", "iodine"],
    )
    alerts = evaluate_clinical_contraindications(assessment)
    blocked = [a.blocked_category for a in alerts]
    assert DressingCategory.ANTIMICROBIAL_SILVER.value in blocked
    assert DressingCategory.ANTIMICROBIAL_IODINE.value in blocked
