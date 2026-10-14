"""Rebuild bundled catalog from the repository's single source of truth."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from data.awc_data_manager import AWCDataManager
m = AWCDataManager(str(ROOT / 'data/AWCare_Merged.xlsx'))
products = [m.get_product_details(name) for name in m.get_all_product_names()]
# Collect precautions from every record, rather than silently discarding later rows.
for p in products:
    sub = m.df_main[m.df_main['Product Name'].str.lower() == p['product_name'].lower()]
    p['contraindications'] = '\n'.join(dict.fromkeys(v for v in sub['Contra-indications'] if v))
    p['image_url'] = ''  # Populated by optional local image download; never contact a remote host at runtime.
columns = {'wound_type':'Wound Type', 'indication':'Indications (AWC)', 'exudate':'Exudate Level(Mild/ Moderate/ Heavy)', 'application':'Application', 'dressing_type':'Type of Dressing', 'healing_phase':'Healing Phase', 'product_name':'Product Name'}
rows = [{k: row[c] for k,c in columns.items()} for _,row in m.df_main.iterrows()]
options = {'wound_type':m.get_wound_types(), 'indication':m.get_indications(), 'exudate':m.get_exudate_levels(), 'application':m.get_applications(), 'dressing_type':m.get_dressing_types(), 'healing_phase':m.get_healing_phases()}
payload = {'source':'data/AWCare_Merged.xlsx', 'version':'1.0.0', 'rows':rows, 'products':products, 'options':options}
out = ROOT / 'android/app/src/main/assets/catalog.js'
out.write_text('window.AWC_CATALOG = ' + json.dumps(payload, ensure_ascii=False) + ';\n')
print(f'Exported {len(rows)} rows and {len(products)} products')
