# CivicEye AI

Turn a civic issue photo into an editable complaint and follow its local status.
Built for a beginner-friendly hackathon demonstration with Python, Streamlit,
the official OpenAI SDK, Pillow, python-dotenv and SQLite.

## Run on Windows (PowerShell)

```powershell
cd D:\civic_eye_prj\civiceye-ai
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Python 3.10 or newer is required. Using the virtual environment's Python directly
avoids PowerShell activation restrictions. Open http://localhost:8501.
If using an existing environment: `pip install -r requirements.txt`, then
`streamlit run app.py`.

## Environment settings

| Variable | Meaning |
| --- | --- |
| GEMINI_API_KEY | Your own key, used on the server only; blank allows manual reporting |
| GEMINI_MODEL | Vision-capable Chat Completions model, default gemini-3.1-flash-lite |
| ADMIN_PASSWORD | Choose a password for the demo admin; blank disables admin |
| DEMO_MODE | true = explicitly labelled simulated pothole draft; false = real AI |

Restart Streamlit after changing `.env`. No `.env` or API key is shipped.
For an offline demonstration set DEMO_MODE=true and set ADMIN_PASSWORD.
The simulated result never analyses the photo; correct its fields before saving.
Manual entry is available regardless of the API or demo mode.

## Features and use

1. Report: upload a valid image under 5 MB, enter location and optional notes,
   generate an AI draft or enter a manual report. Edit category, title,
   description and severity. Check the confirmation box and submit.
2. Track: paste the CE tracking ID. Case and outer spaces do not matter.
   See the saved photo, citizen location, timestamps and status history.
3. Admin (Demo): sign in with the configured password, filter complaints,
   then advance Submitted → In Progress → Resolved. Tracking reads fresh data
   on lookup/rerun; click Look up complaint again to refresh an already open tab.

Suggested departments are generic routing suggestions. Nothing is sent to a real
municipal authority. Resolved is a demo admin's status, not independent verification.
All streetlight and Unknown drafts require review. All reports require citizen
confirmation. Severity is a suggestion, not a safety assessment.

## Architecture

```text
Citizen browser
    ↓
app.py (Streamlit UI + session state)
    ├── ai_engine.py → Pillow validation → resized JPEG → Google Gemini → JSON validation
    │                  ↳ labelled demo result / manual route on failure
    ├── database.py → SQLite complaints + status_history (one transaction)
    └── uploads/ → generated JPEG filename, no original name or EXIF metadata
config.py → shared choices, departments, limits, environment settings
```

The AI receives only the processed image and instructions, not the location or
citizen notes. Location is saved separately from the citizen's input. The prompt
prohibits invented locations, but human review is still needed for hallucinations.
One invalid JSON/schema result triggers one retry. API errors do not trigger hidden
simulated output. Each API request has a 45-second timeout and SDK retries are
disabled; a schema retry can take approximately 90 seconds in total.
IDs use eight UUID4 hexadecimal characters. SQLite's primary key prevents duplicates,
and collisions are retried. A rare inability to allocate an ID returns a retry message.

## Tests

```powershell
cd D:\civic_eye_prj\civiceye-ai
.\.venv\Scripts\python.exe -m pytest -q
```

Tests mock the AI, use synthetic image bytes only for format tests, and use isolated
temporary databases/uploads. No real API key is required. They cover JSON and schema
validation, retry, simulated mode, service failures, invalid/oversized/unsupported
images, resize, DB CRUD, edited values, ID collisions, status history, wrong passwords,
Streamlit submission, tracking and manual fallback. Browser checks verify desktop
and narrow layouts separately. Mocked category tests do not measure model accuracy.

## Explain this code in 30 seconds

- app.py: displays the three screens and preserves editable fields in session state.
- ai_engine.py: validates the photograph, calls the model and checks the six returned fields.
- database.py: saves complaints and every status change using parameterised SQL.
- config.py: keeps category, severity, status, department and limit choices together.
- tests/: checks logic and real Streamlit widgets without calling the internet.
- requirements.txt: lists the small set of libraries needed to run and test.
- .env.example: shows server-side settings without including secrets.
- .streamlit/config.toml: sets the upload limit and readable colours.
- data/ and uploads/: hold runtime records and metadata-free resized JPEGs.
- DEMO_SCRIPT.md and PRESENTATION_QA.md: help you present and answer judges honestly.

## Limitations and responsible AI

This is a local MVP. Shared-password admin protection has no user accounts, rate
limiting, audit identities or production security. Anyone with a tracking ID can
view that complaint; short IDs must not be treated as private access tokens.
Photos can contain people or number plates. AI mode sends images to Google Gemini;
manual reporting stays local. This MVP has no automatic blurring or retention policy.
Records and resized uploads stay on disk until the operator intentionally removes
them. Do not expose this demo publicly with sensitive images.
The AI can misclassify or invent details; schema checks establish structure, not
truth. Streetlight review is deliberately conservative even for visible faults.
No labelled evaluation dataset or accuracy percentage is claimed. Images are
resized, so tiny details may be lost. SQLite suits a small local demonstration,
not a city-scale, multi-user deployment. Browser tab switches alone may not rerun
Streamlit; lookup or another interaction refreshes saved status. Real-image model
classification and live API access require your own configured key and test photos.

## Future scope (not built)

GPS capture, maps, notifications, duplicate/spam detection, automatic privacy blurring,
multilingual Kannada/Hindi support, real authentication and authority integrations.
For scale: a separate FastAPI service, PostgreSQL, object storage and secure municipal
workflows would replace the local MVP infrastructure.

## One-page pitch outline

**Problem (20 seconds):** Reporting potholes, garbage and other issues takes effort,
and citizens often cannot see what happens afterwards.

**Solution (25 seconds):** CivicEye turns a photo into a structured draft, lets the
citizen correct it and provides a tracking ID. It also suggests a generic department.

**Live demo (90 seconds):** Upload a pothole image at Rajajinagar, Bengaluru; show
and edit the draft; submit; copy the ID; track it; use demo admin to update status.

**Tech & AI approach (25 seconds):** A pretrained multimodal model avoids training
a new model. Pillow prepares the image; strict JSON validation and one retry make
the output usable. Streamlit and SQLite keep the architecture easy to explain.

**Responsible AI (20 seconds):** AI suggests and citizens review. Unknown issues
and streetlights are flagged. There is no confidence score or authority verification.
Images can contain private information, so consent, blurring and retention matter.

**Impact (15 seconds):** The intended benefit is less typing and clearer follow-up.
These are goals, not measured results. No pilot or impact metrics are claimed.

**Future scope (15 seconds):** Add GPS, maps, duplicate detection, multilingual
support and official authority integration. Today there is no forwarding, live
notification, mobile APK, trained custom model or production authentication.


## Gemini integration update

CivicEye now defaults to Google Gemini (`AI_PROVIDER=gemini`, `GEMINI_MODEL=gemini-3.1-flash-lite`). Set GEMINI_API_KEY in .env. The existing OpenAI Python library acts as a client for Google's documented compatibility endpoint; requests go to Google, not OpenAI. No extra SDK is needed. OpenAI remains optional via AI_PROVIDER=openai and its own settings. Restart after changing .env. Free-tier limits apply; Google states that free-tier content may be used to improve its products. Use non-sensitive demo photos. See https://ai.google.dev/gemini-api/docs/openai and https://ai.google.dev/gemini-api/docs/pricing.
