from unittest.mock import Mock,patch
import pytest
from PIL import Image
from vision.vision_model import provider_error,check_connection,describe_photo,DEFAULT_MODEL

@pytest.mark.parametrize('status,expected',[(400,'HTTP 400'),(401,'API key'),(402,'billing'),(403,'HTTP 403'),(404,'WOUND_VISION_MODEL'),(429,'quota'),(503,'temporarily unavailable')])
def test_errors_are_actionable_and_never_echo_provider_payload(status,expected):
    response=Mock(status_code=status);response.json.return_value={'error':{'message':'private-key private-image-data'}}
    message=provider_error(response)
    assert expected in message
    assert 'private-key' not in message and 'private-image-data' not in message

def test_invalid_key_reason_and_leaked_key():
    response=Mock(status_code=400)
    response.json.return_value={'error':{'details':[{'reason':'API_KEY_INVALID'}]}}
    assert 'rejected the API key' in provider_error(response)
    response.json.return_value={'error':{'message':'Your API key was reported as leaked. PRIVATE'}}
    assert 'blocked this API key' in provider_error(response)

def test_non_json_bad_request_is_handled():
    response=Mock(status_code=400);response.json.side_effect=ValueError()
    assert 'HTTP 400' in provider_error(response)

def test_connection_check_uses_server_key_without_sending_photos():
    with patch('vision.vision_model.requests.get') as get,patch('vision.vision_model.requests.post') as post:
        get.return_value=Mock(status_code=200)
        get.return_value.json.return_value={'supportedGenerationMethods':['generateContent']}
        assert check_connection('private-key','models/'+DEFAULT_MODEL)==DEFAULT_MODEL
        assert get.call_args.kwargs['headers']['x-goog-api-key']=='private-key'
        assert 'private-key' not in get.call_args.args[0]
        assert 'json' not in get.call_args.kwargs
        post.assert_not_called()

def test_generation_uses_compatible_settings_and_preserves_quota_error():
    with patch('vision.vision_model.requests.post') as post:
        post.return_value=Mock(status_code=429)
        post.return_value.json.return_value={'error':{'message':'Quota exceeded'}}
        with pytest.raises(ValueError,match='quota'):describe_photo(Image.new('RGB',(20,20)),'key','models/'+DEFAULT_MODEL,consent=True)
        config=post.call_args.kwargs['json']['generationConfig']
        assert 'temperature' not in config and config['responseSchema']
        assert post.call_count==1
