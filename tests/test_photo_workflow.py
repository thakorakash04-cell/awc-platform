import io,json,tempfile
from datetime import date,timedelta
from unittest.mock import Mock,patch
from pathlib import Path
import numpy as np
from PIL import Image
import pytest
from vision.tissue_segmentation import segment_wound_tissue
from vision.photo_workflow import prepare_photo,crop_photo,compare_measured_areas
from vision.vision_model import describe_photo
from workspace_store import Store,AccessDenied
from data.wound_history import WoundHistory

def test_unclassified_pixels_are_not_fabricated_as_red_tissue():
    result,_=segment_wound_tissue(Image.new('RGB',(100,100),(100,100,150)))
    assert result['unclassified']==100 and result['granulation_red']==0
    assert sum(result.values())==100

def test_color_observations_use_the_full_crop_and_preserve_pixels():
    arr=np.zeros((100,100,3),dtype=np.uint8);arr[:50]=[180,30,40];arr[50:]=[100,100,150]
    image=Image.fromarray(arr);result,overlay=segment_wound_tissue(image)
    assert result['granulation_red']==50 and result['unclassified']==50
    assert np.array_equal(np.asarray(image),arr) and overlay.size==image.size

def test_decoder_crop_orientation_and_size_limits():
    image=Image.new('RGB',(400,600),(100,100,100));buf=io.BytesIO();image.save(buf,format='JPEG',exif=Image.Exif())
    clean=prepare_photo(buf.getvalue());assert not clean.getexif()
    assert crop_photo(clean,(0,50),(0,50)).size==(200,300)
    with pytest.raises(ValueError):crop_photo(clean,(20,20),(0,100))
    with pytest.raises(ValueError):prepare_photo(b'not an image')
    buf=io.BytesIO();image.save(buf,format='GIF')
    with pytest.raises(ValueError):prepare_photo(buf.getvalue())

def test_comparison_requires_dates_and_clinical_area():
    first=(date.today()-timedelta(days=7)).isoformat();last=date.today().isoformat()
    assert compare_measured_areas([{'captured_on':first,'area_cm2':None},{'captured_on':last,'area_cm2':None}]) is None
    assert compare_measured_areas([{'captured_on':first,'area_cm2':10},{'captured_on':last,'area_cm2':8}])['reduction_percent']==20
    assert compare_measured_areas([{'captured_on':first,'area_cm2':10},{'captured_on':last,'area_cm2':0}])['reduction_percent']==100
    with pytest.raises(ValueError):compare_measured_areas([{'captured_on':last},{'captured_on':first}])
    with pytest.raises(ValueError):compare_measured_areas([{'captured_on':first,'area_cm2':0},{'captured_on':last,'area_cm2':8}])

def test_ai_requires_consent_and_sends_metadata_free_image_with_key_in_header():
    image=Image.new('RGB',(400,400),(150,80,70))
    with patch('vision.vision_model.requests.post') as post:
        with pytest.raises(ValueError):describe_photo(image,'private-key',consent=False)
        post.assert_not_called()
        note={'wound_visible':True,'description':'Red and yellow visible areas.','visible_colors':['red','yellow'],'limitations':['Lighting affects colour.']}
        post.return_value=Mock(status_code=200)
        post.return_value.json.return_value={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(note)}]}}]}
        assert describe_photo(image,'private-key',consent=True)==note
        args,kwargs=post.call_args
        assert 'private-key' not in args[0] and kwargs['headers']['x-goog-api-key']=='private-key'
        assert len(kwargs['json']['contents'][0]['parts'])==2

def test_ai_rejects_diagnosis_fields_and_blocked_or_incomplete_responses():
    image=Image.new('RGB',(300,300))
    with patch('vision.vision_model.requests.post') as post:
        post.return_value=Mock(status_code=200)
        post.return_value.json.return_value={'candidates':[]}
        with pytest.raises(ValueError):describe_photo(image,'key',consent=True)
        post.return_value.json.return_value={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'wound_visible':True,'description':'x','visible_colors':[],'limitations':[],'diagnosis':'forbidden'})}]}}]}
        with pytest.raises(ValueError):describe_photo(image,'key',consent=True)
        post.return_value=Mock(status_code=401)
        with pytest.raises(ValueError,match='API key'):describe_photo(image,'key',consent=True)

def test_history_is_private_permission_checked_and_does_not_save_images():
    with tempfile.TemporaryDirectory() as folder:
        store=Store('sqlite:///'+str(Path(folder)/'history.db'));store.bootstrap_admin('admin_user','Initial-admin-password!123')
        admin=store.login('admin_user','Initial-admin-password!123')
        store.create_viewer(admin,'viewer_user','Initial-viewer-password!123');viewer=store.login('viewer_user','Initial-viewer-password!123')
        history=WoundHistory(store)
        photo={'captured_on':date.today().isoformat(),'area_cm2':2,'colors':{'granulation_red':20,'slough_yellow':20,'eschar_black':10,'unclassified':50},'image':b'PRIVATE_IMAGE','api_key':'PRIVATE_KEY'}
        history.save(viewer,'case_A',[photo],{'wound_type':'Reviewed type'})
        records=WoundHistory(Store(store.url)).records(viewer,'case_A')
        assert len(records)==1 and 'PRIVATE' not in json.dumps(records)
        assert history.records(admin,'case_A')==[]
        store.update_permissions(admin,'viewer_user',{'use_tools':False})
        viewer=store.login('viewer_user','Initial-viewer-password!123')
        with pytest.raises(AccessDenied):history.save(viewer,'case_A',[photo],{})

def test_strict_formulary_matching_never_relaxes_clinical_goal():
    from core.awc_rules_engine import evaluate_awc_query
    dm=Mock();dm.filter_products.return_value=[]
    with patch('core.awc_rules_engine.get_awc_data_manager',return_value=dm):
        result=evaluate_awc_query(wound_type='Assessed type',exudate_level='Mild',application='Specific goal',allow_fallback=False)
    assert result['total_count']==0 and not result['fallback_used'] and dm.filter_products.call_count==1
