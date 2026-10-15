"""Private, per-account, de-identified assessment records; no photo bytes stored."""
import json,re,time,uuid
from datetime import date

class WoundHistory:
    def __init__(self,store):
        self.store=store
        with store.transaction() as db:
            store.run(db,'''CREATE TABLE IF NOT EXISTS awc_wound_assessments (
                id TEXT PRIMARY KEY,owner TEXT NOT NULL,case_ref TEXT NOT NULL,
                created_at DOUBLE PRECISION NOT NULL,payload TEXT NOT NULL)''')
    @staticmethod
    def case_ref(value):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,50}',value):raise ValueError('Use a de-identified reference with 1–50 letters, numbers, underscores or hyphens.')
        return value
    def save(self,actor,case_ref,photos,clinical):
        case_ref=self.case_ref(case_ref)
        if not 1<=len(photos)<=3:raise ValueError('Save one to three reviewed photo observations.')
        # Explicit allow-list: image data, filenames, API keys and model text never persist.
        clean=[]
        for photo in photos:
            if date.fromisoformat(photo['captured_on'])>date.today():raise ValueError('Capture dates cannot be in the future.')
            area=photo.get('area_cm2')
            if area is not None and not 0<=float(area)<100000:raise ValueError('Invalid measured area.')
            colors={key:int(photo['colors'][key]) for key in ('granulation_red','slough_yellow','eschar_black','unclassified')}
            if any(v<0 or v>100 for v in colors.values()) or sum(colors.values())!=100:raise ValueError('Invalid colour observations.')
            clean.append({'captured_on':photo['captured_on'],'area_cm2':area,'colors':colors})
        clinical={key:str(clinical.get(key,''))[:150] for key in ('wound_type','exudate','goal','location','depth_assessed')}
        payload=json.dumps({'photos':clean,'clinical':clinical},allow_nan=False)
        with self.store.transaction() as db:
            self.store.require(db,actor,permission='use_tools')
            self.store.run(db,'INSERT INTO awc_wound_assessments(id,owner,case_ref,created_at,payload) VALUES(?,?,?,?,?)',
                (uuid.uuid4().hex,actor.username,case_ref,time.time(),payload))
            self.store._log(db,actor.username,'tool_use','Saved reviewed image assessment',actor.session_id)
    def records(self,actor,case_ref):
        case_ref=self.case_ref(case_ref)
        with self.store.transaction() as db:
            self.store.require(db,actor,permission='use_tools')
            rows=self.store.run(db,'SELECT created_at,payload FROM awc_wound_assessments WHERE owner=? AND case_ref=? ORDER BY created_at DESC LIMIT 50',(actor.username,case_ref)).fetchall()
        return [{'saved_at':r['created_at'],**json.loads(r['payload'])} for r in rows]
