#!/usr/bin/env python3
import os, sys, re, argparse, json
from typing import Optional
from tools import load_budgets, load_projects, search_budgets, list_projects, summarize_spending
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def print_table(title: str, rows, headers):
    t = Table(title=title)
    for h in headers:
        t.add_column(h)
    for r in rows:
        t.add_row(*[str(x) for x in r])
    console.print(t)

def cmd_budgets(args):
    df = load_budgets(args.data_dir)
    res = search_budgets(df, sector=args.sector, region=args.region)
    if res.empty:
        console.print("[yellow]No matching budget rows.[/yellow]")
        return
    rows = res[['year','region','sector','program','amount_npr']].values.tolist()
    print_table("Budget Rows", rows, ["Year","Region","Sector","Program","Amount (NPR)"])
    console.print(Panel.fit(f"Source: data/budgets_2024.csv", style="dim"))

def cmd_projects(args):
    dfp = load_projects(args.data_dir)
    res = list_projects(dfp, region=args.region, top=args.top)
    if res.empty:
        console.print("[yellow]No projects found.[/yellow]")
        return
    rows = res[['project_name','region','sector','budget_npr','status']].values.tolist()
    print_table(f"Top {args.top} Projects", rows, ["Project","Region","Sector","Budget (NPR)","Status"])
    console.print(Panel.fit(f"Source: data/projects.csv", style="dim"))

def cmd_report(args):
    df = load_budgets(args.data_dir)
    out = summarize_spending(df, region=args.region)
    rows = [(args.region or 'ALL', f"{out['total_npr']:,}")] 
    print_table(f"Spending Summary — {args.region or 'All Regions'}", rows, ["Region","Total Spending (NPR)"])
    by_sec = sorted(out['by_sector'].items(), key=lambda x: x[1], reverse=True)
    print_table("By Sector", [(s, f"{amt:,}") for s, amt in by_sec], ["Sector","Amount (NPR)"])
    console.print(Panel.fit("Source: data/budgets_2024.csv", style="dim"))

def naive_parse_region(text: str, regions):
    for r in regions:
        if r.lower() in text.lower():
            return r
    return None

def naive_parse_sector(text: str):
    sectors = ["roads","health","education","water","energy"]
    for s in sectors:
        if s in text.lower():
            return s
    return None

def gpt_answer(prompt: str, evidence: str) -> Optional[str]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        system_msg = (
            "You are an AI governance assistant for Nepal. "
            "Answer briefly with numbers, then cite sources provided in <EVIDENCE>. "
            "If unsure, say what data is missing."
        )
        content = f"{prompt}\n\n<EVIDENCE>\n{evidence}\n</EVIDENCE>"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":system_msg},
                {"role":"user","content":content},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None

def cmd_ask(args):
    dfb = load_budgets(args.data_dir)
    dfp = load_projects(args.data_dir)
    regions = sorted(set(dfb['region'].dropna().tolist()))
    region = naive_parse_region(args.query, regions) or args.region
    sector = naive_parse_sector(args.query) or args.sector
    dfq = search_budgets(dfb, sector=sector, region=region)
    projects = list_projects(dfp, region=region, top=5)
    ev = {
        "region": region or "ALL",
        "sector": sector or "ALL",
        "budgets_match_rows": int(len(dfq.index)),
        "budgets_total_npr": int((dfq['amount_npr'].sum() if not dfq.empty else 0)),
        "top_projects": projects[['project_name','budget_npr','status']].head(5).to_dict(orient="records")
    }
    evidence = json.dumps(ev, indent=2)
    answer = gpt_answer(args.query, evidence)
    if not answer:
        lines = "\n".join([f"- {p['project_name']} — NPR {p['budget_npr']:,} ({p['status']})" for p in ev["top_projects"]])
        answer = (
            f"Region: {ev['region']}, Sector: {ev['sector']}\n"
            f"Matching budget rows: {ev['budgets_match_rows']}\n"
            f"Total spending (approx): NPR {ev['budgets_total_npr']:,}\n"
            f"Top projects:\n{lines}\n"
            f"Sources: data/budgets_2024.csv, data/projects.csv"
        )
    console.print(Panel.fit(answer, title="Answer"))
    console.print(Panel.fit("Tip: export OPENAI_API_KEY to enable AI-written answers.", style="dim"))

def build_parser():
    p = argparse.ArgumentParser(prog="aiminister", description="AI Minister — Terminal Assistant")
    p.add_argument("--data-dir", default="data", help="Path to data folder")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("budgets", help="Filter budget rows")
    b.add_argument("--sector", default=None, help="roads/health/education/water/energy")
    b.add_argument("--region", default=None, help="e.g., Pokhara")
    b.set_defaults(func=cmd_budgets)

    pr = sub.add_parser("projects", help="List top projects")
    pr.add_argument("--region", default=None)
    pr.add_argument("--top", type=int, default=5)
    pr.set_defaults(func=cmd_projects)

    r = sub.add_parser("report", help="Summarize spending by sector")
    r.add_argument("--region", default=None)
    r.set_defaults(func=cmd_report)

    a = sub.add_parser("ask", help="Natural-language Q&A")
    a.add_argument("query")
    a.add_argument("--region", default=None)
    a.add_argument("--sector", default=None)
    a.set_defaults(func=cmd_ask)
    return p

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
