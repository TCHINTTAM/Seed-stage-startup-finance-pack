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




# --- 4. Unit economics -------------------------------------------------------

def build_unit_economics(revenue, costs, price_per_month, gross_margin,
                         monthly_churn):
    """
    How much it costs to win a customer, and how much they're worth.

      CAC (customer acquisition cost) = marketing spend / new customers
      Gross profit per customer per month = price x gross margin
      LTV (lifetime value) = gross profit per customer per month / churn
          (on average a customer stays 1 / churn months: 1 / 0.03 = 33 months)
      LTV:CAC = LTV / CAC        (how many £ of value per £1 spent winning them)
      CAC payback (months) = CAC / gross profit per customer per month
          (how long until a new customer has "paid back" what it cost to win)
    """
    gross_profit_per_customer = price_per_month * gross_margin

    # If churn is 0, customers never leave and LTV would be infinite,
    # so we mark it as None (not applicable) instead of dividing by zero.
    if monthly_churn > 0:
        ltv = gross_profit_per_customer / monthly_churn
    else:
        ltv = None

    rows = []
    for i in range(len(revenue)):
        marketing = costs["Marketing (£)"][i]
        new_customers = revenue["New customers"][i]

        cac = marketing / new_customers if new_customers > 0 else None
        if cac is not None and ltv is not None and cac > 0:
            ltv_to_cac = ltv / cac
        else:
            ltv_to_cac = None
        if cac is not None and gross_profit_per_customer > 0:
            payback = cac / gross_profit_per_customer
        else:
            payback = None

        rows.append({
            "Month": revenue["Month"][i],
            "Date": revenue["Date"][i],
            "Marketing (£)": marketing,
            "New customers": new_customers,
            "CAC (£)": cac,
            "Gross profit per customer per month (£)": gross_profit_per_customer,
            "LTV (£)": ltv,
            "LTV:CAC": ltv_to_cac,
            "CAC payback (months)": payback,
        })
    return pd.DataFrame(rows)


# --- 5. Running the whole model ---------------------------------------------

def default_inputs():
    """
    Collect every default assumption from assumptions.py into one dictionary.
    The app replaces some of these with the sidebar values.
    """
    return {
        "months": assumptions.MONTHS,
        "start_year": assumptions.START_YEAR,
        "start_month": assumptions.START_MONTH,
        "opening_cash": assumptions.OPENING_CASH,
        "starting_customers": assumptions.STARTING_CUSTOMERS,
        "price_per_month": assumptions.PRICE_PER_MONTH,
        "new_customers_month_1": assumptions.NEW_CUSTOMERS_MONTH_1,
        "new_customer_growth": assumptions.NEW_CUSTOMER_GROWTH,
        "monthly_churn": assumptions.MONTHLY_CHURN,
        "gross_margin": assumptions.GROSS_MARGIN,
        "employer_on_costs": assumptions.EMPLOYER_ON_COSTS,
        "headcount_plan": assumptions.HEADCOUNT_PLAN,
        "software_cost": assumptions.SOFTWARE_COST,
        "office_cost": assumptions.OFFICE_COST,
        "marketing_spend_month_1": assumptions.MARKETING_SPEND_MONTH_1,
        "marketing_growth": assumptions.MARKETING_GROWTH,
    }


def run_model(inputs):
    """
    Run every part of the model in order and return all the tables.
    Each step uses the results of the one before:
      revenue -> headcount -> costs -> cash -> unit economics
    """
    revenue = build_revenue(
        months=inputs["months"],
        starting_customers=inputs["starting_customers"],
        new_customers_month_1=inputs["new_customers_month_1"],
        new_customer_growth=inputs["new_customer_growth"],
        monthly_churn=inputs["monthly_churn"],
        price_per_month=inputs["price_per_month"],
        start_year=inputs["start_year"],
        start_month=inputs["start_month"],
    )
    headcount = build_headcount(
        headcount_plan=inputs["headcount_plan"],
        months=inputs["months"],
        employer_on_costs=inputs["employer_on_costs"],
    )
    costs = build_costs(
        revenue=revenue,
        headcount=headcount,
        gross_margin=inputs["gross_margin"],
        software_cost=inputs["software_cost"],
        office_cost=inputs["office_cost"],
        marketing_spend_month_1=inputs["marketing_spend_month_1"],
        marketing_growth=inputs["marketing_growth"],
    )
    cash = build_cash(revenue, costs, inputs["opening_cash"])
    unit_economics = build_unit_economics(
        revenue=revenue,
        costs=costs,
        price_per_month=inputs["price_per_month"],
        gross_margin=inputs["gross_margin"],
        monthly_churn=inputs["monthly_churn"],
    )
    return {
        "revenue": revenue,
        "headcount": headcount,
        "costs": costs,
        "cash": cash,
        "unit_economics": unit_economics,
    }


