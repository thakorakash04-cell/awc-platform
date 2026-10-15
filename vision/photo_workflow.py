"""Bounded photo decoding and descriptive longitudinal comparisons."""
import io,math
from datetime import date
from PIL import Image,ImageOps,UnidentifiedImageError

MAX_BYTES=10*1024*1024
MAX_PIXELS=20_000_000

def prepare_photo(raw):
    if not raw or len(raw)>MAX_BYTES:raise ValueError('Choose a JPEG or PNG photo under 10 MB.')
    try:
        with Image.open(io.BytesIO(raw)) as opened:
            if opened.format not in ('JPEG','PNG'):raise ValueError('Only genuine JPEG and PNG images are supported.')
            if opened.width*opened.height>MAX_PIXELS:raise ValueError('Image is too large. Use a photo below 20 megapixels.')
            normalized=ImageOps.exif_transpose(opened).convert('RGB')
            normalized.thumbnail((2048,2048))
            # Rebuild pixels so original EXIF/GPS metadata cannot reach a provider.
            return Image.fromarray(__import__('numpy').array(normalized))
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as exc:
        raise ValueError('The photo could not be read. Choose a valid JPEG or PNG.') from exc

def crop_photo(image,horizontal,vertical):
    x1,x2=horizontal;y1,y2=vertical
    if not (0<=x1<x2<=100 and 0<=y1<y2<=100):raise ValueError('Choose a non-empty wound-bed crop.')
    box=(round(image.width*x1/100),round(image.height*y1/100),round(image.width*x2/100),round(image.height*y2/100))
    if box[2]-box[0]<32 or box[3]-box[1]<32:raise ValueError('Crop is too small for analysis. Include at least 32 pixels in each direction.')
    return image.crop(box)

def compare_measured_areas(records):
    """Only compare clinician-entered cm² values; never infer area from pixel count."""
    if len(records)<2:return None
    dates=[date.fromisoformat(r['captured_on']) for r in records]
    if dates!=sorted(dates) or len(set(dates))!=len(dates):raise ValueError('Comparison photos must have distinct dates in chronological order.')
    if any(d>date.today() for d in dates):raise ValueError('Capture dates cannot be in the future.')
    first,last=records[0].get('area_cm2'),records[-1].get('area_cm2')
    if first is None or last is None:return None
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (first,last)) or first<=0 or last<0:raise ValueError('Baseline area must be positive and latest area non-negative, in finite cm² values.')
    return {'initial_cm2':first,'latest_cm2':last,'change_cm2':last-first,'reduction_percent':round((first-last)/first*100,1)}
