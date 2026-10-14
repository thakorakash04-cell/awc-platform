'use strict';
const catalog=window.AWC_CATALOG, engine=window.AWCEngine;
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fields={wound_type:'Wound type',indication:'Specific indication',exudate:'Exudate / drainage',application:'Clinical goal',dressing_type:'Dressing type',healing_phase:'Healing phase'};
let tab='clinician', selected=new Set(), imageToken=0, photoResult=null;
const checked=id=>Boolean($(id)?.checked);
const val=id=>$(id)?.value||'All';
const check=(id,label)=>`<label class="check"><input type="checkbox" id="${id}"><span>${esc(label)}</span></label>`;
function option(v){return `<option value="${esc(v)}">${esc(v)}</option>`;}
function select(id,label,values,initial='All'){return `<label class="field">${esc(label)}<select id="${id}">${values.map(v=>`<option${v===initial?' selected':''} value="${esc(v)}">${esc(v)}</option>`).join('')}</select></label>`;}
function field(key,prefix='',initial='All'){return select(prefix+key,fields[key],['All',...catalog.options[key]],initial);}
function notice(text,type=''){return `<div class="notice ${type}" role="status">${text}</div>`;}
function safety(prefix,patient=false) {
 const labels=patient?['I have fever, chills, or feel sick all over','Redness is rapidly spreading around the wound','I can see bone, tendon, or deep structures','Tissue is black, mushy, or has a strong bad smell','My foot/leg is cold, pale/blue, numb, or severely painful']:['Exposed bone, tendon, or surgical hardware','Systemic fever, rigors, or rapidly spreading infection','Critical limb ischemia: cold/pale foot or ABPI below 0.5'];
 return `<div class="panel"><h2>Safety check</h2><p class="text-small">Check every statement that applies.</p>${labels.map((s,i)=>check(prefix+'flag'+i,s)).join('')}${patient?check('diabetes','I have diabetes and an open sore on my foot')+'<label class="field">Weeks the wound has been open<input id="duration" type="number" min="0" max="52" value="0"></label>':''}${check(prefix+'reviewed','I have reviewed all the safety statements above.')}<div id="${prefix}safety-message"></div></div>`;
}
function emergency(){return notice('<strong>Immediate medical evaluation required</strong>Reported warning signs require an in-person medical assessment. Product selection is halted. Go to the nearest emergency department.','danger');}
function currentEmergency(prefix,patient=false){return Array.from({length:patient?5:3},(_,i)=>checked(prefix+'flag'+i)).some(Boolean);}
function details(p){const keys={moc:'Material / components',sizes_available:'Available sizes',indications:'Indications',applications:'Applications',wound_types:'Wound types',exudate_levels:'Exudate levels',healing_phase:'Healing phase',hydration:'Hydration',absorbency:'Absorbency',frequency:'Change frequency',wear_time:'Cumulative wear time',sterilization:'Sterilization',key_features:'Key features'};return Object.entries(keys).map(([key,label])=>`<div class="detail-row"><b>${label}</b>${esc(Array.isArray(p[key])?p[key].join(' · '):p[key]||'Not specified')}</div>`).join('');}
function product(p,compare=false){return `<article class="product"><span class="pill">${esc(p.dressing_type||'Product reference')}</span><h3>${esc(p.product_name)}</h3>${p.image_url&&p.image_url.startsWith('images/')?`<img class="product-image" src="${esc(p.image_url)}" alt="${esc(p.product_name)}">`:''}<p>${esc(p.description)}</p><div class="meta"><div><strong>Clinical goal</strong>${esc(p.applications.join(' · '))}</div><div><strong>Exudate</strong>${esc(p.exudate_levels.join(' · '))}</div><div><strong>Change frequency</strong>${esc(p.frequency||'Not specified')}</div><div><strong>Wear time</strong>${esc(p.wear_time||'Not specified')}</div></div>${p.contraindications?notice('<strong>Product precautions</strong>'+esc(p.contraindications),'warning'):''}<details><summary>Full product details</summary>${details(p)}</details>${compare?`<label class="check compare-label"><input type="checkbox" data-compare="${esc(p.product_name)}"${selected.has(p.product_name)?' checked':''}><span>Add to comparison</span></label>`:''}</article>`;}
function renderResult(result,target='match-results'){
 let html='';
 if(result.is_emergency){$(target).innerHTML=emergency();return;}
 if(result.fallback_used) html+=notice('<strong>Broader catalog matches</strong>No exact match was found. Clinical goal, dressing type and healing phase were relaxed; wound type, indication and exudate were retained. Review these differences before selection.','warning');
 if(!result.total_count) html+=`<div class="empty">No products match this combination. Adjust the filters.</div>`;
 else html+=result.all_matches.map(p=>product(p)).join('');
 $(target).innerHTML=html;
 if($('match-count')) $('match-count').textContent=result.total_count+' products';
}
function bindChanges(fn){$('content').querySelectorAll('select,input:not([type=file])').forEach(el=>el.addEventListener('change',fn));}
function updateIndications(prefix=''){
 const value=val(prefix+'indication'), wound=val(prefix+'wound_type');
 const values=[...new Set(catalog.rows.filter(r=>wound==='All'||r.wound_type===wound).map(r=>r.indication))].filter(Boolean).sort();
 $(prefix+'indication').innerHTML=['All',...values].map(option).join('');
 $(prefix+'indication').value=values.includes(value)?value:'All';
}
function showIndication(prefix=''){const name=val(prefix+'indication').toLowerCase();const image=catalog.indication_images?.[name];const target=$(prefix+'indication-image');if(target)target.innerHTML=image&&image.startsWith('images/')?`<details><summary>View indication reference image</summary><img class="photo" src="${esc(image)}" alt="${esc(val(prefix+'indication'))}"><p class="text-small">Catalog reference image; appearance alone cannot establish a diagnosis.</p></details>`:'';}
function clinician(){
 $('content').innerHTML=safety('c')+`<div class="panel"><h2>Wound assessment</h2><div class="grid">${Object.keys(fields).map(k=>field(k)).join('')}</div><div id="indication-image"></div></div><div class="result-head"><h2>Formulary matches</h2><span class="count" id="match-count">0 products</span></div><div id="match-results"></div>`;
 const update=()=>{
   showIndication();
   if(currentEmergency('c')){ $('csafety-message').innerHTML=emergency();renderResult(engine.evaluate(catalog,{},true));return;}
   $('csafety-message').innerHTML='';
   if(!checked('creviewed')){$('match-results').innerHTML=notice('Review and confirm the safety check to see matching products.');$('match-count').textContent='Awaiting review';return;}
   renderResult(engine.evaluate(catalog,Object.fromEntries(Object.keys(fields).map(k=>[k,val(k)]))));
 };
 $('wound_type').addEventListener('change',()=>updateIndications());bindChanges(update);update();
}
function patient(){
 $('content').innerHTML=safety('p',true)+`<div class="panel"><h2>Describe the wound</h2><div class="grid">${field('wound_type','p','Acute Wound')}${field('indication','p')}${field('exudate','p','Moderate')}${field('application','p','Moisture Balance')}</div><div id="pindication-image"></div><p class="text-small">These are catalog matches to review with your clinician. The photo tool does not diagnose wounds.</p></div><div class="result-head"><h2>Dressings to discuss</h2><span class="count" id="match-count"></span></div><div id="match-results"></div><div class="panel"><h2>General care reminders</h2><p>Wash hands before and after handling dressings. Follow the product instructions for cleansing, application and changes. Seek medical help for spreading redness, increased pain, or fever.</p></div>`;
 const update=()=>{
   showIndication('p');
   const level=engine.triage(Array.from({length:5},(_,i)=>checked('pflag'+i)),checked('diabetes'),Number($('duration').value));
   if(level==='emergency'){$('psafety-message').innerHTML=emergency();renderResult(engine.evaluate(catalog,{},true));return;}
   $('psafety-message').innerHTML=level==='urgent'?notice('<strong>Doctor evaluation recommended</strong>A diabetic foot sore or a wound open for four weeks or longer needs professional assessment. Review catalog options with your clinician.','warning'):'';
   if(!checked('previewed')){$('match-results').innerHTML=notice('Review and confirm the safety check before viewing catalog matches.');$('match-count').textContent='Awaiting review';return;}
   const query={wound_type:val('pwound_type'),indication:val('pindication'),exudate:val('pexudate'),application:val('papplication')};
   renderResult(engine.evaluate(catalog,query));
 };$('pwound_type').addEventListener('change',()=>updateIndications('p'));updateIndications('p');bindChanges(update);update();
}
function comparison(){
 const products=catalog.products.filter(p=>selected.has(p.product_name));
 $('compare-count').textContent=products.length+' / 4';
 if(!products.length){$('comparison').innerHTML=notice('Select up to four products below to compare.');return;}
 const rows={dressing_type:'Dressing type',description:'Description',moc:'Material',sizes_available:'Sizes',indications:'Indications',applications:'Applications',exudate_levels:'Exudate',healing_phase:'Healing phase',absorbency:'Absorbency',frequency:'Change frequency',wear_time:'Wear time',sterilization:'Sterilization',contraindications:'Precautions'};
 $('comparison').innerHTML=`<div class="comparison"><table><thead><tr><th>Compare</th>${products.map(p=>`<th>${esc(p.product_name)}</th>`).join('')}</tr></thead><tbody>${Object.entries(rows).map(([key,label])=>`<tr><td>${label}</td>${products.map(p=>`<td>${esc(Array.isArray(p[key])?p[key].join(' · '):p[key]||'Not specified')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function explorer(){
 $('content').innerHTML=`<div class="panel"><h2>Explore the formulary</h2><div class="grid"><label class="field">Search product, material or feature<input type="text" id="search" placeholder="e.g. silicone, foam, silver"></label>${field('wound_type','cat')}${field('application','cat')}</div></div><div class="result-head"><h2>Side-by-side comparison</h2><span class="count" id="compare-count"></span></div><div id="comparison"></div><div class="result-head"><h2>Products</h2><span class="count" id="catalog-count"></span></div><div id="catalog-results"></div>`;
 const update=()=>{const q=$('search').value.toLowerCase().trim();let products=engine.filter(catalog,{wound_type:val('catwound_type'),application:val('catapplication')});if(q) products=products.filter(p=>[p.product_name,p.moc,p.key_features,p.description].some(v=>String(v).toLowerCase().includes(q)));$('catalog-count').textContent=products.length+' products';$('catalog-results').innerHTML=products.length?products.map(p=>product(p,true)).join(''):'<div class="empty">No products found.</div>';
 $('catalog-results').querySelectorAll('[data-compare]').forEach(el=>el.addEventListener('change',()=>{if(el.checked&&selected.size>=4){el.checked=false;alert('Compare up to four products. Remove one selection first.');return;}el.checked?selected.add(el.dataset.compare):selected.delete(el.dataset.compare);comparison();}));};
 $('search').addEventListener('input',update);bindChanges(update);comparison();update();
}
function photo(){
 photoResult=null;
 $('content').innerHTML=notice('<strong>Assistive colour analysis</strong>This is the repository’s colour heuristic, not a diagnostic AI model. Colour classes cannot establish infection, wound depth, blood flow, or tissue viability. Clinician review is required.','warning')+`<div class="panel"><h2>Choose a wound photo</h2><p class="text-small">Photo processing happens on this device. Images are not uploaded or saved by the app.</p><div class="actions"><label class="button" for="photo-input">Choose photo</label><input id="photo-input" type="file" accept="image/*"><button id="take-photo" class="secondary">Take photo</button><button id="clear-photo" class="secondary">Clear</button></div><p class="text-small">Use a sharp image of at least 300 × 300 px, with diffused light and no flash glare. Maximum file size: 20 MB. Large images are resized to 1600 px for on-device processing.</p><div id="photo-status"></div><canvas id="photo-canvas" hidden></canvas><div id="photo-metrics"></div></div><div id="photo-confirm"></div>`;
 $('photo-input').addEventListener('change',async event=>{const file=event.target.files[0];if(!file)return;if(file.size>20*1024*1024){clearPhoto();$('photo-status').innerHTML=notice('Photo exceeds 20 MB. Choose a smaller image.','danger');return;}const url=URL.createObjectURL(file);await analyze(url);URL.revokeObjectURL(url);});
 $('take-photo').addEventListener('click',()=>{clearPhoto();if(window.AWCNative)window.AWCNative.takePhoto();else $('photo-status').innerHTML=notice('Camera is available in the Android APK. Choose a photo for this preview.');});$('clear-photo').addEventListener('click',clearPhoto);
}
function clearPhoto(){imageToken++;photoResult=null;if(!$('photo-canvas'))return;const canvas=$('photo-canvas');canvas.hidden=true;canvas.width=1;canvas.height=1;$('photo-status').innerHTML='';$('photo-metrics').innerHTML='';$('photo-confirm').innerHTML='';$('photo-input').value='';}
async function analyze(url){
 clearPhoto();const token=imageToken;$('photo-status').innerHTML='<p class="busy">Checking photo on this device…</p>';
 try{
 const image=new Image();image.src=url;await image.decode();if(token!==imageToken||tab!=='photo')return;
 const ratio=Math.min(1,1600/Math.max(image.naturalWidth,image.naturalHeight));const width=Math.max(1,Math.round(image.naturalWidth*ratio)),height=Math.max(1,Math.round(image.naturalHeight*ratio));
 const canvas=$('photo-canvas');canvas.width=width;canvas.height=height;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0,width,height);canvas.hidden=false;
 const data=ctx.getImageData(0,0,width,height), q=engine.quality(data.data,width,height);
 $('photo-metrics').innerHTML=`<div class="metrics"><div><strong>${q.sharpness.toFixed(1)}</strong>Sharpness</div><div><strong>${q.mean.toFixed(1)}</strong>Luminance</div><div><strong>${q.glare.toFixed(1)}%</strong>Glare</div></div>`;
 if(!q.passed){$('photo-status').innerHTML=notice('<strong>Image quality check failed</strong>'+q.reasons.map(esc).join('<br>'),'danger');return;}
 const s=engine.segment(data.data,width,height);
 if(!s.classified){$('photo-status').innerHTML=notice('<strong>No colour classes identified</strong>The heuristic could not classify this photo. Use a manual clinical assessment.','warning');return;}
 ctx.putImageData(new ImageData(s.overlay,width,height),0,0);photoResult=s;
 $('photo-status').innerHTML=notice('Quality check passed. Overlay covers the central 70% of the image.');
 $('photo-metrics').innerHTML+=`<div class="metrics"><div><strong>${s.percentages[0]}%</strong>Red-class pixels</div><div><strong>${s.percentages[1]}%</strong>Yellow-class pixels</div><div><strong>${s.percentages[2]}%</strong>Black-class pixels</div></div><p class="text-small">Percentages describe classified colour pixels, not clinically confirmed tissue composition. Fluid level and treatment goals must be assessed manually.</p>`;
 $('photo-confirm').innerHTML=safety('i')+`<div class="panel"><h2>Clinician confirmation</h2><div class="grid">${field('wound_type','i')}${field('exudate','i')}${field('application','i')}</div>${check('iconfirm','I have manually assessed the wound and selected the clinical parameters above.')}<button id="photo-match">Show catalog matches</button></div><div id="match-results"></div>`;
 const update=()=>{if(currentEmergency('i')){$('isafety-message').innerHTML=emergency();$('match-results').innerHTML=emergency();}else{$('isafety-message').innerHTML='';$('match-results').innerHTML='';}};
 $('photo-confirm').querySelectorAll('input,select').forEach(el=>el.addEventListener('change',update));
 $('photo-match').addEventListener('click',()=>{if(currentEmergency('i')){$('match-results').innerHTML=emergency();return;}if(!checked('ireviewed')||!checked('iconfirm')||['iwound_type','iexudate','iapplication'].some(id=>val(id)==='All')){$('match-results').innerHTML=notice('Review safety, select all three parameters, and confirm the manual assessment.','warning');return;}renderResult(engine.evaluate(catalog,{wound_type:val('iwound_type'),exudate:val('iexudate'),application:val('iapplication')}));});
 }catch(error){if(token===imageToken&&tab==='photo'){$('photo-status').innerHTML=notice('Could not read this image. Choose a standard JPEG or PNG photo.','danger');}}
}
window.receiveCameraPhoto=url=>{if(tab==='photo')analyze(url);};
function about(){
 $('content').innerHTML=`<div class="panel"><h2>Built to work offline</h2><p>The app bundles <b>${catalog.products.length} products</b> and <b>${catalog.rows.length} clinical matching records</b> from <b>${esc(catalog.source)}</b>. No account, server, API key or internet connection is required.</p><p>All product matching and photo processing run on your device. Photos are held in memory and cleared when you leave the photo tab. Temporary camera files are deleted after processing. The app does not keep patient records.</p></div><div class="panel"><h2>How matching works</h2><p>Wound type, indication, exudate, clinical goal and dressing type use exact text matches. Healing phase uses a text containment match. If a clinical-goal or dressing-type query returns no products, the source engine broadens the search and explicitly labels the result.</p><p>Product specifications and precautions are taken from the bundled dataset. Catalog matches are reference information; they do not independently establish suitability for an individual patient.</p></div><div class="panel"><h2>Photo analysis</h2><p>The photo tool reproduces the repository’s brightness, glare and sharpness checks, followed by red/yellow/black colour thresholds in the central image region. It is a colour heuristic, not trained AI and not a diagnosis. A clinician must manually assess and confirm the wound before viewing matches.</p></div><div class="panel"><h2>Guidelines &amp; source claims</h2><p>The source repository refers to WOCN, EWMA, IWII, IEC 62366-1 and FDA CDS provisions. These references are not a certification of this mobile app. The catalog and clinical content require review by the responsible clinical team before clinical deployment.</p><p>No professional credential verification is performed offline. Clinician workspace access is a workspace choice, not authentication.</p></div><div class="panel"><h2>Updating the catalog</h2><p>This version uses a bundled snapshot. Updating the Excel source requires regenerating the bundled catalog and installing a new APK. Your existing Streamlit application remains a separate interface.</p><p class="text-small">AWC Offline · 1.0.0 · Android 8.0 and later</p></div>`;
}
function navigate(next){imageToken++;photoResult=null;tab=next;document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));const titles={clinician:['Clinician workspace','Match your assessment to the bundled AWCare formulary.'],patient:['Patient & caregiver guide','Review warning signs and explore dressing reference information.'],catalog:['Product catalog','Explore 23 products and compare their specifications.'],photo:['Assistive photo review','Local image checks with required clinician confirmation.'],about:['About AWC Offline','Your catalog and matching tools, available without a connection.']};$('page-title').textContent=titles[tab][0];$('page-caption').textContent=titles[tab][1];({clinician,patient,catalog:explorer,photo,about})[tab]();window.scrollTo(0,0);}
window.handleAndroidBack=()=>{if(tab!=='clinician'){navigate('clinician');return true;}return false;};
document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.tab)));navigate('clinician');
