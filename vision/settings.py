"""Resolve server-side Gemini configuration without exposing credentials to widgets."""
import os
from collections.abc import Mapping
import streamlit as st
from .vision_model import DEFAULT_MODEL

def load_vision_settings():
    try:settings=dict(st.secrets)
    except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):settings={}
    nested=settings.get('gemini',{})
    if not isinstance(nested,Mapping):nested={}
    def clean(value):return value.strip() if isinstance(value,str) else ''
    key=next((value for value in map(clean,[settings.get('GEMINI_API_KEY'),settings.get('GOOGLE_API_KEY'),nested.get('api_key'),os.getenv('GEMINI_API_KEY'),os.getenv('GOOGLE_API_KEY')]) if value),'')
    model=clean(settings.get('WOUND_VISION_MODEL')) or clean(nested.get('model')) or clean(os.getenv('WOUND_VISION_MODEL')) or DEFAULT_MODEL
    return key,model
