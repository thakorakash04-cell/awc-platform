"""Fail a build when bundled clinical records no longer match the source workbook."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from data.awc_data_manager import AWCDataManager
m=AWCDataManager(str(ROOT/'data/AWCare_Merged.xlsx'))
p=ROOT/'android/app/src/main/assets/catalog.js'
bundled=json.loads(p.read_text().removeprefix('window.AWC_CATALOG = ').removesuffix(';\n'))
columns={'wound_type':'Wound Type','indication':'Indications (AWC)','exudate':'Exudate Level(Mild/ Moderate/ Heavy)','application':'Application','dressing_type':'Type of Dressing','healing_phase':'Healing Phase','product_name':'Product Name'}
assert bundled['rows']==[{k:r[c] for k,c in columns.items()} for _,r in m.df_main.iterrows()], 'Regenerate bundled catalog after editing the workbook'
expected=[m.get_product_details(n) for n in m.get_all_product_names()]
for product in expected:
    sub=m.df_main[m.df_main['Product Name'].str.lower()==product['product_name'].lower()]
    product['contraindications']='\n'.join(dict.fromkeys(v for v in sub['Contra-indications'] if v))
actual=bundled['products']
for a,e in zip(actual,expected):
    assert {k:v for k,v in a.items() if k!='image_url'}=={k:v for k,v in e.items() if k!='image_url'}, 'Stale product specifications'
assert len(actual)==len(expected)
for product in actual:
    assert not product['image_url'] or (p.parent/product['image_url']).is_file()
print('Bundled records, product specifications, precautions and photo references verified')
