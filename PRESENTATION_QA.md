# Fifteen likely judge questions

1. **Why use a pretrained multimodal model instead of training one?**
   It already understands images and text. Training requires a labelled dataset,
   compute and evaluation time that we do not have for this MVP.

2. **What if the category is wrong?**
   The citizen can edit it. Unknown and all streetlight drafts are flagged for
   review, and every submission requires the citizen's confirmation.

3. **What if the model returns invalid output?**
   We check JSON, keys, types, allowed values and text limits. We retry once for
   an invalid answer, then offer retry or manual entry.

4. **What happens with no internet, a timeout or a missing API key?**
   The app shows a friendly message and manual reporting remains available.
   Optional demo mode returns a clearly labelled simulated example.

5. **Can a streetlight photo prove it is broken?**
   Usually not. The prompt asks for visible evidence, and our code conservatively
   flags every streetlight result for human review, even when a fault is described.

6. **How is privacy handled?**
   We resize images and strip metadata, but people and number plates may remain.
   AI analysis sends the image to OpenAI; manual entry stays local. Future work
   includes consent, automatic blurring, secure storage and a retention policy.

7. **How do you stop fake reports or spam?**
   We require a real image, location and citizen review, but these do not prove
   authenticity. Rate limits, real accounts and moderation are future work.

8. **Can you detect duplicate complaints?**
   Not yet. We could compare location, time and image similarity, then let a
   reviewer group reports without deleting useful citizen evidence.

9. **Why Streamlit and SQLite? How would it scale?**
   They keep a small Python prototype easy to build and explain. For scale,
   we would use FastAPI, PostgreSQL, object storage and real authority integration.

10. **What is your accuracy? How would you measure it?**
    We do not claim a percentage. We would create a labelled, diverse test set,
    measure per-category precision/recall and review uncertain cases and errors.
    Mocked unit tests verify code behavior, not visual recognition accuracy.

11. **Who is responsible for AI mistakes or bias?**
    AI only suggests. Citizens review and real authorities would verify before
    acting. We would evaluate different locations, lighting and infrastructure
    and monitor which groups experience more errors.

12. **Does the app send a complaint to the municipality?**
    No. It saves a local complaint and suggests a generic department. Official
    forwarding would require a real partnership and secure integration.

13. **Are the admin login and tracking IDs production-secure?**
    No. A shared password is demo-only. A tracking ID gives access to that report;
    it is not private authentication. Production needs accounts, authorization,
    rate limits and proper access controls.

14. **What is the impact or business potential?**
    The goal is less reporting effort and clearer follow-up for citizens.
    Municipalities or campus/facility teams could pilot it. We would measure
    time to report and resolution outcomes; no measured impact is claimed yet.

15. **What would you build next?**
    GPS and maps, notifications, duplicate detection, Kannada/Hindi support,
    privacy blurring and official authority workflows. None is implemented now.
