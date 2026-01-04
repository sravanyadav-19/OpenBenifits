# OpenBenefits

OpenBenefits is a small web application that helps residents in India discover
public schemes they may be eligible for, using a simple rule-based engine and
an assistant that explains results in plain language.

## Features

- Asks a few simple questions (age, work status, household income, location).
- Matches answers against a JSON ruleset of government schemes.
- Shows a clear list of possible schemes and why they appear.
- Local assistant answers common questions about the schemes and process.
- Architecture is ready to plug in Google Gemini / Google GenAI in the future.

## Tech stack

- Python, Flask
- HTML, Jinja2 templates, custom CSS
- Rules stored in `rules/schemes.v1.json`

## Running locally

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py


Adjust country/wording as you like.

---

## 4. Remove unused files/folders if any

From the tree you showed:

- `openbenefits/openbenefits/static/js` looked empty – you can safely delete that empty `openbenefits` subfolder if it’s not used.
- If you are no longer using `static/js/assistant.js` or `static/js/main.js` (because assistant JS is inline in `results.html`), you can either:
  - Remove them, or
  - Leave them but empty with a small comment (not necessary, but cleaner to remove).

Only do this if you’re sure templates don’t reference them.

---

## 5. Final quick manual checks before push

In your browser:

1. Go to `/questions`:
   - Try 2–3 different profiles:
     - Student, low income → see scholarships/education schemes.
     - Unemployed youth → see PMKVY/PM‑DAKSH, etc.
     - Senior citizen → see pension schemes.
2. On `/results`:
   - Confirm:
     - Scheme list appears.
     - “Why this scheme is shown” details open.
     - Assistant:
       - Answers “Why are there not more schemes for me?”
       - Answers “What should I check before applying?”
       - Answers “Explain [one of the schemes]”.

If all that works without errors in the browser console, you’re ready.

---

## 6. Push to GitHub

From project root:

```bash
git init
git add .
git commit -m "Initial commit: OpenBenefits eligibility checker with local assistant"
git branch -M main
git remote add origin https://github.com/sravanyadav-19/OpenBenifits.git
git push -u origin main
