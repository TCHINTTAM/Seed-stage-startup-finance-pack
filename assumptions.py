# assumptions.py
# ---------------------------------------------------------------------------
# Default assumptions for LedgerLoop - a FICTIONAL UK B2B fintech that sells
# accounting automation software to small businesses on monthly subscriptions.
# LedgerLoop is not a real company. These numbers are illustrative only.
#
# Units used everywhere in this project:
#   - Money is in GBP (£)
#   - Figures are MONTHLY unless the name says otherwise (e.g. annual_salary)
#   - Percentages are stored as decimals (5% = 0.05)
#
# The app's sidebar starts from these values, and anyone can change them there.
# ---------------------------------------------------------------------------

COMPANY_NAME = "LedgerLoop (fictional)"

# How many months the model runs for. 36 months = 3 years.
MONTHS = 36

# Month 1 of the model is January 2027. Used only to put real-looking dates
# on tables and the investor update.
START_YEAR = 2027
START_MONTH = 1  # 1 = January


# --- A. Starting position ----------------------------------------------------

# Cash in the bank at the start of month 1. The £2m seed round has just landed.
OPENING_CASH = 2_000_000

# Paying customers LedgerLoop already has before month 1.
# 150 x £149 = about £22k MRR, typical for a UK seed-stage SaaS company.
STARTING_CUSTOMERS = 150


# --- B. Revenue --------------------------------------------------------------

# Monthly subscription price per customer (one customer = one small business).
# Basic accounting tools cost ~£15-60/month; LedgerLoop saves hours of
# bookkeeping worth £300+/month, so £149 is a reasonable price.
PRICE_PER_MONTH = 149

# New customers won in month 1. About one per working day.
NEW_CUSTOMERS_MONTH_1 = 25

# How fast the number of NEW customers grows each month.
# 0.05 = 5% per month, which compounds to about 80% per year (1.05^12 = 1.8).
NEW_CUSTOMER_GROWTH = 0.05

# Share of existing customers who cancel each month.
# 0.03 = 3% per month, about 31% per year. Small businesses churn more than
# big ones (they close down, switch tools or cut costs); 3-7% is typical.
MONTHLY_CHURN = 0.03

# Share of revenue left after the direct costs of serving customers
# (cloud hosting, open-banking data fees, payment processing, support tools).
# Software is usually 75-85%; fintech data fees pull it a little lower.
GROSS_MARGIN = 0.80


# --- C. People ---------------------------------------------------------------

# Extra cost on top of salary for each employee: UK employer National
# Insurance (15% above £5,000/year), employer pension (3% minimum), plus a
# small allowance for benefits and equipment. 0.20 = 20% on top of salary.
EMPLOYER_ON_COSTS = 0.20

# The headcount plan. Each row is one person:
#   role          - job title
#   start_month   - the first month they are paid (1 = already on the team)
#   annual_salary - yearly salary in £, BEFORE on-costs
HEADCOUNT_PLAN = [
    # Current team of 15 (all start in month 1).
    # Founders pay themselves below market, which is normal at seed stage.
    {"role": "Co-founder & CEO",         "start_month": 1, "annual_salary": 70_000},
    {"role": "Co-founder & CTO",         "start_month": 1, "annual_salary": 70_000},
    {"role": "Software engineer",        "start_month": 1, "annual_salary": 65_000},
    {"role": "Software engineer",        "start_month": 1, "annual_salary": 65_000},
    {"role": "Software engineer",        "start_month": 1, "annual_salary": 65_000},
    {"role": "Software engineer",        "start_month": 1, "annual_salary": 65_000},
    {"role": "Software engineer",        "start_month": 1, "annual_salary": 65_000},
    {"role": "Software engineer",        "start_month": 1, "annual_salary": 65_000},
    {"role": "Product designer",         "start_month": 1, "annual_salary": 55_000},
    # Fintech handles client financial data, so it needs compliance early.
    {"role": "Compliance & risk lead",   "start_month": 1, "annual_salary": 55_000},
    {"role": "Sales executive",          "start_month": 1, "annual_salary": 45_000},
    {"role": "Sales executive",          "start_month": 1, "annual_salary": 45_000},
    {"role": "Marketing manager",        "start_month": 1, "annual_salary": 45_000},
    {"role": "Finance & operations",     "start_month": 1, "annual_salary": 45_000},
    {"role": "Customer success",         "start_month": 1, "annual_salary": 35_000},
    # Planned hires paid for by the seed round (team grows from 15 to 21).
    {"role": "Software engineer",        "start_month": 4,  "annual_salary": 65_000},
    {"role": "Sales executive",          "start_month": 7,  "annual_salary": 45_000},
    {"role": "Customer success",         "start_month": 10, "annual_salary": 35_000},
    {"role": "Software engineer",        "start_month": 13, "annual_salary": 65_000},
    {"role": "Sales executive",          "start_month": 16, "annual_salary": 45_000},
    {"role": "Growth marketer",          "start_month": 19, "annual_salary": 50_000},
]


# --- D. Other monthly costs -------------------------------------------------

# Internal software and tools (Slack, Google Workspace, GitHub, CRM,
# accounting) plus development servers. Customer-facing hosting is NOT here;
# it is inside the cost of revenue (the 20% that gross margin leaves out).
SOFTWARE_COST = 5_000

# Co-working desks in London: about £400 per desk x 15 people.
OFFICE_COST = 6_000

# Marketing spend in month 1 (paid ads, content, events).
# £25,000 / 25 new customers = £1,000 customer acquisition cost (CAC).
MARKETING_SPEND_MONTH_1 = 25_000

# How fast marketing spend grows each month. 0.04 = 4% per month.
# Slightly slower than new-customer growth (5%), assuming word of mouth
# makes acquisition a little more efficient over time.
MARKETING_GROWTH = 0.04


# --- E. Scenarios ------------------------------------------------------------

# Slow growth: new-customer growth is multiplied by this (0.5 = halved).
# Marketing spend stays the same, so each customer costs more to win.
SLOW_GROWTH_FACTOR = 0.5

# Aggressive hiring: this many extra people join in this month,
# each on this salary (a mix of engineers and sales). Revenue is unchanged.
AGGRESSIVE_EXTRA_HIRES = 5
AGGRESSIVE_HIRE_MONTH = 6
AGGRESSIVE_HIRE_SALARY = 60_000
