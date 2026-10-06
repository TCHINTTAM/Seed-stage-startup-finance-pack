# app.py
# ---------------------------------------------------------------------------
# The Streamlit web app for the LedgerLoop seed-stage finance pack.
# LedgerLoop is a FICTIONAL company.
#
# This file only handles LAYOUT: the sidebar, charts, tables and downloads.
# All the finance maths lives in model.py, and the default numbers live in
# assumptions.py.
#
# Run it with:   streamlit run app.py
#
# How Streamlit works: every time someone moves a slider, Streamlit re-runs
# this whole file from top to bottom with the new values. That's why the
# results update instantly - there's no special "refresh" code.
# ---------------------------------------------------------------------------

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

import assumptions
import model


# Chart colours, picked so they stay distinguishable for colour-blind readers.
# Each scenario and cost category always gets the same colour.
SCENARIO_COLOURS = {
    "Base": "#2a78d6",               # blue
    "Slow growth": "#eb6834",        # orange
    "Aggressive hiring": "#1baf7a",  # aqua
}
COST_COLOURS = {
    "Payroll": "#2a78d6",            # blue
    "Marketing": "#eb6834",          # orange
    "Cost of revenue": "#1baf7a",    # aqua
    "Office": "#eda100",             # yellow
    "Software": "#e87ba4",           # magenta
}
SINGLE_LINE_COLOUR = "#2a78d6"
CASH_OUT_COLOUR = "#e34948"          # red, used only for the "cash runs out" marker


# --- Small helpers for showing numbers nicely --------------------------------

def gbp(value):
    """Format money in a short, readable way: £1.9m, £66.8k, £950."""
    if value is None or pd.isna(value):
        return "–"
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}£{value / 1_000_000:.2f}m"
    if value >= 10_000:
        return f"{sign}£{value / 1_000:.1f}k"
    return f"{sign}£{value:,.0f}"


