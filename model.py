# model.py
# ---------------------------------------------------------------------------
# The finance calculations for LedgerLoop (a FICTIONAL company).
# No app layout here - just plain functions you can read on their own.
#
# Each function takes assumptions in and gives a table (a pandas DataFrame)
# back, with one row per month.
#
# Units: GBP (£), monthly figures, percentages as decimals (5% = 0.05).
# ---------------------------------------------------------------------------

import pandas as pd

import assumptions


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_label(month_number, start_year, start_month):
    """Turn a model month (1, 2, 3...) into a date label like 'Jan 2027'."""
    # Count how many months after January of the start year we are.
    months_since_january = (start_month - 1) + (month_number - 1)
    year = start_year + months_since_january // 12   # // = whole-number division
    month_index = months_since_january % 12           # % = remainder (0 = Jan)
    return MONTH_NAMES[month_index] + " " + str(year)


# --- 1. Revenue --------------------------------------------------------------

def build_revenue(months, starting_customers, new_customers_month_1,
                  new_customer_growth, monthly_churn, price_per_month,
                  start_year, start_month):
    """
    Work out customers and MRR (monthly recurring revenue) for every month.

    Each month:
      1. We start with last month's ending customers.
      2. Some of them cancel:   churned = customers at start x churn rate
      3. Some new ones join:    new = month-1 new customers, grown each month
      4. Customers at end = start - churned + new
      5. MRR = customers at end x price per month

    New customers are not churned in the month they join (they've only just
    signed up). Customer numbers can be fractions (e.g. 26.3): the model shows
    the average we EXPECT, not whole people, so we keep the decimals for
    accuracy and only round them when displaying.
    """
    rows = []  # we'll add one dictionary per month, then turn it into a table
    customers_at_start = starting_customers

    for month in range(1, months + 1):  # 1, 2, 3 ... 36
        # New customers grow by the growth rate every month.
        # Month 1: 25. Month 2: 25 x 1.05. Month 3: 25 x 1.05 x 1.05 ...
        new_customers = new_customers_month_1 * (1 + new_customer_growth) ** (month - 1)

        churned_customers = customers_at_start * monthly_churn
        customers_at_end = customers_at_start - churned_customers + new_customers
        mrr = customers_at_end * price_per_month

        rows.append({
            "Month": month,
            "Date": month_label(month, start_year, start_month),
            "Customers at start": customers_at_start,
            "New customers": new_customers,
            "Churned customers": churned_customers,
            "Customers at end": customers_at_end,
            "MRR (£)": mrr,
        })

        # Next month starts with this month's ending customers.
        customers_at_start = customers_at_end

    return pd.DataFrame(rows)


# --- 2. Costs ----------------------------------------------------------------

def build_headcount(headcount_plan, months, employer_on_costs):
    """
    Turn the headcount plan (a list of people with start months and annual
    salaries) into a monthly table of headcount and payroll cost.

    For each month, everyone whose start month has arrived is paid:
      monthly salary = annual salary / 12
      on-costs       = monthly salary x on-cost rate (NI, pension, benefits)
    """
    rows = []
    for month in range(1, months + 1):
        headcount = 0
        salaries = 0
        for person in headcount_plan:
            if month >= person["start_month"]:  # have they started yet?
                headcount = headcount + 1
                salaries = salaries + person["annual_salary"] / 12

        on_costs = salaries * employer_on_costs
        rows.append({
            "Month": month,
            "Headcount": headcount,
            "Salaries (£)": salaries,
            "On-costs (£)": on_costs,
            "Total payroll (£)": salaries + on_costs,
        })
    return pd.DataFrame(rows)


def build_costs(revenue, headcount, gross_margin, software_cost, office_cost,
                marketing_spend_month_1, marketing_growth):
    """
    Add up every cost for every month, split into categories.

    - Cost of revenue: the direct cost of serving customers. If gross margin
      is 80%, the other 20% of revenue goes on hosting, data fees etc.
      So cost of revenue = MRR x (1 - gross margin).
    - Payroll: from the headcount table (salaries + on-costs).
    - Software and office: fixed amounts each month.
    - Marketing: starts at the month-1 amount and grows each month.
    """
    rows = []
    for i in range(len(revenue)):           # i = 0, 1, 2 ... (row positions)
        month = revenue["Month"][i]
        mrr = revenue["MRR (£)"][i]

        cost_of_revenue = mrr * (1 - gross_margin)
        payroll = headcount["Total payroll (£)"][i]
        marketing = marketing_spend_month_1 * (1 + marketing_growth) ** (month - 1)
        total = cost_of_revenue + payroll + software_cost + office_cost + marketing

        rows.append({
            "Month": month,
            "Date": revenue["Date"][i],
            "Cost of revenue (£)": cost_of_revenue,
            "Payroll (£)": payroll,
            "Software (£)": software_cost,
            "Office (£)": office_cost,
            "Marketing (£)": marketing,
            "Total costs (£)": total,
        })
    return pd.DataFrame(rows)


