from unittest.mock import patch
from vision.settings import load_vision_settings

def test_streamlit_secrets_override_environment_and_trim_key():
    with patch('vision.settings.st.secrets',{'GEMINI_API_KEY':'  private-secret  ','WOUND_VISION_MODEL':'custom-model'}),patch.dict('os.environ',{'GEMINI_API_KEY':'env-key'}):
        assert load_vision_settings()==('private-secret','custom-model')

def test_google_and_nested_secret_aliases():
    for settings in [{'GOOGLE_API_KEY':'alias-key'},{'gemini':{'api_key':'alias-key'}}]:
        with patch('vision.settings.st.secrets',settings),patch.dict('os.environ',{},clear=True):
            assert load_vision_settings()[0]=='alias-key'

def test_missing_key_keeps_local_analysis_available():
    with patch('vision.settings.st.secrets',{}),patch.dict('os.environ',{},clear=True):
        assert load_vision_settings()[0]==''
