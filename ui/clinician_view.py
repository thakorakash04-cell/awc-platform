"""
Advanced Clinician View (Powered by strictly filtered custom AWC dataset)
"""

import streamlit as st
from data.awc_data_manager import get_awc_data_manager
from core.awc_rules_engine import evaluate_awc_query
from ui.components import render_product_card


def render_clinician_view():
    st.header("🩺 Advanced Wound Care Decision Support (Clinician Workspace)")
    st.markdown("Dynamic product engine directly connected to your standardized clinical formulary.")

    dm = get_awc_data_manager()

    with st.expander("👤 Clinician Authentication & Practice Settings", expanded=False):
        c_npi, c_role = st.columns(2)
        with c_npi:
            npi_val = st.text_input("National Provider Identifier (NPI) / License #", "1942857102")
        with c_role:
            role_val = st.selectbox("Specialty / Clinical Role", ["WOCN / Wound Specialist", "MD / DO", "DPM (Podiatry)", "Nurse Practitioner / PA", "Physical Therapist"])

    st.markdown("---")

    # Assessment Form Matrix
    st.subheader("📋 Comprehensive Wound Assessment Matrix")

    # Pre-fetch dropdown options from dataset
    all_wound_types = ["All"] + dm.get_wound_types()
    all_exudate = ["All"] + dm.get_exudate_levels()
    all_applications = ["All"] + dm.get_applications()
    all_phases = ["All"] + dm.get_healing_phases()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### A. Etiology & Indications")
        wound_type = st.selectbox("Wound Type", options=all_wound_types, index=0)

        # Dynamically filter indications based on Selected Wound Type
        available_indications = ["All"] + dm.get_indications(wound_type)
        indication = st.selectbox("Specific Indication (AWC)", options=available_indications, index=0)

        # Highlight if Indication has an image linked
        if indication != "All" and indication.lower() in dm.ind_images:
            st.image(dm.ind_images[indication.lower()], width=200, caption=f"Typical {indication}")

    with col2:
        st.markdown("#### B. Exudate & Clinical Goal")
        exudate = st.selectbox("Exudate Level", options=all_exudate, index=0)
        application = st.selectbox("Primary Clinical Goal (Application)", options=all_applications, index=0)

    with col3:
        st.markdown("#### C. Additional Guardrails")
        healing_phase = st.selectbox("Healing Phase", options=all_phases, index=0)
        dressing_type = st.selectbox("Dressing Type", ["All", "Primary", "Secondary"], index=0)

    # Red Flag Checkbox
    st.markdown("---")
    st.markdown("#### 🚨 Emergency Safety Interlocks")
    c_emerg1, c_emerg2 = st.columns(2)
    with c_emerg1:
        emerg_bone = st.checkbox("Visibly exposed bone, deep tendon, or surgical hardware")
        emerg_sepsis = st.checkbox("Systemic fever, rigors, or rapidly spreading cellulitis (>2cm)")
    with c_emerg2:
        emerg_ischemia = st.checkbox("Severe Critical Limb Ischemia (ABPI < 0.5, cold/pale foot)")

    has_emergency = emerg_bone or emerg_sepsis or emerg_ischemia
    emerg_reason = ""
    if emerg_bone: emerg_reason += "Exposed deep structures (Osteomyelitis risk). "
    if emerg_sepsis: emerg_reason += "Systemic sepsis / spreading infection. "
    if emerg_ischemia: emerg_reason += "Critical Limb Ischemia. "

    st.markdown("---")
    st.subheader("💡 Tailored Clinical Care Plan (Live Update)")

    # Run Clinical Decision Engine automatically!
    result = evaluate_awc_query(
        wound_type=wound_type,
        indication=indication,
        exudate_level=exudate,
        application=application,
        dressing_type=dressing_type,
        healing_phase=healing_phase,
        has_emergency_flags=has_emergency,
        emergency_reason=emerg_reason,
    )

    if result["is_emergency"]:
        st.error(f"🚨 **CRITICAL EMERGENCY HARD STOP TRIGGERED**\n\n**Reason:** {result['emergency_reason']}\n\nDo not proceed with autonomous dressing selection. Immediate physician evaluation and ER/Specialist referral is mandatory.")
        return

    total = result["total_count"]
    if total == 0:
        st.warning("⚠️ No exact products found matching these specific parameters in your dataset. Try relaxing your filters (e.g., set 'Dressing Type' or 'Healing Phase' to 'All').")
        return
    else:
        if result["fallback_used"]:
            st.info(f"✅ Found {total} products (exact matches were too strict, so 'Application' or 'Dressing Type' filters were relaxed).")
        else:
            st.success(f"✅ Found {total} perfectly matched product(s) in your formulary.")

        # Render Contraindications upfront
        if result["contraindication_alerts"]:
            st.error("#### 🛡️ Patient Safety Alerts from Selected Products")
            for alert in result["contraindication_alerts"]:
                st.markdown(f"- **{alert['product_name']}:** {alert['warning']}")

        # Render Primary Matches
        if result["primary_matches"]:
            st.markdown("### 🥇 Primary Wound Dressings")
            for p in result["primary_matches"]:
                render_product_card(p, is_primary=True)

        # Render Secondary Matches
        if result["secondary_matches"]:
            st.markdown("### 🥈 Secondary / Cover Dressings")
            for p in result["secondary_matches"]:
                render_product_card(p, is_primary=False)

        # Render Unknown/Other Matches (if they lack "Primary"/"Secondary" designation)
        if result.get("all_matches") and not (result["primary_matches"] or result["secondary_matches"]):
            for p in result["all_matches"]:
                render_product_card(p, is_primary=False)
