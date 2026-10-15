"""Three-photo review, optional visual description and confirmed formulary matching."""
import hashlib,json,os,uuid
from datetime import date,datetime,timezone
import pandas as pd
import streamlit as st
from vision.iqa_gate import evaluate_image_quality
from vision.photo_workflow import prepare_photo,crop_photo,compare_measured_areas
from vision.tissue_segmentation import segment_wound_tissue
from vision.vision_model import describe_photo,check_connection,DEFAULT_MODEL
from vision.settings import load_vision_settings
from data.wound_history import WoundHistory
from data.awc_data_manager import get_awc_data_manager
from core.awc_rules_engine import evaluate_awc_query
from ui.components import render_product_card
from workspace_auth import can

REF='https://www.smith-nephew.com/en/health-care-professionals/products/advanced-wound-management/clinical-support-app'

def render_image_analysis_view():
    st.header('Photo assessment & product matching')
    st.caption('Capture → review → confirm clinical findings → match your formulary. Supports up to three dated photos of one wound.')
    if not can('use_tools'):
        st.info('Ask your administrator for assessment-tool access.');return
    gemini_key,model=load_vision_settings()
    with st.expander('Gemini AI settings',expanded=not bool(gemini_key)):
        if gemini_key:st.success('Gemini API key loaded from server settings.')
        else:
            st.warning('Gemini API key is missing. Add GEMINI_API_KEY in Streamlit → Manage app → Settings → Secrets, then save and reboot the app.')
            st.code('GEMINI_API_KEY = "your-private-key"',language='toml')
        st.caption('Model: '+model+'. The key stays on the server. Photos are sent only after you authorise an AI description.')
        if model.removeprefix('models/').startswith('gemini-2.5'):
            st.info('Google restricts 2.5 models for new projects. If access fails, set WOUND_VISION_MODEL = "'+DEFAULT_MODEL+'" in Streamlit Secrets.')
        if st.button('Check Gemini connection',disabled=not gemini_key):
            try:
                with st.spinner('Checking Gemini access…'):check_connection(gemini_key,model)
                st.success('API key and model access verified. No photo was sent. Generation quota and image support are checked when you request a description.')
            except ValueError as exc:st.error(str(exc))

    store=st.session_state._account_store;actor=st.session_state.actor
    dm=get_awc_data_manager()
    st.info('Photo observations are not a diagnosis. Colour cannot determine infection, depth, exudate volume or healing. Product candidates require a separate clinical assessment and confirmation.')
    with st.expander('Workflow reference'):
        st.write('Inspired by the guided location, appearance, exudate, depth and formulary workflow described for Smith+Nephew WOUND COMPASS. This is an independent implementation, not its APK, model or validated clinical system.')
        st.link_button('Official WOUND COMPASS overview',REF)
    st.session_state.setdefault('wound_case_ref','W-'+uuid.uuid4().hex[:8])
    case_ref=st.text_input('De-identified wound reference',key='wound_case_ref',help='Do not use a patient name, phone number or hospital ID. Keep the same reference for follow-ups.')
    with st.expander('Previously saved assessments'):
        try:
            saved=WoundHistory(store).records(actor,case_ref)
            if saved:
                table=[]
                for record in saved:
                    latest=record['photos'][-1]
                    table.append({'Saved (UTC)':datetime.fromtimestamp(record['saved_at'],timezone.utc).strftime('%d %b %Y %H:%M'),
                        'Capture date':latest['captured_on'],'Measured area (cm²)':latest['area_cm2'],**record['clinical']})
                st.table(pd.DataFrame(table))
                measured={}
                for record in reversed(saved):
                    for capture in record['photos']:
                        if capture['area_cm2'] is not None:measured[capture['captured_on']]=capture['area_cm2']
                if len(measured)>1:
                    st.caption('Clinician-entered area history; not an AI healing assessment.')
                    st.line_chart(pd.DataFrame({'Date':pd.to_datetime(list(measured)),'Entered area (cm²)':list(measured.values())}).sort_values('Date').set_index('Date'))
            else:st.caption('No records for this reference in your account. Only confirmed observations and entered measurements are saved, never photos.')
        except ValueError as exc:st.warning(str(exc))
    st.subheader('1. Add up to three photos')
    source=st.radio('Photo source',['Upload photos','Use camera'],horizontal=True,key='wound_photo_source')
    st.caption('Photograph the same site at a similar angle and lighting. Exclude identifying features. Photos remain in the session unless you explicitly send a crop to the optional AI provider.')
    photos=[];quality_failed=False
    for index,column in enumerate(st.columns(3)):
        with column:
            st.markdown(f'**Photo {index+1}**'+(' · required' if index==0 else ' · optional'))
            photo=st.file_uploader(f'Upload photo {index+1}',type=['jpg','jpeg','png'],key=f'wound_upload_{index}') if source=='Upload photos' else st.camera_input(f'Take photo {index+1}',key=f'wound_camera_{index}')
            if photo is None:continue
            try:
                image=prepare_photo(photo.getvalue());digest=hashlib.sha256(photo.getvalue()).hexdigest()[:12]
                key=f'photo_{index}_{digest}'
                captured=st.date_input('Capture date',value=date.today(),max_value=date.today(),key=key+'_date')
                iqa=evaluate_image_quality(image)
                st.image(image,caption=f'Photo {index+1}',width='stretch')
                if not iqa['passed']:
                    quality_failed=True
                    for reason in iqa['rejection_reasons']:st.warning(reason)
                    continue
                st.caption('Basic quality checks passed. Adjust the crop to exclude healthy skin and dressings.')
                horizontal=st.slider('Crop left / right (%)',0,100,(0,100),key=key+'_x')
                vertical=st.slider('Crop top / bottom (%)',0,100,(0,100),key=key+'_y')
                crop=crop_photo(image,horizontal,vertical)
                st.image(crop,caption='Selected wound-bed crop',width='stretch')
                roi_confirmed=st.checkbox('This crop contains the wound bed I intend to review',key=key+f'_{horizontal}_{vertical}_roi')
                area=None
                if st.checkbox('I have a clinically measured area',key=key+'_measured'):
                    area=st.number_input('Measured area (cm²)',min_value=0.0,value=0.0,step=.1,key=key+'_area')
                photos.append({'slot':index,'source_hash':digest,'image':crop,'captured_on':captured.isoformat(),'area_cm2':area,'confirmed':roi_confirmed,'digest':key+str(horizontal)+str(vertical)})
            except ValueError as exc:quality_failed=True;st.error(str(exc))
    if quality_failed:st.info('Replace rejected photos before continuing, or use the manual assessment workspace.');return
    if not photos:st.caption('Add a photo to start the review.');return
    if photos[0]['slot']!=0:st.info('Add Photo 1 before adding follow-ups.');return
    if len({p['source_hash'] for p in photos})!=len(photos):
        st.warning('Use different captures for a longitudinal comparison.');return
    if not all(p['confirmed'] for p in photos):st.info('Confirm the wound-bed crop for every photo.');return
    if len(photos)>1 and not st.checkbox('All photos show the same wound and can be compared',key='same_wound_'+''.join(p['digest'] for p in photos)):
        return
    try:comparison=compare_measured_areas(photos)
    except ValueError as exc:st.warning(str(exc));return
    st.subheader('2. Review image observations')
    for photo,column in zip(photos,st.columns(len(photos))):
        colors,overlay=segment_wound_tissue(photo['image']);photo['colors']=colors
        with column:
            st.image(overlay,caption=photo['captured_on']+' · colour overlay',width='stretch')
            st.write(f"Red-like: {colors['granulation_red']}% · Yellow-like: {colors['slough_yellow']}% · Dark: {colors['eschar_black']}% · Unclassified: {colors['unclassified']}%")
    st.caption('These are local pixel-colour fractions, not measured tissue composition or a healing score. Lighting, blood, shadows and skin tone can change the result.')
    if comparison:
        st.metric('Entered area: first → latest',f"{comparison['initial_cm2']:g} → {comparison['latest_cm2']:g} cm²")
        st.write(f"Change in clinician-entered area: {comparison['change_cm2']:+.2f} cm² ({comparison['reduction_percent']:+.1f}% reduction).")
        st.caption('Descriptive comparison only; this is not evidence of healing or a photo-derived measurement.')
    else:st.caption('To compare area, enter a clinical cm² measurement for the first and latest photo. Pixel area is never converted into wound size.')
    latest=photos[-1]
    with st.expander('Optional AI visual description'):
        st.caption('Local analysis works without an API key. This optional step sends only the latest cropped image, re-encoded without EXIF metadata, to Google Gemini. A general-purpose model is not a validated wound diagnostic model. Provider terms and data handling apply.')
        st.caption('Configured model: '+model)
        if not gemini_key:st.info('Configure the key in Gemini AI settings above to enable this step.')
        consent=st.checkbox('I am authorised to send this de-identified crop to Google for an AI description',key='photo_ai_consent_'+latest['digest'])
        note_key='visual_note_'+latest['digest']+model
        if st.button('Describe latest crop with AI',disabled=not gemini_key or not consent):
            store.require_permission(actor,'use_tools')
            try:
                with st.spinner('Requesting a visual description…'):st.session_state[note_key]=describe_photo(latest['image'],gemini_key,model,consent=consent)
                store.log_event(actor,'tool_use','Optional photo description')
            except ValueError as exc:st.error(str(exc))
        if note_key in st.session_state:
            note=st.session_state[note_key]
            st.write(note['description']);st.write('Visible colours: '+', '.join(note['visible_colors']))
            for limitation in note['limitations']:st.caption(limitation)
            if not note['wound_visible']:st.warning('AI did not identify a clear wound. Use manual clinical assessment; no AI diagnosis or product choice is made.')
    st.subheader('3. Confirm clinical findings')
    st.caption('Complete these from clinical assessment, not from colour percentages or AI text.')
    location=st.selectbox('Anatomical location',['Select location','Lower limb','Foot','Sacral / trunk','Upper limb','Other assessed site'])
    col1,col2,col3=st.columns(3)
    wound_type=col1.selectbox('Assessed wound type',['Select wound type']+dm.get_wound_types())
    exudate=col2.selectbox('Assessed exudate level',['Select exudate level']+dm.get_exudate_levels())
    goal=col3.selectbox('Clinician-selected goal',['Select goal']+dm.get_applications())
    depth=st.radio('Depth / cavity assessment',['Not assessed','Superficial — assessed in person','Cavity / tunnelling or uncertain depth — specialist review'],key='photo_depth')
    status=st.radio('Infection and vascular assessment',['Not assessed','Assessed: no identified concern requiring specialist review','Concern present — specialist review'],key='photo_safety_status')
    emergency=st.checkbox('Fever with spreading infection, exposed bone/tendon, or a cold/pale limb',key='photo_emergency')
    review_token=hashlib.sha256(json.dumps([case_ref,[(p['digest'],p['captured_on'],p['area_cm2']) for p in photos],location,wound_type,exudate,goal,depth,status]).encode()).hexdigest()[:16]
    clinician=st.checkbox('A clinician has reviewed these findings, patient allergies and product precautions',key='photo_clinician_review_'+review_token)
    # Changes to crop/clinical inputs require a fresh explicit matching action.
    if emergency:
        st.error('Urgent in-person medical evaluation is needed. Product matching is stopped.');return
    if depth=='Not assessed' or status=='Not assessed':st.info('Assess depth, infection and vascular status before product matching.');return
    if depth.startswith('Cavity') or status.startswith('Concern'):
        st.warning('Use specialist clinical assessment for this wound; photo-based product matching is withheld.');return
    ready=clinician and not any(value.startswith('Select') for value in (location,wound_type,exudate,goal))
    if st.button('Match confirmed findings to products',type='primary',disabled=not ready):
        store.require_permission(actor,'use_tools')
        result=evaluate_awc_query(wound_type=wound_type,exudate_level=exudate,application=goal,allow_fallback=False)
        store.log_event(actor,'tool_use','Reviewed formulary matching')
        if not result['all_matches']:st.info('No exact formulary match. Clinical criteria were not relaxed automatically.')
        else:
            st.success(f"{result['total_count']} formulary candidates. Review indications and contraindications; these are not AI prescriptions.")
            for product in result['all_matches']:render_product_card(product,is_primary='primary' in product.get('dressing_type','').lower())
    if st.button('Save confirmed assessment to my history',disabled=not ready):
        try:
            WoundHistory(store).save(actor,case_ref,photos,{'wound_type':wound_type,'exudate':exudate,'goal':goal,'location':location,'depth_assessed':depth})
            st.success('Confirmed observations saved privately to your account. No photo or AI text was stored.')
        except ValueError as exc:st.error(str(exc))
