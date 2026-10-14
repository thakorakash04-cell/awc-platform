/* Deterministic port of the active AWCare dataframe filtering pipeline. */
(function(root) {
'use strict';
const norm = v => String(v ?? '').trim().toLowerCase();
const fields = ['wound_type','indication','exudate','application','dressing_type','healing_phase'];
function filter(catalog, query={}) {
  const rows = catalog.rows.filter(row => fields.every(key => {
    const value = norm(query[key]);
    return !value || value === 'all' || (key === 'healing_phase' ? norm(row[key]).includes(value) : norm(row[key]) === value);
  }));
  const counts = new Map();
  rows.forEach(row => counts.set(row.product_name,(counts.get(row.product_name)||0)+1));
  return [...counts].map(([name,count]) => ({...catalog.products.find(p => p.product_name === name),match_count:count}));
}
function evaluate(catalog, query={}, emergency=false) {
  if (emergency) return {is_emergency:true,all_matches:[],primary_matches:[],secondary_matches:[],contraindication_alerts:[],total_count:0,fallback_used:false};
  let matches = filter(catalog,query), fallback = false;
  if (!matches.length && ['application','dressing_type'].some(k=>query[k] && norm(query[k]) !== 'all')) {
    matches = filter(catalog,{wound_type:query.wound_type,indication:query.indication,exudate:query.exudate});
    fallback = true;
  }
  return {is_emergency:false,all_matches:matches,primary_matches:matches.filter(p=>norm(p.dressing_type).includes('primary')),
    secondary_matches:matches.filter(p=>!norm(p.dressing_type).includes('primary') && norm(p.dressing_type).includes('secondary')),
    contraindication_alerts:matches.filter(p=>p.contraindications).map(p=>({product_name:p.product_name,warning:p.contraindications})),total_count:matches.length,fallback_used:fallback};
}
function triage(flags, diabetes, duration) {
  if (flags.some(Boolean)) return 'emergency';
  return diabetes || duration >= 4 ? 'urgent' : 'routine';
}
function quality(pixels,width,height) {
  const count = width*height;
  if (count < 4 || width < 2 || height < 2) return {passed:false,reasons:['Image is too small'],sharpness:0,mean:0,glare:0};
  const gray = new Float64Array(count);
  let luminance = 0, glare = 0;
  for(let i=0;i<count;i++) {
    const r=pixels[i*4], g=pixels[i*4+1], b=pixels[i*4+2];
    gray[i]=(r+g+b)/3; luminance+=gray[i]; if(r>245 && g>245 && b>245) glare++;
  }
  let sx=0,sy=0,sxx=0,syy=0;
  for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
    const i=y*width+x;
    const gx=x===0 ? gray[i+1]-gray[i] : x===width-1 ? gray[i]-gray[i-1] : (gray[i+1]-gray[i-1])/2;
    const gy=y===0 ? gray[i+width]-gray[i] : y===height-1 ? gray[i]-gray[i-width] : (gray[i+width]-gray[i-width])/2;
    sx+=gx;sy+=gy;sxx+=gx*gx;syy+=gy*gy;
  }
  const sharpness=sxx/count-(sx/count)**2+syy/count-(sy/count)**2, mean=luminance/count, glareRatio=glare/count;
  const reasons=[];
  if(width<300 || height<300) reasons.push('Resolution must be at least 300 × 300 pixels.');
  if(mean<40) reasons.push('Photo is too dark. Use diffused natural light.');
  if(mean>220 || glareRatio>.08) reasons.push('Excessive brightness or glare. Avoid direct flash.');
  if(sharpness<40) reasons.push('Photo appears blurred. Hold the camera steady.');
  return {passed:!reasons.length,reasons,sharpness,mean,glare:glareRatio*100};
}
function segment(pixels,width,height) {
  const overlay=new Uint8ClampedArray(pixels); const counts=[0,0,0];
  const mx=Math.floor(width*.15),my=Math.floor(height*.15),colors=[[220,20,60],[255,215,0],[20,20,20]];
  for(let y=my;y<height-my;y++) for(let x=mx;x<width-mx;x++) {
    const i=(y*width+x)*4,r=pixels[i],g=pixels[i+1],b=pixels[i+2];
    let k=-1;
    if(r>110 && r>g+20 && r>b+20) k=0;
    else if(r>130 && g>110 && b<120) k=1;
    else if(r<65 && g<65 && b<65) k=2;
    if(k>=0) {counts[k]++;for(let c=0;c<3;c++) overlay[i+c]=Math.floor(pixels[i+c]*.6+colors[k][c]*.4);}
  }
  const total=counts.reduce((a,b)=>a+b,0);
  // An unclassified image must not become 100% granulation, as in the original zero-pixel fallback.
  const percentages=total ? counts.map(n=>Math.round(n/total*100)) : [0,0,0];
  if(total) percentages[0]=Math.max(0,percentages[0]+100-percentages.reduce((a,b)=>a+b,0));
  return {percentages,counts,classified:total,overlay};
}
const api={filter,evaluate,triage,quality,segment};
root.AWCEngine=api; if(typeof module!=='undefined') module.exports=api;
})(typeof window!=='undefined' ? window : globalThis);
