"""
Core Clinical & Product Data Models
Structured according to WOCN, EWMA, IWII guidelines, and US Medicare LCD L33331 standards.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    LAYPERSON = "layperson"  # Patient / Caregiver
    CLINICIAN = "clinician"  # MD, DO, DPM, WOCN, NP, PT, RN


class WoundEtiology(str, Enum):
    PRESSURE_INJURY = "pressure_injury"
    VENOUS_LEG_ULCER = "venous_leg_ulcer"
    DIABETIC_FOOT_ULCER = "diabetic_foot_ulcer"
    ARTERIAL_ULCER = "arterial_ulcer"
    SURGICAL_DEHISCENCE = "surgical_dehiscence"
    TRAUMATIC_LACERATION = "traumatic_laceration"
    SKIN_TEAR = "skin_tear"
    FIRST_SECOND_DEGREE_BURN = "burn_partial_thickness"
    ATYPICAL_VASCULITIC = "atypical_vasculitic"


class ExudateLevel(str, Enum):
    NONE_SCANT = "none_scant"      # Dry bed, 0-1 mL/24h
    MINIMAL = "minimal"            # Light dampness, changed q2-3d, 1-3 mL/24h
    MODERATE = "moderate"          # Wet through daily, 3-5 mL/24h
    HEAVY = "heavy"                # Daily strike-through, >5 mL/24h
    COPIOUS = "copious"            # Saturated multiple times daily


class ExudateType(str, Enum):
    SEROUS = "serous"              # Clear, straw-colored, thin
    SEROSANGUINOUS = "serosanguinous"  # Thin, pink to pale red
    SANGUINOUS = "sanguinous"      # Red, bloody
    PURULENT = "purulent"          # Thick, cloudy, yellow/green/brown (infection indicator)


class BioburdenGrade(str, Enum):
    CLEAN = "clean"                              # Normal colonization, non-infected
    CRITICAL_COLONIZATION = "covert_infection"  # NERDS signs: stalled, hyper-granulation, debris, odor
    LOCAL_INFECTION = "local_infection"          # STONEES signs: >2cm erythema, warmth, pain, purulence
    SPREADING_SYSTEMIC = "systemic_sepsis"       # Cellulitis, lymphangitis, fever, rigors (Emergency)


class WoundDepthType(str, Enum):
    SUPERFICIAL_PARTIAL = "superficial_partial"  # Epidermis/dermis only, flat bed
    FULL_THICKNESS_SHALLOW = "full_thickness_shallow"  # Subcutaneous fat visible, < 0.5 cm
    DEEP_CAVITY = "deep_cavity"                  # Depth >= 0.5 cm, dead space present
    UNDERMINING_TUNNELING = "undermining_tunneling"  # Sinus tract / subterranean tracks
    EXPOSED_BONE_TENDON = "exposed_bone_tendon"  # Bone, tendon, joint, hardware (Emergency)


class VascularStatus(str, Enum):
    NORMAL = "normal"              # ABPI >= 0.8, strong palpable pulses
    BORDERLINE_PAD = "borderline"  # ABPI 0.5 - 0.79, mild arterial compromise
    SEVERE_ISCHEMIA = "ischemic"   # ABPI < 0.5, pulseless, pale/mottled (Contraindicates compression)
    UNKNOWN_NOT_TESTED = "unknown" # Requires cautious non-compression approach


class PeriwoundCondition(str, Enum):
    INTACT = "intact"              # Healthy periwound skin
    FRAGILE_AGED = "fragile_aged"  # Thin, friable, MARSI risk (requires gentle silicone)
    MACERATED = "macerated"        # White, waterlogged (requires barrier film + higher absorbency)
    EXCORIATED_DENUDED = "denuded" # Raw, stripped epidermis from fluid or tape
    ERYTHEMATOUS = "erythematous"  # Red, inflamed, contact dermatitis vs cellulitis


class DressingRole(str, Enum):
    PRIMARY = "primary"            # Direct wound contact
    SECONDARY = "secondary"        # Cover / absorption backing
    COMPOSITE = "composite"        # All-in-one bordered island
    CAVITY_FILLER = "cavity_filler"# Ribbon / rope for packing dead space


class DressingCategory(str, Enum):
    POLYURETHANE_FOAM_BORDERED = "foam_bordered"
    POLYURETHANE_FOAM_NON_BORDERED = "foam_non_bordered"
    CALCIUM_ALGINATE_SHEET = "alginate_sheet"
    CALCIUM_ALGINATE_ROPE = "alginate_rope"
    HYDROFIBER_SHEET = "hydrofiber_sheet"
    HYDROFIBER_RIBBON = "hydrofiber_ribbon"
    HYDROCOLLOID_STANDARD = "hydrocolloid_standard"
    HYDROCOLLOID_THIN = "hydrocolloid_thin"
    HYDROGEL_AMORPHOUS = "hydrogel_amorphous"
    HYDROGEL_SHEET = "hydrogel_sheet"
    SILICONE_CONTACT_LAYER = "silicone_contact_layer"
    ANTIMICROBIAL_SILVER = "antimicrobial_silver"
    ANTIMICROBIAL_IODINE = "antimicrobial_cadexomer_iodine"
    ANTIMICROBIAL_HONEY = "antimicrobial_medical_honey"
    ANTIMICROBIAL_PHMB = "antimicrobial_phmb"
    COLLAGEN_MATRIX = "collagen_matrix"
    SUPERABSORBENT_PAD = "superabsorbent_pad"
    TRANSPARENT_FILM = "transparent_film"
    SKIN_BARRIER_FILM = "skin_barrier_film"
    MULTI_LAYER_COMPRESSION = "compression_system"


class AdhesiveType(str, Enum):
    SOFT_SILICONE = "soft_silicone"  # Gentle, atraumatic removal (safest for fragile skin)
    ACRYLIC = "acrylic"              # High initial tack, potential MARSI risk
    HYDROCOLLOID_ADHESIVE = "hydrocolloid_adhesive"
    NON_ADHERENT = "non_adherent"    # Requires secondary tape or tubular wrap


class FormatType(str, Enum):
    PAD = "pad"
    BORDERED_ISLAND = "bordered_island"
    ROPE_RIBBON = "rope_ribbon"
    TUBE_GEL = "tube_gel"
    SHEET = "sheet"
    ROLL_WRAP = "roll_wrap"
    WIPE_SPRAY = "wipe_spray"


# --- Clinical Assessment Models ---

class WoundAssessment(BaseModel):
    """Full 12+ Parameter Clinician Assessment Schema."""
    etiology: WoundEtiology
    exudate_level: ExudateLevel
    exudate_type: ExudateType = ExudateType.SEROUS
    depth_type: WoundDepthType
    depth_cm: float = Field(default=0.0, ge=0.0, le=15.0)
    has_undermining_tunneling: bool = False
    bioburden_grade: BioburdenGrade = BioburdenGrade.CLEAN
    granulation_percent: int = Field(default=100, ge=0, le=100)
    slough_percent: int = Field(default=0, ge=0, le=100)
    eschar_percent: int = Field(default=0, ge=0, le=100)
    epithelial_percent: int = Field(default=0, ge=0, le=100)
    periwound_state: PeriwoundCondition = PeriwoundCondition.INTACT
    vascular_status: VascularStatus = VascularStatus.NORMAL
    abpi_value: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    anatomical_location: str = "Lower Extremity"
    known_allergies: List[str] = Field(default_factory=list)  # e.g., ["silver", "iodine", "honey", "adhesives"]
    current_enzymatic_debrider: bool = False  # If True, Collagenase (Santyl) -> block Silver


class LaypersonAssessment(BaseModel):
    """Jargon-free Perceptual Questionnaire Inputs from Patient / Caregiver."""
    wound_cause: str  # "scrape/cut", "pressure sore", "leg sore", "foot ulcer with diabetes", "surgical cut"
    drainage_frequency: str  # "dry", "light (changed q2-3d)", "moderate (wet daily)", "heavy (leaks through)"
    wound_color_texture: str  # "red_pink", "yellow_creamy", "black_brown_crust", "mixed"
    has_depth_or_hole: bool = False
    skin_around_wound: str = "normal"  # "normal", "fragile_tears_easily", "white_soggy", "red_irritated"
    wants_self_adhesive: bool = True
    known_allergies: List[str] = Field(default_factory=list)


# --- Product & Catalog Models ---

class ProductSKU(BaseModel):
    sku_id: str
    dimensions: str  # e.g., '4" x 4"', '6" x 6"', '3/4" x 18" Rope', '15g Tube'
    hcpcs_code: str  # e.g., 'A6212', 'A6196'
    unit_of_measure: str = "Box of 10"
    estimated_retail_usd: float
    otc_available: bool = True


class AWCProduct(BaseModel):
    """Advanced Wound Care Product Specification Schema."""
    id: str
    brand_name: str
    manufacturer: str
    category: DressingCategory
    generic_moc: str  # Material of Construction, e.g. "Polyurethane foam with Safetac soft silicone"
    role: DressingRole
    adhesive_type: AdhesiveType
    format: FormatType
    fluid_handling_capacity: str  # "Low", "Moderate", "High", "Maximum"
    dynamic_mvtr: str  # "High (breathable)", "Moderate", "Occlusive"
    waterproof_barrier: bool = True
    active_antimicrobial: Optional[str] = None  # "Ionic Silver", "Cadexomer Iodine", "Medical Honey", "PHMB", None
    wear_time_days_max: int = 7
    wear_time_recommended_days: int = 3
    is_rx_only: bool = False
    hcpcs_base_code: str
    indications: List[str]
    contraindications: List[str]
    clinical_pearls: str
    application_instructions: List[str]
    skus: List[ProductSKU] = Field(default_factory=list)


# --- Decision Support & Triage Output Models ---

class TriageSeverity(str, Enum):
    SAFE_FOR_SELECTION = "safe"
    TIER_2_URGENT_REFERRAL = "tier_2_urgent"      # 24-48h Wound Clinic
    TIER_1_EMERGENCY_HARD_STOP = "tier_1_emergency"# 911 / Emergency Room


class TriageResult(BaseModel):
    severity: TriageSeverity
    triggered_red_flags: List[str]
    patient_action_message: str
    clinical_summary_sbar: Optional[str] = None
    allow_product_browsing: bool = True


class RecommendationItem(BaseModel):
    product: AWCProduct
    match_score: float  # 0.0 to 100.0
    match_rationale: List[str]
    role_in_care_plan: str  # "Primary Contact Layer", "Cavity Packing Rope", "Secondary Absorbent Cover", "Skin Protectant"
    recommended_change_frequency: str
    secondary_dressing_required: bool
    suggested_secondary_type: Optional[str] = None


class ClinicalContraindicationAlert(BaseModel):
    rule_id: str
    severity: str  # "CRITICAL_CONTRAINDICATION", "WARNING", "PRECAUTION"
    blocked_category: str
    clinical_reason: str
    evidence_source: str
    suggested_alternative: str


class RecommendationResult(BaseModel):
    triage: TriageResult
    optimal_primary: Optional[RecommendationItem] = None
    cavity_filler: Optional[RecommendationItem] = None
    secondary_cover: Optional[RecommendationItem] = None
    skin_protectant: Optional[RecommendationItem] = None
    alternative_options: List[RecommendationItem] = Field(default_factory=list)
    step_up_rx_option: Optional[RecommendationItem] = None
    active_contraindications: List[ClinicalContraindicationAlert] = Field(default_factory=list)
    clinical_guideline_citations: List[str] = Field(default_factory=list)
    change_protocol_summary: str = ""
