import sys,json,random,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from core.awc_rules_engine import evaluate_awc_query
from data.awc_data_manager import get_awc_data_manager
m=get_awc_data_manager()
options={'wound_type':['All']+m.get_wound_types(),'indication':['All']+m.get_indications(),'exudate':['All']+m.get_exudate_levels(),'application':['All']+m.get_applications(),'dressing_type':['All']+m.get_dressing_types(),'healing_phase':['All']+m.get_healing_phases()}
queries=[{}]
for field,values in options.items():queries += [{field:v} for v in values]
for wound,ex,app in itertools.product(options['wound_type'],options['exudate'],options['application']):queries.append(dict(wound_type=wound,exudate=ex,application=app))
random.seed(42)
for _ in range(500):queries.append({k:random.choice(v) for k,v in options.items()})
cases=[]
for q in queries:
    args=dict(q)
    if 'exudate' in args:args['exudate_level']=args.pop('exudate')
    r=evaluate_awc_query(**args)
    cases.append({'query':q,'names':[p['product_name'] for p in r['all_matches']],'fallback':r['fallback_used']})
Path(sys.argv[1]).write_text(json.dumps(cases))
print('Generated',len(cases),'reference cases')
