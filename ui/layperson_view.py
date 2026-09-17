"""
Layperson View (Patient & Caregiver Track)
Jargon-free perceptual triage and safe dressing guidance powered directly by the AWCare dataset.
"""

import streamlit as st
from data.awc_data_manager import get_awc_data_manager
from core.awc_rules_engine import evaluate_awc_query
from ui.components import render_product_card


def render_layperson_view():
    st.header("🩹 Patient & Caregiver Wound Care Guide")
    st.markdown(
        "Welcome. This tool helps you select safe, gentle bandages and protective dressings for non-emergency cuts, scrapes, "
        "burns, and skin sores from our clinical catalog."
    )

    dm = get_awc_data_manager()

    st.markdown("---")

    # Step 1: Safety & Emergency Triage Check
    st.subheader("Step 1: Emergency & Safety Check")
    st.info("Please check any statement below that applies to your wound:")

    col1, col2 = st.columns(2)
    with col1:
        fever = st.checkbox("🌡️ I have a fever, chills, or feel sick all over")
        spreading_red = st.checkbox("🔴 Redness is spreading fast around the wound (more than an inch)")
        bone_visible = st.checkbox("🦴 I can see white bone, shiny tendon, or deep tissues")
    with col2:
        gangrene = st.checkbox("⚫ Tissue is black, mushy, or has a strong bad smell")
        cold_limb = st.checkbox("❄️ Foot or leg is cold, pale/blue, numb, or very painful when lying down")
        diabetes_check = st.checkbox("🩺 I have diabetes and this is an open sore on my foot")

    duration_weeks = st.number_input("How many weeks has this wound been open?", min_value=0, max_value=52, value=0)

    # Emergency Hard Stop Check
    is_emergency = fever or spreading_red or bone_visible or gangrene or cold_limb
    is_urgent = diabetes_check or (duration_weeks >= 4)

    if is_emergency:
        st.markdown(
            """
            <div style="background-color: #fff0f0; border: 2px solid #dc3545; padding: 20px; border-radius: 8px; color: #721c24;">
                <h3 style="margin-top:0;">🚨 CRITICAL ALERT: IMMEDIATE MEDICAL EVALUATION REQUIRED</h3>
                <p><b>Your answers indicate warning signs of deep infection, severe circulation issue, or deep tissue involvement.</b></p>
                <p>Applying standard bandages at home without an in-person medical exam is unsafe. Please proceed immediately to the nearest <b>Emergency Room or Urgent Care Center</b>, or call <b>911</b>.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.error("❌ Product selection has been halted for your safety. Do NOT attempt self-treatment.")
        return

    if is_urgent:
        st.warning(
            "⚠️ **Doctor Evaluation Recommended:** Because this wound is linked to diabetes or has lasted over a month, "
            "it requires an in-person exam by a doctor or wound specialist. Below are safe dressings you can review with your clinician."
        )

    st.markdown("---")

    # Step 2: Perceptual Questionnaire
    st.subheader("Step 2: Describe Your Wound")

    colA, colB = st.columns(2)

    with colA:
        q_wound_type = st.selectbox(
            "What kind of wound is this?",
            [
                "Chronic Wound (Long-lasting sore or ulcer)",
                "Acute Wound (Fresh cut, scrape, or injury)",
                "Burn (First or second degree burn)",
                "Scar (Healing scar or surgical line)",
            ],
            index=0,
        )
        # Map to dataset Wound Type
        wound_type_mapped = "Chronic Wound"
        if "Acute" in q_wound_type: wound_type_mapped = "Acute Wound"
        elif "Burn" in q_wound_type: wound_type_mapped = "Burn"
        elif "Scar" in q_wound_type: wound_type_mapped = "Scar"

        # Offer specific common indications from dataset
        available_inds = ["All"] + dm.get_indications(wound_type_mapped)
        q_indication = st.selectbox("Can you be more specific about the sore type?", available_inds, index=0)

        # Show Indication image if available
        if q_indication != "All" and q_indication.lower() in dm.ind_images:
            st.image(dm.ind_images[q_indication.lower()], width=200, caption=f"Example: {q_indication}")

    with colB:
        q_drainage = st.radio(
            "How much fluid or drainage is coming from the wound?",
            [
                "Mild / Dry (Bandage stays mostly dry or clean for days)",
                "Moderate (Bandage pad gets damp or wet once a day)",
                "Heavy (Fluid leaks through the bandage multiple times a day)",
            ],
            index=1,
        )
        # Map to dataset Exudate Level
        exudate_mapped = "Moderate"
        if "Mild" in q_drainage: exudate_mapped = "Mild"
        elif "Heavy" in q_drainage: exudate_mapped = "Heavy"

        q_goal = st.selectbox(
            "What is your primary care need?",
            [
                "Moisture Balance (Keep wound clean, moist, and protected)",
                "Debridement (Gently soften dry, hard, or yellowish crust)",
                "Infection Control (Kill germs, control odor or redness)",
                "Support (Physical cushion, wrap, or scar care)",
            ],
            index=0,
        )
        # Map to dataset Application
        application_mapped = "Moisture Balance"
        if "Debridement" in q_goal: application_mapped = "Debridement"
        elif "Infection" in q_goal: application_mapped = "Infection Control"
        elif "Support" in q_goal: application_mapped = "Support"

    st.markdown("---")

    # Step 3: Dynamic Care Plan from Dataset
    st.subheader("Step 3: Recommended Dressings (Live Match)")

    result = evaluate_awc_query(
        wound_type=wound_type_mapped,
        indication=q_indication,
        exudate_level=exudate_mapped,
        application=application_mapped,
        dressing_type="All",
    )

    total = result["total_count"]
    if total == 0:
        st.warning("No exact matching dressings found for this specific combination. Showing general protective options from catalog.")
        fallback_res = dm.filter_products(wound_type=wound_type_mapped, exudate=exudate_mapped)
        for p in fallback_res[:2]:
            render_product_card(p, is_primary=True)
    else:
        st.success(f"✅ Found **{total}** matching dressing option(s) in our catalog for your condition.")

        # Show contraindications in clear plain language
        if result["contraindication_alerts"]:
            st.markdown("#### ⚠️ Important Safety Precautions for this Dressing:")
            for alert in result["contraindication_alerts"]:
                st.warning(f"**{alert['product_name']}:** {alert['warning']}")

        # Render Primary Matches
        if result["primary_matches"]:
            st.markdown("### 🏆 Top Recommended Bandages / Contact Dressings")
            for p in result["primary_matches"]:
                render_product_card(p, is_primary=True)

        # Render Secondary Matches
        if result["secondary_matches"]:
            st.markdown("### 🩹 Recommended Outer Cover / Secondary Dressings")
            for p in result["secondary_matches"]:
                render_product_card(p, is_primary=False)

        # Render others
        if not (result["primary_matches"] or result["secondary_matches"]) and result["all_matches"]:
            for p in result["all_matches"]:
                render_product_card(p, is_primary=True)

    with st.expander("ℹ️ General Dressing Application & Care Tips:"):
        st.markdown(
            """
            1. **Clean Hands:** Always wash your hands with soap and warm water before and after touching any bandage.
            2. **Gentle Cleansing:** Rinse the wound bed gently with sterile saline or mild drinking water before applying a new dressing.
            3. **Do Not Over-stretch:** Apply adhesive borders without pulling or stretching the skin.
            4. **When to Change:** Change the bandage whenever fluid leaks to the edge, or according to the wear time listed on the product card.
            5. **Watch for Infection:** If you notice spreading redness, increasing pain, or fever, contact your healthcare provider immediately.
            """
        )
