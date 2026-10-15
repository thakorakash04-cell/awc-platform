import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from workspace_store import Store

class WorkspaceUITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.url='sqlite:///'+str(Path(self.tmp.name)/'ui.db')
        self.env=patch.dict(os.environ,{'DATABASE_URL':self.url,'ADMIN_USERNAME':'admin_user','ADMIN_PASSWORD':'Test-only-admin-password!123'})
        self.env.start()
        self.store=Store(self.url);self.store.bootstrap_admin('admin_user','Test-only-admin-password!123')
        self.admin=self.store.login('admin_user','Test-only-admin-password!123')
        self.store.create_viewer(self.admin,'viewer_user','Test-only-viewer-password!123')
    def tearDown(self):
        self.env.stop();self.tmp.cleanup()
    def signed_in(self,username,password):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
        self.assertEqual(len(at.exception),0)
        self.assertFalse(at.get('component_instance'))
        at.text_input(key='login_username').set_value(username)
        at.text_input(key='login_password').set_value(password)
        at.button[0].click().run()
        self.assertEqual(len(at.exception),0)
        return at
    def test_viewer_has_no_management_or_downloads(self):
        at=self.signed_in('viewer_user','Test-only-viewer-password!123')
        self.assertFalse(any(t.label=='Manage users' for t in at.toggle))
        self.assertEqual(len(at.get('download_button')),0)
        self.assertEqual(len(at.get('file_uploader')),0)
        self.assertEqual(len(at.get('data_editor')),0)
    def test_admin_manage_users_and_revocation(self):
        at=self.signed_in('admin_user','Test-only-admin-password!123')
        at.toggle(key='workspace_users').set_value(True).run()
        self.assertEqual(len(at.exception),0)
        self.assertTrue(any(t.label=='New viewer username' for t in at.text_input))
        self.store.bootstrap_admin('admin_user','Rotated-password!123')
        at.run()
        self.assertTrue(any(t.label=='Username' for t in at.text_input))

    def test_login_blocks_all_tracks_until_authenticated(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
        self.assertEqual(len(at.radio),0)
        at.text_input(key='login_username').set_value('viewer_user')
        at.text_input(key='login_password').set_value('wrong-password')
        at.button[0].click().run()
        self.assertEqual(len(at.radio),0)
        self.assertTrue(at.error)

    def test_viewer_can_use_existing_tracks_and_sign_out(self):
        at=self.signed_in('viewer_user','Test-only-viewer-password!123')
        tracks=list(at.sidebar.radio[0].options)
        for track in tracks:
            at.sidebar.radio[0].set_value(track).run()
            self.assertEqual(len(at.exception),0)
        at.button(key='workspace_signout').click().run()
        self.assertEqual(len(at.radio),0)
        self.assertTrue(any(x.label=='Username' for x in at.text_input))

if __name__=='__main__':unittest.main()