# --- 6. Scenarios ------------------------------------------------------------

def make_scenarios(base_inputs):
    """
    Build the three scenarios from one set of base inputs:
      - Base: the inputs as they are
      - Slow growth: new-customer growth halved (marketing spend unchanged)
      - Aggressive hiring: 5 extra hires in month 6 (revenue unchanged)

    dict(...) and list(...) make COPIES, so changing a scenario never
    accidentally changes the base inputs.
    """
    slow = dict(base_inputs)
    slow["new_customer_growth"] = (base_inputs["new_customer_growth"]
                                   * assumptions.SLOW_GROWTH_FACTOR)

    aggressive = dict(base_inputs)
    extra_hires = []
    for n in range(assumptions.AGGRESSIVE_EXTRA_HIRES):
        extra_hires.append({
            "role": "Extra hire (aggressive scenario)",
            "start_month": assumptions.AGGRESSIVE_HIRE_MONTH,
            "annual_salary": assumptions.AGGRESSIVE_HIRE_SALARY,
        })
    aggressive["headcount_plan"] = list(base_inputs["headcount_plan"]) + extra_hires

    return {
        "Base": base_inputs,
        "Slow growth": slow,
        "Aggressive hiring": aggressive,
    }


def summarise(results, month):
    """
    Key numbers from one model run, for one chosen month.
    Used for the side-by-side scenario table and the investor update.
    """
    i = month - 1  # tables start at row 0, months start at 1
    revenue = results["revenue"]
    cash = results["cash"]
    unit = results["unit_economics"]

    runway = runway_months(cash)
    cash_out = find_cash_out_month(cash)

    # Month-on-month MRR growth: (this month / last month) - 1.
    # Month 1 has no previous month in the table, so we compare it with the
    # starting customers instead (the price is the same, so this works).
    if i > 0:
        previous_mrr = revenue["MRR (£)"][i - 1]
    else:
        price = revenue["MRR (£)"][0] / revenue["Customers at end"][0]
        previous_mrr = revenue["Customers at start"][0] * price
    mrr_growth = revenue["MRR (£)"][i] / previous_mrr - 1

    return {
        "Date": revenue["Date"][i],
        "Customers": revenue["Customers at end"][i],
        "New customers": revenue["New customers"][i],
        "Churned customers": revenue["Churned customers"][i],
        "MRR (£)": revenue["MRR (£)"][i],
        "MRR growth vs last month": mrr_growth,
        "ARR (£)": revenue["MRR (£)"][i] * 12,  # annual run rate
        "Headcount": results["headcount"]["Headcount"][i],
        "Net burn (£)": cash["Net burn (£)"][i],
        "Closing cash (£)": cash["Closing cash (£)"][i],
        "CAC (£)": unit["CAC (£)"][i],
        "LTV (£)": unit["LTV (£)"][i],
        "LTV:CAC": unit["LTV:CAC"][i],
        "CAC payback (months)": unit["CAC payback (months)"][i],
        "Runway (months)": runway if runway is not None else "36+",
        "Cash runs out": revenue["Date"][cash_out - 1] if cash_out else "Not within 36 months",
    }


def compare_scenarios(base_inputs, month):
    """
    Run all three scenarios and put their key numbers side by side:
    one column per scenario, one row per metric.
    """
    columns = {}
    for name, inputs in make_scenarios(base_inputs).items():
        columns[name] = summarise(run_model(inputs), month)
    return pd.DataFrame(columns)


# --- Run this file directly to check the numbers ---------------------------
# This block only runs when you type `python model.py` in the terminal.
# It does NOT run when app.py imports this file.
if __name__ == "__main__":
    pd.set_option("display.width", 200)
    results = run_model(default_inputs())

    print("LedgerLoop (fictional) - revenue, first 6 months")
    print(results["revenue"].head(6).round(1).to_string(index=False))
    print()
    print("Unit economics, months 1, 12, 24, 36")
    print(results["unit_economics"].iloc[[0, 11, 23, 35]].round(1).to_string(index=False))
    print()
    print("Runway:", runway_months(results["cash"]), "months")
    print()
    print("Scenarios compared at month 12")
    print(compare_scenarios(default_inputs(), 12).to_string())
