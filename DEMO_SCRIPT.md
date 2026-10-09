# Three-minute CivicEye AI demo

## Pre-demo checklist

- Install dependencies and run `python -m pytest -q` from the project folder.
- Configure `.env`: working GEMINI_API_KEY, gemini-3.1-flash-lite, a chosen ADMIN_PASSWORD.
  Run one real image analysis before presenting; do not show the key on screen.
- Keep three permitted test photos ready: pothole, garbage and an unrelated image.
  Also check a streetlight photo to show the review safeguard.
- Start `streamlit run app.py`; open http://localhost:8501. Use 100% browser zoom.
- Try a narrow browser or phone-width view; expand/collapse the sidebar as needed.
- Optional fresh demo database: stop the app, back up needed files, then from the
  project folder run `Remove-Item -LiteralPath .\data\complaints.db`.
  This permanently deletes reports/history; do it only for disposable demo data.
  Uploaded files remain and should be managed separately. Restart to create tables.
- Keep Plan B ready: DEMO_MODE=true or the Enter report manually button.

## 0:00–0:25 — Problem and solution

Say: “A citizen sees a pothole, but writing and following up on a complaint takes
effort. CivicEye AI helps create a draft from a photo, lets the citizen correct it,
and gives them a tracking ID. This is a local demo, not a municipal portal.”

Click **Report an Issue**. Click the photo upload control and choose a pothole photo.
Type **Rajajinagar, Bengaluru** in Location. Optional notes: “Near my daily route.”

## 0:25–1:15 — AI draft and citizen review

Click **Generate AI draft**. Say: “The image is checked, resized and sent to a
pretrained vision-capable model. The model suggests a category, title, description
and severity. Our code checks the JSON structure before displaying it.”

Point to visual evidence, category, title, description and severity. Say:
“These are suggestions. The person reporting must check the photo and correct
anything inaccurate. Unclear issues and streetlights need careful review.”

Edit the title to **Pothole repair requested in Rajajinagar**. Explain that the
location comes from the citizen. Show the department suggestion. Tick
**I have checked the photo, category and complaint details.**

If the real model says Unknown, say: “The model is unsure. We can review the photo
and select Pothole ourselves. We do not pretend every prediction is correct.”

## 1:15–1:50 — Submit and track

Click **Submit complaint**. Copy the ID from the code box's copy control.
Say: “The report and initial history are saved in SQLite. This ID identifies
the report, and the app has not forwarded it to an authority.”

Click **Track Complaint**, paste the ID and click **Look up complaint**.
Point to Submitted, the edited text, citizen location, photo and initial timeline.

## 1:50–2:35 — Admin and history

Click **Admin (Demo)**. Enter your chosen demo password and click **Sign in to admin**.
Select the new tracking ID in **Complaint to manage**.
Say: “This is shared-password demo protection. Real deployment needs proper accounts.”

Click **Mark as In Progress**. Click Track Complaint and **Look up complaint**.
Show In Progress and the added timeline entry. Return to admin, click
**Mark as Resolved**, then look up the ID again on Track Complaint.
Say: “Every status change persists and appears in history. Resolved here is a
demo admin's update, not independent verification of the repair.”

## 2:35–3:00 — Honest scope and next steps

Say: “We built upload, editable drafts, manual fallback, local storage and tracking.
Next we would add GPS, multilingual reporting, duplicate detection and official
authority integration. We have not measured model accuracy or real-world impact yet.”

## Plan B if the internet/API fails

1. Read the friendly error and click **Enter report manually**. Select Pothole,
   write a factual title/description, choose severity, confirm and submit normally.
2. Or stop Streamlit, set DEMO_MODE=true in `.env` and restart. Say explicitly:
   “Demo mode: this is a simulated pothole example, not analysis of the photo.”
   Check and correct the canned fields. Submission, tracking and admin still work.
3. If no API key is configured, manual reporting still works. Never display or
   paste the API key during the presentation.


## Gemini integration update

CivicEye now defaults to Google Gemini (`AI_PROVIDER=gemini`, `GEMINI_MODEL=gemini-3.1-flash-lite`). Set GEMINI_API_KEY in .env. The existing OpenAI Python library acts as a client for Google's documented compatibility endpoint; requests go to Google, not OpenAI. No extra SDK is needed. OpenAI remains optional via AI_PROVIDER=openai and its own settings. Restart after changing .env. Free-tier limits apply; Google states that free-tier content may be used to improve its products. Use non-sensitive demo photos. See https://ai.google.dev/gemini-api/docs/openai and https://ai.google.dev/gemini-api/docs/pricing.
