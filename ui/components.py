"""
Reusable UI Components for displaying AWC Products
"""

import streamlit as st
from typing import Dict, Any


def render_product_card(product: Dict[str, Any], is_primary: bool = False):
    """Renders a rich product card using metadata and images from the user's dataset."""

    border_color = "#28a745" if is_primary else "#007bff"
    badge_label = "🌟 Primary Match" if is_primary else "✅ Matching Product"

    st.markdown(
        f"""
        <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 20px; background-color: white; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h3 style="margin-top: 0; color: #333;">{product['product_name']} <span style="font-size: 14px; background-color: {border_color}; color: white; padding: 4px 8px; border-radius: 20px; vertical-align: middle;">{badge_label}</span></h3>
            </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 2.5])

    with col1:
        if product.get('image_url'):
            st.image(product['image_url'], use_container_width=True)
        else:
            st.info("No Product Image Provided")

    with col2:
        st.markdown(f"**Type of Dressing:** {product.get('dressing_type', 'N/A')}")
        st.markdown(f"**Material / Components:** {product.get('moc', 'N/A')}")
        st.markdown(f"**Description:** {product.get('description', 'N/A')}")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 📏 Specifications")
        st.markdown(f"**Available Sizes:** {', '.join([str(x) for x in product.get('sizes_available', [])]) or 'N/A'}")
        st.markdown(f"**Absorbency:** {product.get('absorbency', 'N/A')}")
        st.markdown(f"**Hydration:** {product.get('hydration', 'N/A')}")
        st.markdown(f"**Sterilization:** {product.get('sterilization', 'N/A')}")

    with c2:
        st.markdown("#### ⏱️ Clinical Protocol")
        st.markdown(f"**Healing Phase:** {product.get('healing_phase', 'N/A')}")
        st.markdown(f"**Application / Goal:** {', '.join([str(x) for x in product.get('applications', [])])}")
        st.markdown(f"**Change Frequency:** {product.get('frequency', 'N/A')}")
        st.markdown(f"**Max Wear Time:** {product.get('wear_time', 'N/A')}")

    with c3:
        st.markdown("#### 🎯 Clinical Indications")
        st.markdown(f"**Wound Types:** {', '.join([str(x) for x in product.get('wound_types', [])])}")
        # Fix: Convert list items to string before join to avoid float errors
        exudate_list = product.get('exudate_levels', [])
        if not isinstance(exudate_list, list):
            exudate_list = [exudate_list]
        st.markdown(f"**Exudate Levels:** {', '.join([str(x) for x in exudate_list if x is not None])}")

        inds = product.get('indications', [])
        if len(inds) > 3:
            st.markdown(f"**Indications:** {', '.join(inds[:3])} (+{len(inds)-3} more)")
        else:
            st.markdown(f"**Indications:** {', '.join(inds)}")

    if product.get('key_features'):
        st.markdown(f"**✨ Key Features:** {product['key_features'].replace('','')}")

    if product.get('contraindications') and str(product.get('contraindications')).strip().lower() != 'nan':
        st.markdown(
            f"""
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin-top: 15px; border-radius: 4px;">
                <b style="color: #856404;">⚠️ Contra-indications & Precautions:</b><br>
                {product['contraindications']}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
