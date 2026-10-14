"""Download source catalog photos at build time; never runtime."""
import sys,json,hashlib,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from data.awc_data_manager import AWCDataManager
m=AWCDataManager(str(ROOT/'data/AWCare_Merged.xlsx'))
assets=ROOT/'android/app/src/main/assets'; dest=assets/'images'; dest.mkdir(exist_ok=True)
path=assets/'catalog.js'; data=json.loads(path.read_text().removeprefix('window.AWC_CATALOG = ').removesuffix(';\n'))
def download(item):
    name,url=item
    filename=hashlib.sha256(url.encode()).hexdigest()[:16]+'.png'
    target=dest/filename
    try:
        if not target.exists():
            with urllib.request.urlopen(url,timeout=25) as r: content=r.read(8*1024*1024)
            import io
            img=Image.open(io.BytesIO(content)).convert('RGBA');img.thumbnail((600,600));img.save(target)
        return name,'images/'+filename
    except Exception as e:
        print('Missing image:',name,type(e).__name__); return name,''
with ThreadPoolExecutor(max_workers=5) as pool: images=dict(pool.map(download,m.prod_images.items()))
for p in data['products']: p['image_url']=images.get(p['product_name'].strip().lower(),'')
with ThreadPoolExecutor(max_workers=5) as pool: data['indication_images']=dict(pool.map(download,m.ind_images.items()))
path.write_text('window.AWC_CATALOG = '+json.dumps(data,ensure_ascii=False)+';\n')
print('Bundled',sum(bool(p['image_url']) for p in data['products']),'product photos')
