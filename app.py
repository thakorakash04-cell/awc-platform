"""
Advanced Wound Care (AWC) Decision Support & Product Selection Application
Main Entry Point
"""

import streamlit as st
from workspace_auth import require_workspace


def main():
    st.set_page_config(
        page_title="Advanced Wound Care Decision Support Tool",
        page_icon="🩹",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Authenticate before loading or rendering any AWC workspace.
    st.markdown("""<style>
        [data-testid='stAppViewContainer']{background:#F4F6F8}
        h1,h2,h3{color:#285e4c}
        button[kind='primary']{background:#258467;border-color:#258467;color:white}
        .block-container{padding-top:2rem}
    </style>""", unsafe_allow_html=True)
    require_workspace()

    from ui.styles import apply_clinical_theme
    from ui.layperson_view import render_layperson_view
    from ui.clinician_view import render_clinician_view
    from ui.comparison_view import render_comparison_view
    from ui.image_analysis_view import render_image_analysis_view

    # Apply clinical CSS styles
    apply_clinical_theme()

    # Sidebar Navigation & Track Selector
    st.sidebar.title("🩹 AWC Decision Support")
    st.sidebar.caption("Evidence-Based Clinical Decision Support & Triage")

    track_choice = st.sidebar.radio(
        "Select User Experience Track:",
        [
            "🩺 Clinician Workspace (CDS)",
            "🩹 Patient & Caregiver Guide",
            "📷 Assistive Image Analysis (HITL)",
            "📊 Product Catalog & Comparator",
            "ℹ️ Clinical Guidelines & Architecture",
        ],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **🛡️ Clinical Safety Core:**
        - FDA Non-Device CDS Compliant (§ 520(o))
        - IEC 62366-1 Usability & Safety Matrix
        - WOCN / EWMA / IWII Guidelines
        - Poka-Yoke Contraindication Interlocks
        """
    )
    st.sidebar.caption("v1.0.0 | Phased Bifurcated Architecture")

    # Render Chosen View
    if track_choice == "🩺 Clinician Workspace (CDS)":
        render_clinician_view()
    elif track_choice == "🩹 Patient & Caregiver Guide":
        render_layperson_view()
    elif track_choice == "📷 Assistive Image Analysis (HITL)":
        render_image_analysis_view()
    elif track_choice == "📊 Product Catalog & Comparator":
        render_comparison_view()
    elif track_choice == "ℹ️ Clinical Guidelines & Architecture":
        render_documentation_view()


def render_documentation_view():
    st.header("ℹ️ Clinical Architecture & Decision Guidelines")
    st.markdown(
        """
        ### System Architecture & Regulatory Governance
        This application implements a **Bifurcated Dual-Track Architecture** designed to balance patient safety with professional clinical decision support:

        1. **Clinician Track (Clinical Decision Support):**
           - Gated by NPI / professional credentials.
           - Integrates full 12-parameter clinical matrix: Etiology, Vascular status (ABPI), TIME framework, 3D Cavity measurements, Bioburden grading, and Periwound skin integrity.
           - Provides transparent clinical citations and rationale, qualifying as **FDA Non-Device CDS** under Section 520(o)(1)(E) of the FD&C Act.
           - Incorporates **Medicare Part B Surgical Dressing LCD L33331** HCPCS billing codes and allowable quantity limits.

        2. **Layperson Track (Patient & Caregiver Triage):**
           - Free from confusing medical jargon; utilizes visual and everyday perceptual anchors.
           - Mandates an interruptive **Red-Flag Emergency Circuit Breaker** before product browsing.
           - Restricts recommendations to safe Over-the-Counter (OTC) barrier films and gentle silicone foams.

        3. **Assistive Computer Vision (HITL Mode):**
           - Implements pre-flight Image Quality Assessment (IQA) checking for blur, glare, and illumination.
           - Provides color-space RYB tissue segmentation (Granulation, Slough, Eschar).
           - Enforces **Human-in-the-Loop (HITL)** verification; raw AI predictions never directly prescribe dressings.

        4. **Poka-Yoke Safety Interlocks:**
           - Strictly blocks multi-layer compression on ischemic limbs (ABPI < 0.8).
           - Strictly blocks occlusive hydrocolloids and films on infected wounds.
           - Prevents desiccation from alginates on dry wound beds.
           - Prevents enzymatic debrider (Santyl) deactivation by heavy metal silver.
        """
    )


if __name__ == "__main__":
    main()
