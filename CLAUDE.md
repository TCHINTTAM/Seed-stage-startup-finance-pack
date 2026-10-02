# CLAUDE.md — rules for working on this project

## What this project is
A "Seed-stage startup finance pack": an interactive Streamlit web app that models
**LedgerLoop**, a **fictional** UK B2B fintech (accounting automation software for
small businesses, 15 staff, £2m seed raised, monthly subscriptions).
The model runs monthly for 36 months.

The owner is a student with little Python experience building a portfolio project
for startup finance internships. Act as a **tutor as well as a builder**: they must
understand everything you make. Explain in plain English and avoid jargon, or
define it when you use it.

## Rules
1. **Keep code simple and beginner-readable**: plain functions, no classes,
   plain-English comments.
2. **Calculations live in `model.py`**, separate from the app layout in `app.py`,
   so the finance logic can be read on its own. `app.py` should not do finance maths.
3. **All default assumptions live in `assumptions.py`**, each with a comment
   explaining what it is and why that value was chosen.
4. **Consistent units**: money in GBP (£), all figures monthly unless clearly
   labelled otherwise (e.g. "annual salary"), percentages stored as decimals
   (5% = 0.05).
5. **Work in stages.** At the end of each stage, STOP, explain what was built in
   3-5 plain-English bullets, and wait for the owner to reply "next".
6. **Label LedgerLoop as fictional everywhere** it appears (app, README, exports).
7. Credit Claude Code in the app's "About" section and the README.

## File structure
- `assumptions.py` — default assumptions with explanations
- `model.py` — finance calculations (revenue, costs, cash/runway, unit economics, scenarios)
- `app.py` — Streamlit app (sidebar, charts, scenario comparison, investor update, Excel download)
- `requirements.txt` — Python libraries needed
- `README.md` — project write-up (Stage 8)

## Stages
1. Setup  2. Assumptions (needs approval)  3. Revenue model  4. Costs, cash & runway
5. Unit economics & scenarios  6. The app  7. Quiz (skeptical founder, 8 questions,
one at a time, don't give answers first)  8. Publish (README, GitHub, Streamlit Cloud)

## How to run
```
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