def format_metric(name, value):
    """Format one value from model.summarise() based on what kind of metric it is."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "–"
    if isinstance(value, str):
        return value
    if "(£)" in name:
        return gbp(value)
    if "growth" in name:
        return f"{value:.1%}"
    if name == "LTV:CAC":
        return f"{value:.1f}x"
    if name == "Runway (months)":
        return str(value)   # a whole number of months, e.g. 20
    if "months" in name:
        return f"{value:.1f}"
    return f"{value:,.0f}"   # customers, headcount


def show_table(df):
    """Show a monthly table with £ columns formatted and decimals rounded."""
    formats = {}
    for column in df.columns:
        if "(£)" in column:
            formats[column] = "£{:,.0f}"
        elif column not in ("Month", "Date", "Headcount"):
            formats[column] = "{:,.1f}"
    st.dataframe(df.style.format(formats, na_rep="–"), hide_index=True)


def make_excel(results, scenario_table, inputs):
    """
    Build an Excel file in memory with one sheet per section.
    BytesIO is a 'file' that lives in memory instead of on disk, so we can
    hand it straight to the download button.
    """
    assumption_rows = []
    for name, value in inputs.items():
        if name != "headcount_plan":
            assumption_rows.append({"Assumption": name, "Value": value})

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"Note": [
            "LedgerLoop is a FICTIONAL company. All numbers are illustrative.",
            "Units: GBP, monthly figures, percentages as decimals (0.05 = 5%).",
            "Built as a student portfolio project with help from Claude Code.",
        ]}).to_excel(writer, sheet_name="Read me", index=False)
        pd.DataFrame(assumption_rows).to_excel(writer, sheet_name="Assumptions", index=False)
        pd.DataFrame(inputs["headcount_plan"]).to_excel(writer, sheet_name="Headcount plan", index=False)
        results["revenue"].round(2).to_excel(writer, sheet_name="Revenue", index=False)
        results["headcount"].round(2).to_excel(writer, sheet_name="Headcount", index=False)
        results["costs"].round(2).to_excel(writer, sheet_name="Costs", index=False)
        results["cash"].round(2).to_excel(writer, sheet_name="Cash and runway", index=False)
        results["unit_economics"].round(2).to_excel(writer, sheet_name="Unit economics", index=False)
        scenario_table.to_excel(writer, sheet_name="Scenarios")
    return buffer.getvalue()


# --- Page setup ---------------------------------------------------------------

st.set_page_config(page_title="LedgerLoop finance pack", page_icon="📒", layout="wide")

st.title("LedgerLoop seed-stage finance pack")
st.warning(
    "**LedgerLoop is a fictional company.** All numbers are illustrative "
    "assumptions for a student portfolio project, not real data.",
    icon="⚠️",
)
st.caption(
    "A 36-month model of a UK B2B fintech selling accounting automation to small "
    "businesses (15 staff, £2m seed, monthly subscriptions). Change the assumptions "
    "in the sidebar and everything updates."
)


# --- Sidebar: the key assumptions ----------------------------------------------
# Each widget starts at the default from assumptions.py.
# Percentages are shown as % on the slider, then divided by 100 so the model
# gets decimals (5% -> 0.05), keeping our units consistent.

st.sidebar.header("Assumptions")
st.sidebar.caption("LedgerLoop (fictional). All money in £, all figures monthly.")

st.sidebar.subheader("Starting position")
opening_cash = st.sidebar.number_input(
    "Opening cash (£)", min_value=0, step=100_000, value=assumptions.OPENING_CASH)
starting_customers = st.sidebar.number_input(
    "Customers at start", min_value=0, step=10, value=assumptions.STARTING_CUSTOMERS)

st.sidebar.subheader("Revenue")
price_per_month = st.sidebar.slider(
    "Price per customer (£ / month)", 20, 500, assumptions.PRICE_PER_MONTH, step=1)
new_customers_month_1 = st.sidebar.slider(
    "New customers in month 1", 0, 100, assumptions.NEW_CUSTOMERS_MONTH_1)
new_customer_growth = st.sidebar.slider(
    "Growth in new customers (% / month)", 0.0, 15.0,
    assumptions.NEW_CUSTOMER_GROWTH * 100, step=0.5) / 100
monthly_churn = st.sidebar.slider(
    "Monthly churn (%)", 0.0, 10.0, assumptions.MONTHLY_CHURN * 100, step=0.25) / 100
gross_margin = st.sidebar.slider(
    "Gross margin (%)", 50.0, 95.0, assumptions.GROSS_MARGIN * 100, step=1.0) / 100

st.sidebar.subheader("Costs")
employer_on_costs = st.sidebar.slider(
    "Employer on-costs (% on top of salary)", 0.0, 40.0,
    assumptions.EMPLOYER_ON_COSTS * 100, step=1.0) / 100
marketing_spend_month_1 = st.sidebar.slider(
    "Marketing spend in month 1 (£)", 0, 100_000,
    assumptions.MARKETING_SPEND_MONTH_1, step=1_000)
marketing_growth = st.sidebar.slider(
    "Growth in marketing spend (% / month)", 0.0, 15.0,
    assumptions.MARKETING_GROWTH * 100, step=0.5) / 100
software_cost = st.sidebar.number_input(
    "Software & tools (£ / month)", min_value=0, step=500, value=assumptions.SOFTWARE_COST)
office_cost = st.sidebar.number_input(
    "Office (£ / month)", min_value=0, step=500, value=assumptions.OFFICE_COST)


# --- Headcount plan (editable table) --------------------------------------------

with st.expander("Edit the headcount plan (role, start month, annual salary)"):
    st.caption(
        "Change any cell, or add and delete rows at the bottom of the table. "
        "Salaries are annual and BEFORE employer on-costs."
    )
    edited_plan = st.data_editor(
        pd.DataFrame(assumptions.HEADCOUNT_PLAN),
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "role": st.column_config.TextColumn("Role"),
            "start_month": st.column_config.NumberColumn("Start month", min_value=1, max_value=36, step=1),
            "annual_salary": st.column_config.NumberColumn("Annual salary (£)", min_value=0, step=1_000, format="£%d"),
        },
    )
    # Drop any half-filled new rows, then turn the table back into a list of people.
    headcount_plan = edited_plan.dropna().to_dict("records")


# --- Run the model ------------------------------------------------------------
# Start from the defaults, swap in the sidebar values, then run everything.

inputs = model.default_inputs()
inputs["opening_cash"] = opening_cash
inputs["starting_customers"] = starting_customers
inputs["price_per_month"] = price_per_month
inputs["new_customers_month_1"] = new_customers_month_1
inputs["new_customer_growth"] = new_customer_growth
inputs["monthly_churn"] = monthly_churn
inputs["gross_margin"] = gross_margin
inputs["employer_on_costs"] = employer_on_costs
inputs["marketing_spend_month_1"] = marketing_spend_month_1
inputs["marketing_growth"] = marketing_growth
inputs["software_cost"] = software_cost
inputs["office_cost"] = office_cost
inputs["headcount_plan"] = headcount_plan

results = model.run_model(inputs)
revenue = results["revenue"]
costs = results["costs"]
cash = results["cash"]
unit = results["unit_economics"]

runway = model.runway_months(cash)
cash_out_month = model.find_cash_out_month(cash)
month_12 = model.summarise(results, 12)


# --- Headline numbers ------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(5)
if runway is None:
    col1.metric("Runway", "36+ months", help="Cash lasts the whole 36-month forecast.")
    col2.metric("Cash runs out", "Not in forecast")
else:
    col1.metric("Runway", f"{runway} months",
                help="Number of months fully paid for before cash goes below £0.")
    col2.metric("Cash runs out", revenue["Date"][cash_out_month - 1])
col3.metric("MRR at month 12", gbp(month_12["MRR (£)"]))
col4.metric("LTV:CAC at month 12", format_metric("LTV:CAC", month_12["LTV:CAC"]))
col5.metric("CAC payback at month 12", format_metric("months", month_12["CAC payback (months)"]) + " months")


# --- Tabs, one per section ----------------------------------------------------------

(tab_revenue, tab_costs, tab_cash, tab_unit,
 tab_scenarios, tab_update, tab_about) = st.tabs([
    "Revenue", "Costs", "Cash & runway", "Unit economics",
    "Scenarios", "Investor update", "About",
])

# Every chart uses the month number (1-36) on the x-axis; hovering shows the date.

with tab_revenue:
    st.subheader("MRR over time")
    st.caption("MRR = customers at the end of the month x price per month.")
    fig = px.line(revenue, x="Month", y="MRR (£)", hover_data=["Date", "Customers at end"])
    fig.update_traces(line=dict(color=SINGLE_LINE_COLOUR, width=2))
    fig.update_layout(yaxis_tickprefix="£", yaxis_rangemode="tozero")
    st.plotly_chart(fig)
    show_table(revenue)

with tab_costs:
    st.subheader("Costs by category")
    st.caption("Payroll = salaries + employer on-costs. Cost of revenue = MRR x (1 - gross margin).")
    # Reshape the cost table from "wide" (one column per category) to "long"
    # (one row per month per category), which is what a stacked bar chart needs.
    cost_categories = ["Payroll", "Marketing", "Cost of revenue", "Office", "Software"]
    costs_long = costs.rename(columns=lambda c: c.replace(" (£)", "")).melt(
        id_vars=["Month", "Date"], value_vars=cost_categories,
        var_name="Category", value_name="Cost (£)")
    fig = px.bar(costs_long, x="Month", y="Cost (£)", color="Category",
                 color_discrete_map=COST_COLOURS, hover_data=["Date"],
                 category_orders={"Category": cost_categories})
    fig.update_layout(yaxis_tickprefix="£", bargap=0.15)
    st.plotly_chart(fig)
    show_table(costs)
    st.markdown("**Headcount and payroll**")
    show_table(results["headcount"])

with tab_cash:
    st.subheader("Cash balance")
    if runway is None:
        st.success("Cash lasts the whole 36-month forecast (runway 36+ months).")
    else:
        st.error(
            f"**Runway: {runway} months.** Cash runs out in month {cash_out_month} "
            f"({revenue['Date'][cash_out_month - 1]}), so LedgerLoop needs to raise "
            f"money, cut costs or grow faster before then."
        )
    fig = px.line(cash, x="Month", y="Closing cash (£)", hover_data=["Date", "Net burn (£)"])
    fig.update_traces(line=dict(color=SINGLE_LINE_COLOUR, width=2))
    fig.add_hline(y=0, line_color="grey", line_width=1)
    if cash_out_month is not None:
        fig.add_vline(
            x=cash_out_month, line_dash="dash", line_color=CASH_OUT_COLOUR,
            annotation_text=f"Cash runs out: {revenue['Date'][cash_out_month - 1]}",
            annotation_position="top right")
    fig.update_layout(yaxis_tickprefix="£")
    st.plotly_chart(fig)
    st.caption(
        "Net burn = total costs - revenue. Closing cash = opening cash - net burn. "
        "'Runway at current burn' = cash left / this month's burn (what you'd have if nothing changed)."
    )
    show_table(cash)

with tab_unit:
    st.subheader("Unit economics")
    st.markdown(
        "- **CAC** = marketing spend / new customers  \n"
        "- **LTV** = price x gross margin / churn  \n"
        "- **LTV:CAC**: 3x or more is the usual benchmark  \n"
        "- **CAC payback** = CAC / (price x gross margin): under 12 months is good for SMB software"
    )
    st.info(
        "This CAC counts marketing spend only. A 'fully loaded' CAC would also include "
        "the salaries of the sales and marketing team, which makes it noticeably higher."
    )
    fig = px.line(unit, x="Month", y="LTV:CAC", hover_data=["Date", "CAC (£)"])
    fig.update_traces(line=dict(color=SINGLE_LINE_COLOUR, width=2))
    fig.add_hline(y=3, line_dash="dot", line_color="grey",
                  annotation_text="3x benchmark", annotation_position="bottom right")
    fig.update_layout(yaxis_rangemode="tozero")
    st.plotly_chart(fig)
    show_table(unit)

with tab_scenarios:
    st.subheader("Scenarios side by side")
    st.caption(
        f"**Slow growth:** new-customer growth x {assumptions.SLOW_GROWTH_FACTOR} "
        f"(marketing spend unchanged).  **Aggressive hiring:** "
        f"+{assumptions.AGGRESSIVE_EXTRA_HIRES} hires in month {assumptions.AGGRESSIVE_HIRE_MONTH} "
        f"at £{assumptions.AGGRESSIVE_HIRE_SALARY:,} each (revenue unchanged). "
        "Both start from your sidebar settings."
    )
    scenario_month = st.slider("Compare scenarios at month", 1, inputs["months"], 12)

    # Run each scenario through the same model.
    scenario_inputs = model.make_scenarios(inputs)
    scenario_results = {}
    for name, these_inputs in scenario_inputs.items():
        scenario_results[name] = model.run_model(these_inputs)

    scenario_table = model.compare_scenarios(inputs, scenario_month)
    # Format each row for display (the raw numbers still go into Excel).
    display_table = scenario_table.copy().astype(object)
    for metric in display_table.index:
        for scenario in display_table.columns:
            display_table.loc[metric, scenario] = format_metric(metric, scenario_table.loc[metric, scenario])
    st.dataframe(display_table)

    # One long table with a "Scenario" column, so each scenario gets its own line.
    combined = []
    for name, scenario in scenario_results.items():
        table = scenario["cash"][["Month", "Date", "Closing cash (£)"]].copy()
        table["MRR (£)"] = scenario["revenue"]["MRR (£)"]
        table["Scenario"] = name
        combined.append(table)
    combined = pd.concat(combined)

    left, right = st.columns(2)
    with left:
        fig = px.line(combined, x="Month", y="Closing cash (£)", color="Scenario",
                      color_discrete_map=SCENARIO_COLOURS, hover_data=["Date"],
                      title="Cash balance by scenario")
        fig.add_hline(y=0, line_color="grey", line_width=1)
        fig.update_layout(yaxis_tickprefix="£", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig)
    with right:
        fig = px.line(combined, x="Month", y="MRR (£)", color="Scenario",
                      color_discrete_map=SCENARIO_COLOURS, hover_data=["Date"],
                      title="MRR by scenario")
        fig.update_layout(yaxis_tickprefix="£", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig)
        st.caption("Aggressive hiring has the same revenue as Base, so its line sits on top of the Base line.")

with tab_update:
    st.subheader("Monthly investor update")
    update_month = st.selectbox(
        "Write the update for month", list(range(1, inputs["months"] + 1)), index=11,
        format_func=lambda m: f"Month {m} ({revenue['Date'][m - 1]})")
    s = model.summarise(results, update_month)

    # A few plain-English sentences that change depending on the numbers.
    if runway is None:
        runway_sentence = "On current plans our cash lasts beyond the 36-month forecast."
    else:
        # Full months still paid for after this one (same rule as the runway headline).
        months_left = cash_out_month - 1 - update_month
        if months_left < 0:
            runway_sentence = "On this plan we have already run out of cash, so we need new funding now."
        else:
            runway_sentence = (f"On current plans cash runs out in {s['Cash runs out']}, leaving "
                               f"**{months_left} months of runway**.")
            if months_left <= 9:
                runway_sentence += " We are starting fundraising conversations and would value introductions."
    if s["LTV:CAC"] is not None and s["LTV:CAC"] >= 3:
        unit_sentence = (f"LTV:CAC is {s['LTV:CAC']:.1f}x, above our 3x target, "
                         f"with a {s['CAC payback (months)']:.1f}-month CAC payback.")
    else:
        unit_sentence = ("LTV:CAC is below our 3x target, so we are "
                         "reviewing marketing efficiency.")

    st.markdown(f"""
