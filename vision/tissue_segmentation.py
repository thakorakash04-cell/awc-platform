"""Local colour observations within a user-confirmed crop; not a diagnostic model."""
import numpy as np
from PIL import Image

KEYS=('granulation_red','slough_yellow','eschar_black','unclassified')

def segment_wound_tissue(image):
    """Include EVERY crop pixel in the denominator, including uncertain pixels.

    Legacy keys are retained for callers; colours must not be equated with tissue
    diagnoses. Shadows, blood, skin tone, lighting and dressings can confound them.
    """
    arr=np.asarray(image.convert('RGB'));r,g,b=[arr[:,:,i].astype(float) for i in range(3)]
    yellow=(r>100)&(g>80)&(g>=r*.65)&(b<g*.7)
    red=(r>100)&(r>g+20)&(r>b+20)&~yellow
    dark=(r<65)&(g<65)&(b<65)
    unknown=~(red|yellow|dark)
    counts=np.array([m.sum() for m in (red,yellow,dark,unknown)],dtype=float)
    exact=counts/counts.sum()*100
    pct=np.floor(exact).astype(int)
    for index in np.argsort(-(exact-pct))[:100-int(pct.sum())]:pct[index]+=1
    overlay=arr.copy()
    for mask,color in [(red,[220,20,60]),(yellow,[255,215,0]),(dark,[50,50,70])]:
        overlay[mask]=(overlay[mask]*.65+np.array(color)*.35).astype('uint8')
    return dict(zip(KEYS,map(int,pct))),Image.fromarray(overlay)
