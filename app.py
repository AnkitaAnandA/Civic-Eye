"""Three citizen/admin screens; image intelligence and persistence live elsewhere."""
import hashlib
import hmac
import logging
import os
from pathlib import Path
import sqlite3
import uuid
import streamlit as st
from ai_engine import analyze_image, prepare_image
import database as db
from config import BASE_DIR, CATEGORIES, DEPARTMENTS, SEVERITIES, STATUSES, UPLOAD_DIR, demo_mode

st.set_page_config(page_title="CivicEye AI", page_icon="🏙️", layout="centered")

def begin_draft(draft: dict, source: str) -> None:
    """Set editable widget values once, so reruns preserve citizen changes."""
    st.session_state['draft'] = draft
    st.session_state['draft_source'] = source
    for field in ('category', 'title', 'description', 'severity'):
        st.session_state['edit_' + field] = draft[field]
    st.session_state['review_confirmed'] = False
    st.session_state.pop('submitted_id', None)

def clear_report() -> None:
    """Start a fresh report without keeping an old image or old success ID."""
    for key in list(st.session_state):
        if key.startswith(('edit_', 'report_')) or key in ('draft','draft_source','review_confirmed','submitted_id','image_digest','prepared_image'):
            del st.session_state[key]

def report_screen() -> None:
    """Guide upload, review and submission with a manual route always available."""
    st.subheader("Report an Issue")
    st.caption("1 · Upload & Location → 2 · Review Draft → 3 · Submit & Get ID")
    if 'submitted_id' in st.session_state:
        saved = db.get_complaint(st.session_state['submitted_id'])
        st.success("Complaint saved. Save this ID to check progress.")
        st.header(st.session_state['submitted_id'])
        st.code(st.session_state['submitted_id'], language=None)
        if saved:
            st.info("Suggested department: " + DEPARTMENTS[saved['category']])
        st.caption("Saved in this CivicEye demo. This complaint has not been forwarded to a municipal authority.")
        st.button("Report another issue", on_click=clear_report)
        return
    st.markdown("### Step 1 · Upload & Location")
    st.caption("Upload JPG, JPEG, PNG or WebP, up to 5 MB. Avoid photos with personal information. AI analysis sends the resized image to your selected AI provider; manual reporting keeps it local.")
    uploaded = st.file_uploader("Photo of the issue", type=['jpg','jpeg','png','webp'], key='report_photo')
    location = st.text_input("Location (required)", placeholder="Rajajinagar, Bengaluru", max_chars=300, key='report_location')
    notes = st.text_area("Additional notes (optional)", max_chars=1000, key='report_notes')
    prepared = None
    if uploaded is not None:
        raw = uploaded.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != st.session_state.get('image_digest'):
            st.session_state.pop('draft', None)
            st.session_state.pop('prepared_image', None)
            st.session_state['image_digest'] = digest
        try:
            prepared = prepare_image(raw)
            st.session_state['prepared_image'] = prepared
            st.image(prepared, caption="Your photo", width='stretch')
        except ValueError as error:
            st.error(str(error))
    else:
        st.session_state.pop('draft', None)
        st.session_state.pop('prepared_image', None)
        st.session_state.pop('image_digest', None)
    if demo_mode():
        st.warning("Demo mode: simulated AI result. The canned pothole example does not analyse your image. Correct every field before submitting.")
    if st.button("Generate AI draft", disabled=prepared is None, type='primary'):
        if not location.strip():
            st.error("Please enter a location.")
        else:
            try:
                with st.spinner("Preparing your draft… This may take up to 90 seconds if validation needs a retry."):
                    result = analyze_image(uploaded.getvalue())
                begin_draft(result, 'demo' if demo_mode() else 'ai')
            except (RuntimeError, ValueError) as error:
                st.error(str(error))
                st.info("Choose Enter report manually to continue.")
    if st.button("Enter report manually", disabled=prepared is None):
        if not location.strip():
            st.error("Please enter a location.")
        else:
            begin_draft(dict(category='Unknown', title='', description='', severity='Medium',
                             visual_evidence='Citizen-entered report; no AI analysis.', needs_review=True), 'manual')
    if 'draft' not in st.session_state:
        return
    st.markdown("### Step 2 · Review Draft")
    draft = st.session_state['draft']
    source = st.session_state['draft_source']
    st.info({'ai':'AI suggested, please verify.', 'demo':'Demo mode: simulated AI result.', 'manual':'Manual report: describe only what you observed.'}[source])
    st.caption("Visual evidence: " + draft['visual_evidence'])
    category = st.selectbox("Category", CATEGORIES, key='edit_category')
    title = st.text_input("Complaint title", max_chars=80, key='edit_title')
    description = st.text_area("Complaint description", max_chars=2000, height=150, key='edit_description')
    severity = st.selectbox("Severity (suggested; please verify)", SEVERITIES, key='edit_severity')
    st.markdown("**Severity: " + {'Low':'🟢 Low', 'Medium':'🟠 Medium', 'High':'🔴 High'}[severity] + "**")
    st.caption("Suggested department: " + DEPARTMENTS[category])
    needs_review = draft['needs_review'] or category in ['Unknown','Streetlight']
    if needs_review:
        st.warning("Please confirm or correct the category and description. A streetlight photo alone cannot establish a malfunction.")
    confirmed = st.checkbox("I have checked the photo, category and complaint details.", key='review_confirmed')
    st.markdown("### Step 3 · Submit & Get ID")
    st.caption("This saves a local demo complaint; it does not contact a real authority.")
    if st.button("Submit complaint", type='primary'):
        if not location.strip():
            st.error("Please enter a location.")
        elif not title.strip() or not description.strip():
            st.error("Please enter a title and description.")
        elif not confirmed:
            st.error("Please check the complaint details and tick the confirmation box.")
        elif prepared is None:
            st.error("Please upload a valid image.")
        else:
            image_path = UPLOAD_DIR / (uuid.uuid4().hex + '.jpg')
            try:
                image_path.write_bytes(prepared)
                tracking_id = db.save_complaint(dict(category=category, title=title, description=description,
                    location=location, notes=notes, image_path='uploads/' + image_path.name,
                    severity=severity, needs_review=needs_review))
                st.session_state['submitted_id'] = tracking_id
            except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
                # Remove only this generated image if the database insert failed.
                if image_path.exists():
                    image_path.unlink(missing_ok=True)
                logging.warning("Submission failed: %s", type(error).__name__)
                st.error(str(error) if isinstance(error, ValueError) else "Could not save the complaint. Please retry; your draft is still here.")
            else:
                st.rerun()

