"""
Comparison View & Catalog Management (Data-Driven by Excel)
"""

import streamlit as st
import pandas as pd
from data.awc_data_manager import get_awc_data_manager


def render_comparison_view():
    st.header("📊 Product Explorer & Side-by-Side Comparator")
    st.markdown("Browse and compare your entire AWCare product catalog.")

    dm = get_awc_data_manager()

    c1, c2, c3 = st.columns(3)
    with c1:
        search_txt = st.text_input("🔍 Search by Brand or Keyword", "")
    with c2:
        cat_filter = st.selectbox("Wound Type", ["All"] + dm.get_wound_types())
    with c3:
        app_filter = st.selectbox("Application Goal", ["All"] + dm.get_applications())

    filtered_prods = dm.filter_products(
        wound_type=cat_filter,
        application=app_filter
    )

    if search_txt:
        q = search_txt.lower()
        filtered_prods = [
            p for p in filtered_prods if
            q in p.get("product_name", "").lower() or
            q in p.get("moc", "").lower() or
            q in p.get("key_features", "").lower() or
            q in p.get("description", "").lower()
        ]

    st.markdown(f"**Showing {len(filtered_prods)} product(s)**")

    # Extract clean product names for the multi-select
    prod_names = [p["product_name"] for p in filtered_prods]

    # Pre-select first 2 if available
    selected_names = st.multiselect(
        "Select up to 4 products for side-by-side comparison:",
        options=prod_names,
        default=prod_names[:2] if len(prod_names) >= 2 else prod_names
    )

    if selected_names:
        comp_prods = [p for p in filtered_prods if p["product_name"] in selected_names][:4]

        # Build visual comparison columns
        cols = st.columns(len(comp_prods))

        for idx, col in enumerate(cols):
            p = comp_prods[idx]
            with col:
                if p.get("image_url"):
                    st.image(p["image_url"], use_container_width=True)
                st.markdown(f"### {p['product_name']}")
                st.markdown(f"**Type:** {p.get('dressing_type', 'N/A')}")
                st.markdown(f"**Sizes:** {', '.join(p.get('sizes_available', []))}")
                st.markdown(f"**Material:** {p.get('moc', 'N/A')}")
                st.info(f"**Application:** {', '.join(p.get('applications', []))}")
                st.success(f"**Exudate:** {', '.join(p.get('exudate_levels', []))}")
                st.warning(f"**Freq:** {p.get('frequency', 'N/A')}")
                if p.get("contraindications") and str(p.get("contraindications")).strip().lower() != 'nan':
                    st.error(f"**Precautions:** {p['contraindications']}")

    st.markdown("---")
    st.subheader("Raw Dataset Preview")
    st.dataframe(dm.df_main, use_container_width=True)
