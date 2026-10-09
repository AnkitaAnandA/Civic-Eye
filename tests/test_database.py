"""Each test uses its own temporary database, never the demo's saved reports."""
import pytest
from unittest.mock import patch
from types import SimpleNamespace
import database as db

@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'data' / 'test.db')
    monkeypatch.setattr(db, 'UPLOAD_DIR', tmp_path / 'uploads')
    db.init_db()

@pytest.fixture
def complaint():
    return dict(category='Garbage', title='Edited title', description='Edited description',
                location='Rajajinagar, Bengaluru', image_path='uploads/generated.jpg', severity='High', notes='Citizen note')

def test_crud_and_history(complaint):
    tracking_id = db.save_complaint(complaint)
    saved = db.get_complaint('  ' + tracking_id.lower() + '  ')
    assert saved['title'] == 'Edited title' and saved['severity'] == 'High'
    assert saved['notes'] == 'Citizen note' and saved['status'] == 'Submitted'
    assert len(db.list_complaints(status='Submitted', category='Garbage')) == 1
    assert db.list_complaints(category='Pothole') == []
    db.update_status(tracking_id, 'In Progress')
    db.update_status(tracking_id, 'Resolved')
    assert db.get_complaint(tracking_id)['status'] == 'Resolved'
    assert [h['status'] for h in db.get_history(tracking_id)] == db.STATUSES
    db.init_db()
    assert db.get_complaint(tracking_id)['status'] == 'Resolved'

@pytest.mark.parametrize('field,value', [('location','  '),('title',''),('category','Bad'),('severity','Bad'),('image_path','../evil.jpg')])
def test_invalid_report(complaint, field, value):
    complaint[field] = value
    with pytest.raises(ValueError): db.save_complaint(complaint)
    assert db.list_complaints() == []

def test_status_validation(complaint):
    tracking_id = db.save_complaint(complaint)
    for status in ['Bad', 'Resolved']:
        with pytest.raises(ValueError): db.update_status(tracking_id, status)
    db.update_status(tracking_id, 'Submitted')
    assert len(db.get_history(tracking_id)) == 1
    with pytest.raises(ValueError): db.update_status('CE-MISSING', 'In Progress')
    assert db.get_complaint("' OR 1=1 --") is None

def test_unique_id_collision_retry(complaint):
    with patch.object(db.uuid, 'uuid4', side_effect=[SimpleNamespace(hex='aaaaaaaa'+'0'*24), SimpleNamespace(hex='aaaaaaaa'+'0'*24), SimpleNamespace(hex='bbbbbbbb'+'0'*24)]):
        first = db.save_complaint(complaint)
        second = db.save_complaint(complaint)
    assert first != second and len(db.list_complaints()) == 2