---
**To:** LedgerLoop investors  |  **Subject:** {s['Date']} update  |  *LedgerLoop is a fictional company*

Hi all,

Here is our update for **{s['Date']}**.

**TL;DR:** MRR reached **{gbp(s['MRR (£)'])}** ({s['MRR growth vs last month']:+.1%} month on month),
an annual run rate of **{gbp(s['ARR (£)'])}**. We closed the month with **{gbp(s['Closing cash (£)'])}**
in the bank. {runway_sentence}

| Metric | {s['Date']} |
|---|---|
| MRR | {gbp(s['MRR (£)'])} |
| ARR (MRR x 12) | {gbp(s['ARR (£)'])} |
| MRR growth vs last month | {s['MRR growth vs last month']:+.1%} |
| Customers | {s['Customers']:,.0f} |
| New / churned customers | {s['New customers']:,.0f} / {s['Churned customers']:,.0f} |
| Headcount | {s['Headcount']} |
| Net burn | {gbp(s['Net burn (£)'])} |
| Cash in bank | {gbp(s['Closing cash (£)'])} |
| CAC / LTV | {gbp(s['CAC (£)'])} / {gbp(s['LTV (£)'])} |
| LTV:CAC | {format_metric('LTV:CAC', s['LTV:CAC'])} |
| CAC payback | {format_metric('months', s['CAC payback (months)'])} months |

