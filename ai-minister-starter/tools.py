import os
import pandas as pd

def load_budgets(data_dir="data"):
    path = os.path.join(data_dir, "budgets_2024.csv")
    df = pd.read_csv(path)
    df['sector'] = df['sector'].str.lower()
    df['region'] = df['region'].str.title()
    return df

def load_projects(data_dir="data"):
    path = os.path.join(data_dir, "projects.csv")
    df = pd.read_csv(path)
    df['sector'] = df['sector'].str.lower()
    df['region'] = df['region'].str.title()
    return df

def search_budgets(df, sector=None, region=None):
    q = df
    if sector:
        q = q[q['sector'] == sector.lower()]
    if region:
        q = q[q['region'].str.lower() == region.lower()]
    return q

def list_projects(dfp, region=None, top=5):
    q = dfp.copy()
    if region:
        q = q[q['region'].str.lower() == region.lower()]
    q = q.sort_values(by='budget_npr', ascending=False).head(top)
    return q

def summarize_spending(df, region=None):
    q = df
    if region:
        q = q[q['region'].str.lower() == region.lower()]
    total = int(q['amount_npr'].sum())
    by_sector = {k:int(v) for k,v in q.groupby('sector')['amount_npr'].sum().to_dict().items()}
    return {"total_npr": total, "by_sector": by_sector}