def show_complaint(complaint: dict) -> None:
    """Render text safely and show the persisted status timeline on every rerun."""
    st.subheader(complaint['title'])
    st.write("Tracking ID: " + complaint['id'])
    st.info({'Submitted':'📨 Submitted', 'In Progress':'🛠️ In Progress', 'Resolved':'✅ Resolved'}[complaint['status']])
    for label, field in [('Category','category'),('Description','description'),('Location','location'),('Severity','severity'),('Created (UTC)','created_at'),('Updated (UTC)','updated_at')]:
        st.text(label + ': ' + str(complaint[field]))
    if complaint['notes']:
        st.text('Citizen notes: ' + complaint['notes'])
    st.caption('Suggested department: ' + DEPARTMENTS[complaint['category']])
    if complaint['needs_review']:
        st.caption('Review flag: this report required citizen review; it is not authority-verified.')
    path = (BASE_DIR / complaint['image_path']).resolve()
    if path.is_relative_to(UPLOAD_DIR.resolve()) and path.is_file():
        st.image(str(path), caption='Submitted photo', width='stretch')
    else:
        st.warning('The saved image is unavailable.')
    st.markdown('**Status history (UTC)**')
    for entry in db.get_history(complaint['id']):
        st.text(entry['status'] + ' · ' + entry['changed_at'])

