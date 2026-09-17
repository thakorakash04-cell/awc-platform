"""
Image Analysis & Human-in-the-Loop (HITL) Verification View
Assists in parameter estimation with IQA gates and interactive mask inspection connected to the AWCare dataset.
"""

import streamlit as st
from PIL import Image
from vision.iqa_gate import evaluate_image_quality
from vision.tissue_segmentation import segment_wound_tissue
from data.awc_data_manager import get_awc_data_manager
from core.awc_rules_engine import evaluate_awc_query
from ui.components import render_product_card


def render_image_analysis_view():
    st.header("📷 Assistive Wound Image Analysis (HITL Mode)")
    st.caption("Human-in-the-Loop Computer Vision Pipeline connecting to the AWCare Formulary")

    dm = get_awc_data_manager()

    st.markdown(
        """
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin-bottom: 20px; border-radius: 4px;">
            <b>⚠️ MANDATORY CLINICAL SAFETY NOTICE:</b><br>
            Computer vision from smartphone photos <i>cannot</i> detect microscopic bacterial biofilms,
            cannot perceive 3D cavity depth/tunneling, and can misread erythema on darker skin tones (Fitzpatrick IV–VI).
            Extracted visual metrics are <b>assistive suggestions only</b> and require manual verification.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_img = st.file_uploader("Upload or take a photo of the wound", type=["jpg", "jpeg", "png"])

    if uploaded_img is not None:
        try:
            image = Image.open(uploaded_img)

            # Step 1: Pre-flight Image Quality Assessment
            iqa = evaluate_image_quality(image)

            st.subheader("1. Image Quality Assessment (IQA Gate)")
            col_iqa1, col_iqa2, col_iqa3 = st.columns(3)
            with col_iqa1:
                st.metric("Sharpness Score", f"{iqa['sharpness_score']:.1f}", delta="Sharp" if iqa['sharpness_score'] >= 40 else "Blurry")
            with col_iqa2:
                st.metric("Mean Luminance", f"{iqa['mean_luminance']:.1f}", delta="Adequate" if 40 <= iqa['mean_luminance'] <= 220 else "Poor Light")
            with col_iqa3:
                st.metric("Specular Glare", f"{iqa['glare_ratio_pct']:.1f}%", delta="Low Glare" if iqa['glare_ratio_pct'] < 8.0 else "High Glare", delta_color="inverse")

            if not iqa["passed"]:
                st.error("❌ **Image Quality Rejected:**")
                for r in iqa["rejection_reasons"]:
                    st.write(f"- {r}")
                st.info(f"💡 **Guidance:** {iqa['guidance']}")
                st.warning("Please upload a clearer image, or proceed directly to the manual Clinician or Patient tabs.")
                return

            st.success("✅ **Image Quality Passed:** Illumination and focus are suitable for assistive feature analysis.")

            # Step 2: Semantic Segmentation
            st.markdown("---")
            st.subheader("2. Visual RYB Tissue Segmentation")

            percentages, overlay_img = segment_wound_tissue(image)

            c_img1, c_img2 = st.columns(2)
            with c_img1:
                st.image(image, caption="Original Wound Photo", use_container_width=True)
            with c_img2:
                st.image(overlay_img, caption="Segmented Overlay (Red: Granulation | Yellow: Slough | Black: Eschar)", use_container_width=True)

            # Metrics
            st.markdown("##### Extracted Tissue Composition:")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("🔴 Granulation (Viable)", f"{percentages['granulation_red']}%")
            with m2:
                st.metric("🟡 Slough (Non-viable)", f"{percentages['slough_yellow']}%")
            with m3:
                st.metric("⚫ Eschar (Necrotic)", f"{percentages['eschar_black']}%")

            # Step 3: Human-in-the-Loop Confirmation
            st.markdown("---")
            st.subheader("3. Human-in-the-Loop (HITL) Parameter Confirmation")
            st.markdown("Review and confirm parameters from your dataset before generating recommendations:")

            # Heuristic suggestions
            suggested_exudate = "Moderate"
            if percentages['slough_yellow'] > 30: suggested_exudate = "Heavy"
            elif percentages['eschar_black'] > 40: suggested_exudate = "Mild"

            suggested_app = "Moisture Balance"
            if percentages['slough_yellow'] > 40 or percentages['eschar_black'] > 30:
                suggested_app = "Debridement"

            all_wtypes = ["All"] + dm.get_wound_types()
            all_ex = ["All"] + dm.get_exudate_levels()
            all_apps = ["All"] + dm.get_applications()

            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                conf_wtype = st.selectbox("Confirm Wound Type", all_wtypes, index=0)
            with h_col2:
                ex_idx = all_ex.index(suggested_exudate) if suggested_exudate in all_ex else 0
                conf_exudate = st.selectbox("Confirm Exudate Level", all_ex, index=ex_idx)
            with h_col3:
                app_idx = all_apps.index(suggested_app) if suggested_app in all_apps else 0
                conf_app = st.selectbox("Confirm Clinical Goal", all_apps, index=app_idx)

            st.markdown("---")
            st.subheader("💡 Matching Product Recommendations")

            result = evaluate_awc_query(
                wound_type=conf_wtype,
                exudate_level=conf_exudate,
                application=conf_app,
                dressing_type="All"
            )

            total = result["total_count"]
            if total == 0:
                st.warning("No matching products found in dataset for this specific combination. Try relaxing filters.")
            else:
                st.success(f"✅ Found **{total}** matching product(s) in your formulary.")

                if result["primary_matches"]:
                    st.markdown("### 🥇 Primary Wound Dressings")
                    for p in result["primary_matches"]:
                        render_product_card(p, is_primary=True)

                if result["secondary_matches"]:
                    st.markdown("### 🥈 Secondary Dressings")
                    for p in result["secondary_matches"]:
                        render_product_card(p, is_primary=False)

                if not (result["primary_matches"] or result["secondary_matches"]) and result["all_matches"]:
                    for p in result["all_matches"]:
                        render_product_card(p, is_primary=False)

        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
