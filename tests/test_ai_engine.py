"""No network or API key is needed: model responses are mocked."""
import io
import json
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from PIL import Image
from openai import APIConnectionError
import httpx
import ai_engine as ai

@pytest.fixture
def photo():
    output = io.BytesIO()
    Image.new("RGB", (1500, 600), "gray").save(output, "PNG")
    return output.getvalue()

@pytest.fixture
def draft():
    return dict(category="Pothole", title="Repair road", description="A depression is visible. Suggested severity is Medium.", severity="Medium", visual_evidence="Road depression visible.", needs_review=False)

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    mocked = MagicMock()
    mocked.__enter__.return_value = mocked
    monkeypatch.setattr(ai, "OpenAI", MagicMock(return_value=mocked))
    return mocked

def response(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

@pytest.mark.parametrize('category', ['Pothole', 'Garbage', 'Unknown', 'Streetlight'])
def test_valid_category(photo, draft, client, category):
    draft['category'] = category
    client.chat.completions.create.return_value = response(json.dumps(draft))
    result = ai.analyze_image(photo)
    assert result['category'] == category
    assert result['needs_review'] == (category in ['Unknown', 'Streetlight'])

def test_retry_then_success(photo, draft, client):
    client.chat.completions.create.side_effect = [response('bad json'), response('```json\n' + json.dumps(draft) + '\n```')]
    assert ai.analyze_image(photo)['title'] == draft['title']
    assert client.chat.completions.create.call_count == 2

@pytest.mark.parametrize('changes', [{'category':'Other'}, {'severity':'Urgent'}, {'needs_review':'false'}, {'title':''}, {'title':'x'*81}])
def test_invalid_schema_retries(photo, draft, client, changes):
    draft.update(changes)
    client.chat.completions.create.return_value = response(json.dumps(draft))
    with pytest.raises(ValueError): ai.analyze_image(photo)
    assert client.chat.completions.create.call_count == 2

def test_api_failure(photo, client):
    client.chat.completions.create.side_effect = APIConnectionError(request=httpx.Request('POST', 'https://example.test'))
    with pytest.raises(RuntimeError, match='report manually'): ai.analyze_image(photo)

def test_missing_key(photo, monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'openai')
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='not configured'): ai.analyze_image(photo)

def test_demo(photo, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    assert ai.analyze_image(photo)['needs_review'] is True

@pytest.mark.parametrize('content', [b'not a photo', b'x'*(5*1024*1024+1), b''], ids=['invalid','oversized','empty'])
def test_bad_images(content):
    with pytest.raises(ValueError): ai.prepare_image(content)

def test_resize(photo):
    with Image.open(io.BytesIO(ai.prepare_image(photo))) as image:
        assert max(image.size) <= 1024 and image.format == 'JPEG'

def test_unsupported_real_image():
    output = io.BytesIO()
    Image.new('RGB', (10,10)).save(output, 'BMP')
    with pytest.raises(ValueError, match='supported'): ai.prepare_image(output.getvalue())


def test_invalid_json_twice(photo, client):
    client.chat.completions.create.return_value = response('not JSON')
    with pytest.raises(ValueError, match='twice'): ai.analyze_image(photo)
    assert client.chat.completions.create.call_count == 2

def test_invalid_api_key_does_not_leak(photo, client):
    from openai import AuthenticationError
    reply = httpx.Response(401, request=httpx.Request('POST','https://example.test'))
    client.chat.completions.create.side_effect = AuthenticationError('secret-key-must-not-appear', response=reply, body=None)
    with pytest.raises(RuntimeError) as caught: ai.analyze_image(photo)
    assert 'secret-key' not in str(caught.value)


def test_exhausted_credits_message(photo, client):
    from openai import RateLimitError
    reply = httpx.Response(429, request=httpx.Request('POST','https://example.test'))
    client.chat.completions.create.side_effect = RateLimitError('private-provider-message', response=reply,
        body={'code':'credit_balance_exhausted','type':'insufficient_quota'})
    with pytest.raises(RuntimeError, match='credits are exhausted') as caught:
        ai.analyze_image(photo)
    assert 'private-provider-message' not in str(caught.value)


def test_gemini_endpoint_and_model(photo, draft, client, monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-placeholder')
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-2.5-flash')
    client.chat.completions.create.return_value = response(json.dumps(draft))
    assert ai.analyze_image(photo)['category'] == 'Pothole'
    assert ai.OpenAI.call_args.kwargs['base_url'] == 'https://generativelanguage.googleapis.com/v1beta/openai/'
    assert client.chat.completions.create.call_args.kwargs['model'] == 'gemini-2.5-flash'

def test_gemini_quota_message(photo, client, monkeypatch):
    from openai import RateLimitError
    monkeypatch.setenv('AI_PROVIDER', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-placeholder')
    reply = httpx.Response(429, request=httpx.Request('POST','https://example.test'))
    client.chat.completions.create.side_effect = RateLimitError('private text', response=reply, body=None)
    with pytest.raises(RuntimeError, match="Gemini's request or free-tier quota"):
        ai.analyze_image(photo)
