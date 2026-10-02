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