**Customers:** we added {s['New customers']:,.0f} new small-business customers and lost
{s['Churned customers']:,.0f}, ending the month with {s['Customers']:,.0f}.

**Unit economics:** {unit_sentence}

**Cash:** net burn was {gbp(s['Net burn (£)'])} this month (costs minus revenue), leaving
{gbp(s['Closing cash (£)'])} in the bank.

**Team:** we are {s['Headcount']} people.

**How you can help:** introductions to UK accountancy firms and small-business
communities who could become customers or referral partners.

Thanks for your support,
The LedgerLoop team

---
""")

with tab_about:
    st.subheader("About this project")
    st.markdown("""
**What it is.** A seed-stage finance pack for **LedgerLoop, a fictional UK B2B fintech**
selling accounting automation software to small businesses on monthly subscriptions.
It is a student portfolio project for startup finance roles. LedgerLoop is not a
real company and the numbers are illustrative assumptions.

**Method (monthly, 36 months):**
1. **Revenue:** customers at end = customers at start - churned + new. New customers
   grow at a fixed monthly rate. MRR = customers x price.
2. **Costs:** payroll from a headcount plan (annual salary / 12, plus employer on-costs),
   plus software, office and marketing. Cost of revenue = MRR x (1 - gross margin).
3. **Cash:** net burn = costs - revenue. Closing cash = opening cash - net burn.
   Runway = months fully paid for before cash goes below zero.
4. **Unit economics:** CAC = marketing / new customers. LTV = price x gross margin / churn.
   CAC payback = CAC / (price x gross margin).
5. **Scenarios:** base, slow growth (growth halved) and aggressive hiring (+5 hires in month 6).

**Simplifications:** no pay rises, VAT, corporation tax or R&D tax credits; customers pay
monthly so cash arrives the same month as revenue; new customers follow a growth rate rather
than being driven by marketing spend; CAC counts marketing spend only.

**Code:** finance logic in `model.py`, default assumptions in `assumptions.py`,
app layout in `app.py`.

**Built with help from Claude Code**, Anthropic's AI coding assistant, which I used as a
builder and tutor: I chose and approved the assumptions, checked the calculations by
hand, and can explain every part of the model.

**Links:** [live app](https://ledgerloop-finance-pack.streamlit.app/) ·
[code on GitHub](https://github.com/TCHINTTAM/Seed-stage-startup-finance-pack)
""")


# --- Excel download (in the sidebar so it's always visible) ------------------------

st.sidebar.divider()
st.sidebar.download_button(
    "Download as Excel",
    data=make_excel(results, scenario_table, inputs),
    file_name="ledgerloop_fictional_finance_pack.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="All monthly tables, one sheet per section.",
)
