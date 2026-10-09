"""Exercise the actual Streamlit widgets with its supported AppTest runner."""
import pytest
from streamlit.testing.v1 import AppTest
from PIL import Image
import io
import database as db
from config import BASE_DIR

@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'app.db')
    monkeypatch.setattr(db, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setenv('AI_PROVIDER', 'openai')
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('ADMIN_PASSWORD', 'demo-test')
    result = AppTest.from_file(str(BASE_DIR / 'app.py'), default_timeout=15).run()
    assert not result.exception
    return result

def button(app, label):
    return next(widget for widget in app.button if widget.label == label)

def ready_draft(app):
    output = io.BytesIO()
    Image.new('RGB',(10,10)).save(output,'JPEG')
    app.session_state['draft'] = dict(category='Garbage', title='Draft', description='Draft description', severity='Medium', visual_evidence='Mock evidence', needs_review=False)
    app.session_state['draft_source'] = 'ai'
    for key,value in dict(category='Garbage',title='Draft',description='Draft description',severity='Medium').items():
        app.session_state['edit_' + key] = value
    return output.getvalue()

def test_start_and_unknown_lookup(app):
    app.text_input(key='track_id').set_value('CE-MISSING')
    button(app,'Look up complaint').click().run()
    assert any('not found' in item.value for item in app.info)
    assert not app.exception


@pytest.fixture
def uploaded_app(tmp_path, monkeypatch):
    import streamlit as st
    import config
    from types import SimpleNamespace
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'app.db')
    monkeypatch.setattr(db, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setattr(config, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setattr(config, 'BASE_DIR', tmp_path)
    monkeypatch.setenv('AI_PROVIDER', 'openai')
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('ADMIN_PASSWORD', 'demo-test')
    output = io.BytesIO()
    Image.new('RGB',(10,10)).save(output,'JPEG')
    monkeypatch.setattr(st, 'file_uploader', lambda *args, **kwargs: SimpleNamespace(getvalue=lambda: output.getvalue()))
    return AppTest.from_file(str(BASE_DIR / 'app.py'), default_timeout=15).run()

def test_no_location_and_missing_key_manual_fallback(uploaded_app):
    app = uploaded_app
    button(app,'Generate AI draft').click().run()
    assert any('enter a location' in item.value for item in app.error)
    assert db.list_complaints() == []
    app.text_input(key='report_location').set_value('Rajajinagar, Bengaluru')
    button(app,'Generate AI draft').click().run()
    assert any('not configured' in item.value for item in app.error)
    button(app,'Enter report manually').click().run()
    assert app.text_input(key='edit_title').value == ''
    assert not app.exception

def test_edit_submit_track_and_preserve_rerun(uploaded_app):
    app = uploaded_app
    app.text_input(key='report_location').set_value('Rajajinagar, Bengaluru')
    button(app,'Enter report manually').click().run()
    app.selectbox(key='edit_category').select('Garbage')
    app.selectbox(key='edit_severity').select('High')
    app.text_input(key='edit_title').set_value('Citizen edited title')
    app.text_area(key='edit_description').set_value('Citizen edited description')
    app.run()
    assert app.text_input(key='edit_title').value == 'Citizen edited title'
    app.text_input(key='report_location').set_value('  ')
    button(app,'Submit complaint').click().run()
    assert db.list_complaints() == []
    app.text_input(key='report_location').set_value('Rajajinagar, Bengaluru')
    app.checkbox(key='review_confirmed').check()
    button(app,'Submit complaint').click().run()
    assert not app.exception
    saved = db.list_complaints()[0]
    assert saved['title'] == 'Citizen edited title'
    assert saved['description'] == 'Citizen edited description' and saved['severity'] == 'High'
    assert (db.UPLOAD_DIR / saved['image_path'].split('/')[-1]).is_file()
    assert app.code[0].value == saved['id']
    app.text_input(key='track_id').set_value('  ' + saved['id'].lower() + '  ')
    button(app,'Look up complaint').click().run()
    assert any('Citizen edited title' == item.value for item in app.subheader)
    db.update_status(saved['id'], 'In Progress')
    app.run()
    assert any('In Progress' in item.value for item in app.info)


def test_admin_denied_then_status_updates(app):
    tracking_id = db.save_complaint(dict(category='Pothole', title='Road repair', description='Inspection requested.', location='Rajajinagar', image_path='uploads/test.jpg', severity='Medium'))
    app.text_input(key='admin_password').set_value('wrong')
    button(app,'Sign in to admin').click().run()
    assert any('Access denied' in item.value for item in app.error)
    assert not any(widget.label == 'Complaint to manage' for widget in app.selectbox)
    app.text_input(key='admin_password').set_value('demo-test')
    button(app,'Sign in to admin').click().run()
    assert not app.exception
    button(app,'Mark as In Progress').click().run()
    assert db.get_complaint(tracking_id)['status'] == 'In Progress'
    button(app,'Mark as Resolved').click().run()
    assert db.get_complaint(tracking_id)['status'] == 'Resolved'
    assert [item['status'] for item in db.get_history(tracking_id)] == db.STATUSES
    app.text_input(key='track_id').set_value(tracking_id)
    button(app,'Look up complaint').click().run()
    assert any('Resolved' in item.value for item in app.info)
    button(app,'Sign out').click().run()
    assert not any(widget.label == 'Complaint to manage' for widget in app.selectbox)

@pytest.mark.parametrize('image,error', [(b'bad image', 'readable image'), (b'x'*(5*1024*1024+1), 'too large')], ids=['bad-file','oversized'])
def test_bad_upload_ui(app, monkeypatch, image, error):
    import streamlit as st
    from types import SimpleNamespace
    monkeypatch.setattr(st, 'file_uploader', lambda *args, **kwargs: SimpleNamespace(getvalue=lambda: image))
    app.run()
    assert any(error in item.value for item in app.error)
    assert button(app,'Generate AI draft').disabled

def test_demo_label(uploaded_app, monkeypatch):
    monkeypatch.setenv('DEMO_MODE','true')
    app = uploaded_app
    app.text_input(key='report_location').set_value('Rajajinagar')
    button(app,'Generate AI draft').click().run()
    assert any('simulated AI result' in item.value for item in app.info)
    assert any('confirm or correct' in item.value for item in app.warning)


def test_api_outage_still_allows_manual_reporting(uploaded_app, monkeypatch):
    import ai_engine
    def unavailable(image_bytes):
        raise RuntimeError('AI is unavailable or timed out. Please retry or report manually below.')
    monkeypatch.setattr(ai_engine, 'analyze_image', unavailable)
    app = uploaded_app
    app.text_input(key='report_location').set_value('Rajajinagar')
    button(app,'Generate AI draft').click().run()
    assert any('unavailable' in item.value for item in app.error)
    button(app,'Enter report manually').click().run()
    assert app.text_input(key='edit_title').value == ''
    assert not app.exception
