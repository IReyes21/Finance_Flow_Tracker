import json
from datetime import date
from pathlib import Path

DATA_PATH = Path(__file__).parent / "transactions.json"


def load_transactions():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def data_fetcher(chart_type, year, month):
    if chart_type == 'daily_totals':
        return get_daily_totals_for_month(year, month)
    elif chart_type == 'categories':
        return get_category_breakdown_for_month(year, month)
    elif chart_type == 'income_expenses':
        return get_income_expenses_for_month(year, month)
    else:
        return {}


def get_transactions_for_day(year: int, month: int, day: int):
    # returns list of dicts for that date
    d = date(year, month, day)
    key = d.isoformat()
    data = load_transactions()
    return data.get(key, [])


def get_daily_totals_for_month(year: int, month: int):
    # returns lists of dates and totals for days in the month (0 if none)
    import calendar
    data = load_transactions()
    cal = calendar.monthrange(year, month)[1]
    dates = []
    totals = []
    for d in range(1, cal+1):
        key = date(year, month, d).isoformat()
        txs = data.get(key, [])
        total = sum(t.get('amount', 0) for t in txs)
        dates.append(f"{month}/{d}")
        totals.append(total)
    return {"dates": dates, "values": totals}


def get_category_breakdown_for_month(year: int, month: int):
    data = load_transactions()
    from datetime import date
    import calendar
    counts = {}
    for d in range(1, calendar.monthrange(year, month)[1]+1):
        key = date(year, month, d).isoformat()
        for t in data.get(key, []):
            cat = t.get('category', 'Other')
            counts[cat] = counts.get(cat, 0) + (-t.get('amount', 0) if t.get('amount', 0) < 0 else 0)
    labels = list(counts.keys())
    values = [abs(v) for v in counts.values()]
    return {"labels": labels, "values": values}


def get_income_expenses_for_month(year: int, month: int):
    data = load_transactions()
    from datetime import date
    import calendar
    num_days = calendar.monthrange(year, month)[1]

    income = 0.0
    expenses = 0.0

    for day in range(1, num_days + 1):
        key = date(year, month, day).isoformat()
        for t in data.get(key, []):
            amt = t.get("amount", 0)
            if amt > 0:
                income += amt
            elif amt < 0:
                expenses += abs(amt)

    return {"income": income, "expenses": expenses}
