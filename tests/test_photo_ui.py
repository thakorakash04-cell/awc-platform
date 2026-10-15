import io,os,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
from streamlit.testing.v1 import AppTest
import streamlit as st
from workspace_store import Store

def test_photo_review_is_required_and_red_flags_block_matching():
    with tempfile.TemporaryDirectory() as folder:
        url='sqlite:///'+str(Path(folder)/'photo-ui.db')
        with patch.dict(os.environ,{'DATABASE_URL':url,'ADMIN_USERNAME':'admin_user','ADMIN_PASSWORD':'Initial-admin-password!123'}):
            store=Store(url);store.bootstrap_admin('admin_user','Initial-admin-password!123')
            at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30)
            at.secrets.update({'GEMINI_API_KEY':'test-server-secret','DATABASE_URL':url,'ADMIN_USERNAME':'admin_user','ADMIN_PASSWORD':'Initial-admin-password!123'})
            at.run();at.text_input(key='login_username').set_value('admin_user');at.text_input(key='login_password').set_value('Initial-admin-password!123')
            next(b for b in at.button if b.label=='Sign in').click().run()
            arr=np.random.default_rng(42).integers(50,200,(500,500,3),dtype=np.uint8)
            raw=io.BytesIO();Image.fromarray(arr).save(raw,format='PNG')
            uploads=lambda label,**kwargs:raw if label=='Upload photo 1' else None
            with patch('streamlit.file_uploader',side_effect=uploads):
                at.sidebar.radio[0].set_value('📷 Assistive Image Analysis (HITL)').run()
                assert not at.exception
                next(c for c in at.checkbox if c.label.startswith('This crop')).set_value(True).run()
                assert not at.exception
                assert any('API key loaded from server settings' in message.value for message in at.success)
                assert not any('API key' in field.label for field in at.text_input)
                next(c for c in at.checkbox if c.label.startswith('I am authorised')).set_value(True).run()
                with patch('ui.image_analysis_view.describe_photo',return_value={'description':'Visible colours only','visible_colors':['red'],'limitations':[],'wound_visible':True}) as describe:
                    next(b for b in at.button if b.label=='Describe latest crop with AI').click().run()
                    assert describe.call_args.args[1]=='test-server-secret'
                    assert describe.call_args.kwargs['consent'] is True
                assert all('test-server-secret' not in str(element.proto) for element in at if hasattr(element,'proto'))
                match=lambda:next(b for b in at.button if b.label=='Match confirmed findings to products')
                # Before the required clinical assessment, matching is not rendered.
                assert not any(b.label=='Match confirmed findings to products' for b in at.button)
                next(r for r in at.radio if r.label=='Depth / cavity assessment').set_value('Superficial — assessed in person')
                next(r for r in at.radio if r.label=='Infection and vascular assessment').set_value('Assessed: no identified concern requiring specialist review').run()
                for label in ['Anatomical location','Assessed wound type','Assessed exudate level','Clinician-selected goal']:
                    widget=next(s for s in at.selectbox if s.label==label);widget.set_value(widget.options[1])
                at.run();assert match().disabled
                next(c for c in at.checkbox if c.label.startswith('A clinician')).set_value(True).run()
                assert not match().disabled
                with patch('ui.image_analysis_view.evaluate_awc_query',return_value={'all_matches':[],'total_count':0}) as query:
                    match().click().run();query.assert_called_once();assert query.call_args.kwargs['allow_fallback'] is False
                # Changing clinical findings resets the review confirmation.
                widget=next(s for s in at.selectbox if s.label=='Assessed wound type')
                if len(widget.options)>2:
                    widget.set_value(widget.options[2]).run();assert match().disabled
                at.checkbox(key='photo_emergency').set_value(True).run()
                assert any('Urgent in-person' in e.value for e in at.error)
                assert not any(b.label=='Match confirmed findings to products' for b in at.button)
            st.cache_resource.clear()
