"""
Clinical UX Styles & Theme
"""

def apply_clinical_theme():
    import streamlit as st
    st.markdown("""
        <style>
            .stApp {
                background-color: #f8f9fa;
            }
            .css-1544g2n {
                color: #2c3e50;
            }
            .stButton>button {
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }
            .red-flag-box {
                background-color: #fff0f0;
                border: 2px solid #dc3545;
                padding: 15px;
                border-radius: 5px;
                color: #721c24;
            }
            .contraindication-box {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 10px;
                border-radius: 5px;
                color: #856404;
            }
        </style>
    """, unsafe_allow_html=True)
