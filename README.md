# CampusLedger | NSS College of Engineering
CSE · Semester 5 · A Division • Field Notes Studio (bento grid)

## 1. Show the teacher: no installation
Open index.html in Chrome or Edge. This is the self-contained, fictional NSS presentation. It works even when offline. Click Demo guide for the five-minute walkthrough or to reset the presentation. The PDF in handouts/ is a printable companion. Use sample certificates only.

## 2. Publish the teacher demo from VS Code
Extract the ZIP and open the folder containing this README in VS Code. Commit its contents (not the ZIP) and publish the repository. In repository Settings → Pages, choose Deploy from a branch, select the published branch and /(root), then Save. When it finishes, use Visit site. The root index.html is the entire browser demo; the Python server does NOT run on GitHub Pages. Visitors do not share demo records. No permanent public URL is created by extracting this ZIP.

## 3. Run the complete multi-page application with separate logins
Install Python 3.10+ (standard library only). In VS Code, open Terminal → New Terminal from this folder. Run `python portal.py` (Windows: `py portal.py`; macOS/Linux: `python3 portal.py`). Visit http://localhost:8003/ . Stop with Ctrl+C. The bundled launcher binds to the local computer by default; set PORT if 8003 is occupied. The .vscode/launch.json configuration can also run it using the Python debugger extension.

The server serves site/index.html, not the standalone root index.html. The first run creates campus.sqlite and seeds fictional accounts. The app has Student and Teacher roles; choose the matching role on sign-in. The separate, password-free demo buttons use browser-local sample data, not the SQLite accounts. Register numbers are not passwords or login names.

| Role | Name | Email used for login | Register number |
|---|---|---|---|
| Student | Aarav Nair | aarav@campus.edu | NSS24CS001 |
| Student | Ananya S | ananya@campus.edu | NSS24CS002 |
| Student | Arjun Thomas | arjun@campus.edu | NSS24CS003 |
| Teacher | Anjali Menon | anjali@campus.edu | Faculty adviser |

All seeded accounts use the DEMO password `Campus2024!`. Do not expose this development server publicly or use real personal information with these accounts.

## Project map
- index.html — standalone NSS faculty presentation, ready for offline use or Pages.
- portal.py — multi-user Python server, role checks, file storage, review history and SQLite initialization.
- site/student/, site/teacher/ — dedicated HTML pages for the two roles.
- site/*.js and site/*.css — shared workflows, searchable handbook, dashboards, bento layout and styling.
- site/assets/ — local fonts, icons, illustrations, KTU 2024 handbook PDF and activity catalogue CSV.
- site/award-rules.json — server-side points and limit lookup.
- handouts/ — one-page faculty walkthrough PDF.

The standalone presentation embeds its own styling, scripts and sample data; changes to site/ do not automatically rebuild index.html. The two entry points are intentionally independent. Database files, uploaded certificates, real user records, tokens and previous design experiments are not part of this release. The .gitignore keeps the generated database out of Git. A production deployment requires proper account provisioning, access scoping, backups and hosting review.