def track_screen() -> None:
    """Use a persistent lookup ID so a status update is visible after refresh."""
    st.subheader('Track Complaint')
    tracking_id = st.text_input('Tracking ID', placeholder='CE-1234ABCD', key='track_id')
    if st.button('Look up complaint'):
        st.session_state['lookup_id'] = tracking_id
    if 'lookup_id' in st.session_state:
        complaint = db.get_complaint(st.session_state['lookup_id'])
        if complaint:
            show_complaint(complaint)
        else:
            st.info('Complaint not found. Please check the tracking ID and try again.')

def admin_screen() -> None:
    """Demo password protection gates all list and update controls server-side."""
    st.subheader('Admin (Demo)')
    st.warning('Demo-only protection. This shared password is not production authentication.')
    password = os.getenv('ADMIN_PASSWORD', '').strip()
    if not password:
        st.info('Set ADMIN_PASSWORD in .env and restart the app to enable admin controls.')
        return
    password_fingerprint = hashlib.sha256(password.encode()).hexdigest()
    if st.session_state.get('admin_auth') != password_fingerprint:
        supplied = st.text_input('Admin password', type='password', key='admin_password')
        if st.button('Sign in to admin'):
            if hmac.compare_digest(supplied.encode(), password.encode()):
                st.session_state['admin_auth'] = password_fingerprint
                st.session_state.pop('admin_password', None)
                st.rerun()
            else:
                st.error('Access denied. Please check the admin password.')
        return
    if st.button('Sign out'):
        st.session_state.pop('admin_auth', None)
        st.rerun()
    status = st.selectbox('Filter by status', ['All'] + STATUSES, key='admin_status_filter')
    category = st.selectbox('Filter by category', ['All'] + CATEGORIES, key='admin_category_filter')
    complaints = db.list_complaints(None if status == 'All' else status, None if category == 'All' else category)
    st.caption(str(len(complaints)) + ' complaint(s)')
    if not complaints:
        st.info('No complaints match these filters.')
        return
    for item in complaints:
        st.text(item['id'] + ' · ' + item['category'] + ' · ' + item['status'] + ' · ' + item['title'])
    chosen_id = st.selectbox('Complaint to manage', [item['id'] for item in complaints], key='admin_chosen_id')
    chosen = db.get_complaint(chosen_id)
    if chosen is None:
        st.info('Complaint not found. Please refresh.')
        return
    show_complaint(chosen)
    current = chosen['status']
    index = STATUSES.index(current)
    if index == len(STATUSES) - 1:
        st.success('This complaint is resolved.')
        return
    next_status = STATUSES[index + 1]
    st.caption('Next allowed status: ' + next_status)
    if st.button('Mark as ' + next_status):
        try:
            db.update_status(chosen_id, next_status)
        except ValueError as error:
            st.error(str(error))
        else:
            st.rerun()

def main() -> None:
    """Keep startup and database failures readable instead of showing a traceback."""
    st.title('🏙️ CivicEye AI')
    st.write('Spot an issue. Shape a complaint. Follow its progress.')
    with st.sidebar:
        st.header('How it works')
        st.write('1. Upload a photo and location.\n2. Review or write a complaint.\n3. Save your tracking ID.')
        st.caption('AI suggests. Citizens review. Demo admins update status.')
    try:
        db.init_db()
        report, track, admin = st.tabs(['Report an Issue','Track Complaint','Admin (Demo)'])
        with report: report_screen()
        with track: track_screen()
        with admin: admin_screen()
    except (sqlite3.Error, OSError) as error:
        logging.warning('Storage unavailable: %s', type(error).__name__)
        st.error('Local storage is unavailable. Check folder permissions and restart the app. Your draft remains in this browser session.')

main()
