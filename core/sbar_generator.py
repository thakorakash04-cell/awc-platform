"""
SBAR (Situation, Background, Assessment, Request) Generator
Formats clinical data for triage hand-offs.
"""

def generate_sbar(situation: str, background: str, assessment_summary: str, recommendation: str) -> str:
    """Formats clinical information into the standardized SBAR structure."""
    return f"""
--------------------------------------------------
SBAR CLINICAL HANDOFF SUMMARY
--------------------------------------------------
SITUATION:
{situation}

BACKGROUND:
{background}

ASSESSMENT:
{assessment_summary}

RECOMMENDATION / REQUEST:
{recommendation}
--------------------------------------------------
"""
