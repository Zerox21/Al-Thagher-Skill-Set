 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index 725792545444c3198c306459cfe2900cf7a30017..734e4c06aa5e605229dad0248c67fb2d172a1436 100644
--- a/README.md
+++ b/README.md
@@ -1,81 +1,123 @@
-# Al Thaghr Skill Tests (prototype)
+# Al Thaghr Skill Tests (production-ready prototype)
 
 This project implements your workflow:
 
 - Student login by ID + PIN + must choose teacher  
 - Only pre-registered Al Thaghr IDs can sign in  
 - Weekly access limit (default: 1 attempt/week)  
 - Timed tests (client countdown + server enforcement)  
 - Skill gating: teacher unlocks skills per student  
 - Question tool to add questions (MCQ, multi-select, short text, image, interactive video cue points)  
 - PDF report generated after each test (answers + time consumed + top lacking skills)  
 - Dashboards: Chairman / Teacher / Student  
 - Teacher remediation uploads per skill (PDF/PP/Word/Video), visible to student
 
 ## Run locally
 
 ### Windows (PowerShell)
 ```powershell
 cd althaghr-skill-tests
 python -m venv .venv
 .\.venv\Scripts\activate
 pip install -r requirements.txt
 python run.py
 ```
 
 ### Mac/Linux
 ```bash
 cd althaghr-skill-tests
 python3 -m venv .venv
 source .venv/bin/activate
 pip install -r requirements.txt
 python run.py
 ```
 
 Open: http://127.0.0.1:5000
 
 ## Default demo accounts (change immediately)
 - Chairman: `chairman` / PIN `1234`
 - Teacher: `t001` / PIN `1234`
 - Student: `s001` / PIN `1234` (choose Teacher A)
 
+## Deployment (Render)
+1) Create a new **Web Service** from this repo.
+2) Runtime: **Python 3.11**
+3) Build command:
+```bash
+pip install -r requirements.txt
+```
+4) Start command:
+```bash
+gunicorn wsgi:app
+```
+5) Add a Postgres database and set `DATABASE_URL` in the service.
+6) Add environment variables (see list below).
+
+### Environment variables
+Required:
+- `SECRET_KEY`
+- `DATABASE_URL` (Render Postgres)
+
+Recommended:
+- `APP_VERSION` (shows in footer)
+- `BRAND_NAME`, `BRAND_TAGLINE`, `BRAND_PRIMARY_COLOR`, `BRAND_LOGO_PATH`, `BRAND_FAVICON_PATH`
+- `WEEKLY_LIMIT` (default `1`)
+- `WEEKLY_LIMIT_SCOPE` (`student` or `student_skill`)
+- `DEFAULT_TEST_DURATION_MIN`
+- `STORAGE_DIR` (optional; defaults to `instance/storage`)
+
+Optional email (PDF reports):
+- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `SMTP_TLS`
+
+## How to create chairman
+The seed script runs on first boot and creates a default chairman.
+Update the credentials immediately after first login.
+
 ## Import students (allowlist)
 Chairman → Users & imports → Import CSV
 
 CSV columns:
 - required: `student_id,name`
 - optional: `pin,teacher_id`
 
 Example:
 ```csv
 student_id,name,pin,teacher_id
 s002,Student Two,1234,t001
 s003,Student Three,7788,t001
 ```
 
 ## Add skills
 Chairman → Skills
 
 ## Add questions
 Chairman or Teacher → Question tool
 
 Supported types:
 - `mcq_single` (answer: correct option index, 0-based)
 - `mcq_multi` (answer: comma-separated indices, e.g. `0,2`)
 - `true_false` (options True/False; answer 0 or 1)
 - `short_text` (answer: expected text)
 - `image_mcq_single` (meta: {"image_url":"/static/uploads/x.png"})
 - `video_cued_mcq_single` (meta: {"video_url":"/static/uploads/x.mp4","cues":[5,12]})
 
 ### Media files
 Copy images/videos to: `app/static/uploads/`
 Then reference them like: `/static/uploads/filename.ext`
 
 ## Weekly access settings
 Copy `.env.example` to `.env` and edit:
 - `WEEKLY_LIMIT=1`
 - `WEEKLY_LIMIT_SCOPE=student` (default, across all skills) OR `student_skill`
 
 ## PDF sending to teacher
 PDF is always generated + downloadable from teacher dashboard.
 Optional auto-email: fill SMTP values in `.env` and set teacher email.
+
+## Next Improvements
+- Question bank tagging and difficulty levels
+- Item analysis (discrimination index)
+- Proctoring-lite (fullscreen + focus loss logging)
+- Better math rendering (MathJax/KaTeX)
+- S3 storage for media/reports
+- Audit logs and role permissions matrix
 
EOF
)
