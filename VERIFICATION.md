# Verification record

Verified locally on Windows with Python 3.14.8, Streamlit 1.65.0 and OpenAI SDK 2.54.0.

- Scaffold: started the Streamlit server successfully on port 8501.
- AI core and database: 26 initial tests passed before UI integration.
- P0 screens: reporting and tracking tests passed before admin was added.
- Final suite: 36 tests, including mocked AI responses, invalid JSON retry,
  API failure/authentication failure, image validation, CRUD, collision retry,
  edited draft submission, manual fallback, wrong admin password and status history.
- Syntax: compileall passed for the four application modules.
- Browser: inspected report and tracking controls at desktop and 390 × 844 viewport.
  Three tabs remain visible and controls fit the narrow width. Upload control shows 5 MB.
  This is responsive-browser inspection, not testing on a physical phone.
- No real API request was made and no user's key was read. Category tests use mocked
  responses; real pothole/garbage/unrelated-photo predictions are not verified.
- No municipal integrations, GPS, maps, notifications or production auth were added.

To reproduce: `python -m pytest -q` from this folder after installing requirements.
Tests isolate database and uploaded files in temporary directories.
Before a live AI presentation, configure your key and test your own permitted images.


## Gemini integration update

CivicEye now defaults to Google Gemini (`AI_PROVIDER=gemini`, `GEMINI_MODEL=gemini-3.1-flash-lite`). Set GEMINI_API_KEY in .env. The existing OpenAI Python library acts as a client for Google's documented compatibility endpoint; requests go to Google, not OpenAI. No extra SDK is needed. OpenAI remains optional via AI_PROVIDER=openai and its own settings. Restart after changing .env. Free-tier limits apply; Google states that free-tier content may be used to improve its products. Use non-sensitive demo photos. See https://ai.google.dev/gemini-api/docs/openai and https://ai.google.dev/gemini-api/docs/pricing.
Final Gemini verification: a live synthetic blank-image request using gemini-3.1-flash-lite returned valid six-field JSON, category Unknown, and needs_review true. Earlier statements about no live API calls describe the original OpenAI build. Real civic-photo recognition has not yet been evaluated.
