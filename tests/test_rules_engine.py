"""
Integration tests for Clinical Rules Engine
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
    DressingRole,
)
from core.rules_engine import process_clinical_assessment


def test_deep_cavity_wound_triggers_cavity_filler():
    assessment = WoundAssessment(
        etiology=WoundEtiology.PRESSURE_INJURY,
        exudate_level=ExudateLevel.HEAVY,
        depth_type=WoundDepthType.DEEP_CAVITY,
        depth_cm=2.5,
        has_undermining_tunneling=True,
    )
    result = process_clinical_assessment(assessment)
    assert result.cavity_filler is not None
    assert result.cavity_filler.product.role == DressingRole.CAVITY_FILLER
    assert result.secondary_cover is not None


def test_fragile_periwound_triggers_skin_protectant_and_gentle_foam():
    assessment = WoundAssessment(
        etiology=WoundEtiology.VENOUS_LEG_ULCER,
        exudate_level=ExudateLevel.HEAVY,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        periwound_state=PeriwoundCondition.FRAGILE_AGED,
    )
    result = process_clinical_assessment(assessment)
    assert result.skin_protectant is not None
    assert result.skin_protectant.product.category == DressingCategory.SKIN_BARRIER_FILM
    assert result.optimal_primary is not None
    assert result.optimal_primary.product.category == DressingCategory.POLYURETHANE_FOAM_NON_BORDERED


def test_dry_wound_prescribes_moisture_donor():
    assessment = WoundAssessment(
        etiology=WoundEtiology.PRESSURE_INJURY,
        exudate_level=ExudateLevel.NONE_SCANT,
        depth_type=WoundDepthType.SUPERFICIAL_PARTIAL,
        eschar_percent=30,
    )
    result = process_clinical_assessment(assessment)
    assert result.optimal_primary is not None
    assert result.optimal_primary.product.category == DressingCategory.HYDROGEL_AMORPHOUS