# --- 3. Cash and runway ------------------------------------------------------

def build_cash(revenue, costs, opening_cash):
    """
    Track the bank balance month by month.

      Net burn      = total costs - revenue   (cash lost this month;
                                               negative = making money)
      Closing cash  = opening cash - net burn
      Next month's opening cash = this month's closing cash

    Also shows "runway at current burn": how many more months the cash
    would last if every future month burned the same as this one.
    """
    rows = []
    cash = opening_cash
    for i in range(len(revenue)):
        opening = cash
        mrr = revenue["MRR (£)"][i]
        total_costs = costs["Total costs (£)"][i]
        net_burn = total_costs - mrr
        closing = opening - net_burn

        # Only meaningful while we are burning cash and still have some.
        if net_burn > 0 and closing > 0:
            runway_at_current_burn = closing / net_burn
        else:
            runway_at_current_burn = None   # None = "not applicable"

        rows.append({
            "Month": revenue["Month"][i],
            "Date": revenue["Date"][i],
            "Opening cash (£)": opening,
            "Revenue (£)": mrr,
            "Total costs (£)": total_costs,
            "Net burn (£)": net_burn,
            "Closing cash (£)": closing,
            "Runway at current burn (months)": runway_at_current_burn,
        })
        cash = closing
    return pd.DataFrame(rows)


def find_cash_out_month(cash):
    """
    Return the first month where closing cash drops below zero,
    or None if the cash lasts the whole forecast.
    """
    for i in range(len(cash)):
        if cash["Closing cash (£)"][i] < 0:
            return cash["Month"][i]
    return None


def runway_months(cash):
    """
    Runway in months, from the start of the forecast.

    If cash runs out during month 21, the company can fully pay for
    months 1-20, so the runway is 20 months. If cash never runs out
    in the forecast, return None (the app shows this as "36+ months").
    """
    cash_out_month = find_cash_out_month(cash)
    if cash_out_month is None:
        return None
    return cash_out_month - 1


# --- Run this file directly to check the numbers ---------------------------
# This block only runs when you type `python model.py` in the terminal.
# It does NOT run when app.py imports this file.
if __name__ == "__main__":
    revenue = build_revenue(
        months=assumptions.MONTHS,
        starting_customers=assumptions.STARTING_CUSTOMERS,
        new_customers_month_1=assumptions.NEW_CUSTOMERS_MONTH_1,
        new_customer_growth=assumptions.NEW_CUSTOMER_GROWTH,
        monthly_churn=assumptions.MONTHLY_CHURN,
        price_per_month=assumptions.PRICE_PER_MONTH,
        start_year=assumptions.START_YEAR,
        start_month=assumptions.START_MONTH,
    )
    print("LedgerLoop (fictional) - revenue, first 6 months")
    print(revenue.head(6).round(1).to_string(index=False))

    headcount = build_headcount(
        headcount_plan=assumptions.HEADCOUNT_PLAN,
        months=assumptions.MONTHS,
        employer_on_costs=assumptions.EMPLOYER_ON_COSTS,
    )
    costs = build_costs(
        revenue=revenue,
        headcount=headcount,
        gross_margin=assumptions.GROSS_MARGIN,
        software_cost=assumptions.SOFTWARE_COST,
        office_cost=assumptions.OFFICE_COST,
        marketing_spend_month_1=assumptions.MARKETING_SPEND_MONTH_1,
        marketing_growth=assumptions.MARKETING_GROWTH,
    )
    cash = build_cash(revenue, costs, assumptions.OPENING_CASH)

    print()
    print("Costs, first 6 months")
    print(costs.head(6).round(0).to_string(index=False))
    print()
    print("Cash, months 1-3 and 18-22")
    print(cash.iloc[[0, 1, 2, 17, 18, 19, 20, 21]].round(1).to_string(index=False))
    print()
    out = find_cash_out_month(cash)
    print("Cash runs out in month", out, "(" + cash["Date"][out - 1] + ")")
    print("Runway:", runway_months(cash), "months")
