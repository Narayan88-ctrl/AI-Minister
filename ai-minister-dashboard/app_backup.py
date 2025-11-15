# app.py — AI Minister (no logo version)
import os, io, json, glob, datetime
import pandas as pd
import streamlit as st

# =============== UI CONFIG ===============
st.set_page_config(page_title="AI Minister – Nepal", layout="wide")

# =============== I18N STRINGS ===============
STR = {
    "en": {
        "title": "🏛️ AI Minister – Nepal",
        "subtitle": "Prototype dashboard • Transparent, smart, and accountable governance",
        "filters": "Filters",
        "lang": "Language",
        "region": "Region",
        "sector": "Sector",
        "year": "Year",
        "municipality": "Municipality",
        "ask_ai": "Ask AI (optional)",
        "btn_ask": "Ask",
        "kpi_total": "Total Spending (NPR)",
        "kpi_projects": "Projects",
        "kpi_top_sector": "Top Sector",
        "budget_rows": "Budget Rows",
        "projects": "Projects",
        "spending_by_sector": "Spending by Sector",
        "sources": "Sources: data/budgets_*.csv, data/projects.csv",
        "download_pdf": "⬇️ Download Transparency Report (PDF)",
        "dl_budgets": "⬇️ Export Budgets (CSV)",
        "dl_projects": "⬇️ Export Projects (CSV)",
        "ai_disabled": "No OPENAI_API_KEY set — showing rule-based summary.",
        "ai_failed": "AI call failed: ",
        "anomaly_title": "⚠️ Possible anomalies (higher than typical by sector):",
    },
    "np": {
        "title": "🏛️ एआई मन्त्री – नेपाल",
        "subtitle": "प्रोटोटाइप ड्यासबोर्ड • पारदर्शी, स्मार्ट र जवाफदेही शासन",
        "filters": "फिल्टर",
        "lang": "भाषा",
        "region": "प्रदेश/क्षेत्र",
        "sector": "क्षेत्र",
        "year": "आर्थिक वर्ष",
        "municipality": "नगरपालिका",
        "ask_ai": "एआईलाई सोध्नुहोस् (वैकल्पिक)",
        "btn_ask": "सोध्नुहोस्",
        "kpi_total": "कुल खर्च (रु)",
        "kpi_projects": "परियोजना संख्या",
        "kpi_top_sector": "शीर्ष क्षेत्र",
        "budget_rows": "बजेट पङ्क्तिहरू",
        "projects": "परियोजनाहरू",
        "spending_by_sector": "क्षेत्रगत खर्च",
        "sources": "स्रोत: data/budgets_*.csv, data/projects.csv",
        "download_pdf": "⬇️ पारदर्शिता प्रतिवेदन (PDF)",
        "dl_budgets": "⬇️ बजेट CSV डाउनलोड",
        "dl_projects": "⬇️ परियोजना CSV डाउनलोड",
        "ai_disabled": "OPENAI_API_KEY सेट छैन — नियम-आधारित सारांश देखाइँदैछ।",
        "ai_failed": "एआई कल असफल: ",
        "anomaly_title": "⚠️ सम्भावित असामान्यता (क्षेत्रगत औसतभन्दा बढी):",
    },
}

# =============== DATA LOADER (multi-year) ===============
@st.cache_data
def load_data():
    # budgets_*.csv (e.g., budgets_2023.csv, budgets_2024.csv)
    frames = []
    for p in glob.glob("data/budgets_*.csv"):
        try:
            df = pd.read_csv(p, encoding="utf-8")
            frames.append(df)
        except Exception:
            pass
    budgets = (
        pd.concat(frames, ignore_index=True)
        if frames else pd.DataFrame(columns=["year","region","sector","program","amount_npr"])
    )
    # projects.csv
    if os.path.exists("data/projects.csv"):
        projects = pd.read_csv("data/projects.csv", encoding="utf-8")
    else:
        projects = pd.DataFrame(columns=["project_name","region","sector","budget_npr","status"])

    # normalize
    if not budgets.empty:
        budgets["sector"] = budgets["sector"].astype(str).str.lower()
        budgets["region"] = budgets["region"].astype(str).str.title()
        if "municipality" in budgets.columns:
            budgets["municipality"] = budgets["municipality"].astype(str).str.title()
        # coerce to int
        budgets["amount_npr"] = (
            budgets["amount_npr"]
            .apply(lambda x: int(str(x).replace(",", "").replace(" ", "")) if pd.notna(x) and str(x).strip() != "" else 0)
        )
        # coerce year
        budgets["year"] = pd.to_numeric(budgets["year"], errors="coerce").astype("Int64")
    if not projects.empty:
        projects["sector"] = projects["sector"].astype(str).str.lower()
        projects["region"] = projects["region"].astype(str).str.title()
        if "municipality" in projects.columns:
            projects["municipality"] = projects["municipality"].astype(str).str.title()
        projects["budget_npr"] = (
            projects["budget_npr"]
            .apply(lambda x: int(str(x).replace(",", "").replace(" ", "")) if pd.notna(x) and str(x).strip() != "" else 0)
        )
        if "status" in projects.columns:
            projects["status"] = projects["status"].astype(str).str.lower()

    return budgets, projects

budgets, projects = load_data()

# =============== HEADER (no logo) ===============
lang = st.sidebar.selectbox("Language / भाषा", ["en", "np"], index=0)
T = STR[lang]

st.title(T["title"])
st.caption(T["subtitle"])
st.markdown("---")

# =============== SIDEBAR FILTERS ===============
with st.sidebar:
    st.header(T["filters"])
    regions = ["All"] + sorted(list(set(budgets["region"].dropna().tolist() + projects["region"].dropna().tolist())))
    region = st.selectbox(T["region"], regions, index=(regions.index("Pokhara") if "Pokhara" in regions else 0))

    sectors = ["All"] + sorted(list(set(budgets["sector"].dropna().tolist() + projects["sector"].dropna().tolist())))
    sector = st.selectbox(T["sector"], sectors, index=0)

    years_list = ["All"] + (sorted(list(map(int, budgets["year"].dropna().unique()))) if not budgets.empty else [])
    year = st.selectbox(T["year"], years_list, index=0)

    muni = None
    has_muni = ("municipality" in budgets.columns) or ("municipality" in projects.columns)
    if has_muni:
        muni_opts = ["All"] + sorted(list(set(
            budgets.get("municipality", pd.Series(dtype=str)).dropna().tolist()
            + projects.get("municipality", pd.Series(dtype=str)).dropna().tolist()
        )))
        muni = st.selectbox(T["municipality"], muni_opts, index=0)

    st.markdown("---")
    question = st.text_input(T["ask_ai"], "Where did the 2024 road budget go in Pokhara?")
    ask = st.button(T["btn_ask"])

# =============== FILTER DATA ===============
bq = budgets.copy()
pq = projects.copy()

if region != "All":
    bq = bq[bq["region"] == region]
    pq = pq[pq["region"] == region]
if sector != "All":
    bq = bq[bq["sector"] == sector]
    pq = pq[pq["sector"] == sector]
if year != "All" and not bq.empty:
    bq = bq[bq["year"] == year]
if muni and muni != "All":
    if "municipality" in bq.columns:
        bq = bq[bq["municipality"] == muni]
    if "municipality" in pq.columns:
        pq = pq[pq["municipality"] == muni]

# =============== KPIs ===============
total_spend = int(bq["amount_npr"].sum()) if not bq.empty else 0
num_projects = int(pq.shape[0])
by_sector = (bq.groupby("sector")["amount_npr"].sum().sort_values(ascending=False)
             if not bq.empty else pd.Series(dtype=int))
top_sec = (by_sector.index[:1].tolist() or ["—"])[0].title()

c1, c2, c3 = st.columns(3)
c1.metric(T["kpi_total"], f"{total_spend:,}")
c2.metric(T["kpi_projects"], f"{num_projects}")
c3.metric(T["kpi_top_sector"], top_sec)

# =============== TABLES ===============
st.subheader(T["budget_rows"])
budget_cols = ["year","region","sector","program","amount_npr"]
if "municipality" in bq.columns: budget_cols.insert(1, "municipality")
st.dataframe(
    bq[budget_cols].rename(columns={
        "year":"Year","region":"Region","sector":"Sector","program":"Program",
        "amount_npr":"Amount (NPR)","municipality":"Municipality"
    }),
    use_container_width=True
)

st.subheader(T["projects"])
project_cols = ["project_name","region","sector","budget_npr","status"]
if "municipality" in pq.columns: project_cols.insert(1, "municipality")
st.dataframe(
    pq[project_cols].rename(columns={
        "project_name":"Project","region":"Region","sector":"Sector",
        "budget_npr":"Budget (NPR)","status":"Status","municipality":"Municipality"
    }),
    use_container_width=True
)

# =============== CHART ===============
try:
    import altair as alt
    if not bq.empty:
        st.subheader(T["spending_by_sector"])
        chart_df = by_sector.reset_index()
        chart_df.columns = ["sector","amount_npr"]
        chart_df["sector"] = chart_df["sector"].str.title()
        st.altair_chart(
            alt.Chart(chart_df).mark_bar().encode(
                x=alt.X("sector:N", title="Sector"),
                y=alt.Y("amount_npr:Q", title="Amount (NPR)"),
                tooltip=["sector","amount_npr"]
            ),
            use_container_width=True
        )
except Exception:
    st.info("Install 'altair' for charts: pip install altair")

# =============== ANOMALY FLAGS ===============
import numpy as np
def flag_anomalies(series, zthr=1.6):
    if series.empty: return []
    vals = series.values.astype(float)
    mu, sd = vals.mean(), vals.std() or 1.0
    z = (vals - mu) / sd
    out = []
    for (sec, amt), zi in zip(series.items(), z):
        if zi > zthr:
            out.append((sec.title(), int(amt), float(zi)))
    return sorted(out, key=lambda x: x[2], reverse=True)

anoms = flag_anomalies(by_sector)
if anoms:
    st.warning(T["anomaly_title"])
    for sec, amt, z in anoms:
        st.write(f"- **{sec}** — NPR {amt:,} (z={z:.2f})")

st.markdown("---")
st.caption(T["sources"])

# =============== PDF BUILDER (no logo) ===============
def build_transparency_pdf(region, sector, year, muni, total_spend, by_sector, bq, pq, T):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Transparency Report")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='H1', fontSize=16, leading=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='H2', fontSize=13, leading=16, spaceAfter=6))
    styles.add(ParagraphStyle(name='Small', fontSize=9, leading=12))

    story = []
    story.append(Paragraph(T["title"], styles["H1"]))
    story.append(Paragraph(T["subtitle"], styles["Small"]))
    meta = f'{T["region"]}: {region} | {T["sector"]}: {sector} | {T["year"]}: {year} | {T.get("municipality","Municipality")}: {muni or "—"} | {datetime.date.today().isoformat()}'
    story.append(Paragraph(meta, styles["Small"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f'{T["kpi_total"]}: {total_spend:,}', styles["H2"]))

    # By-sector table
    sec_items = (by_sector.items() if hasattr(by_sector, "items") else by_sector.to_dict().items())
    sec_rows = [["Sector","Amount (NPR)"]] + [[str(s).title(), f"{int(a):,}"] for s,a in sec_items]
    t = Table(sec_rows, colWidths=[260, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(Paragraph(T["spending_by_sector"], styles["H2"]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Projects table (top 12)
    story.append(Paragraph(T["projects"], styles["H2"]))
    ptop = pq.sort_values("budget_npr", ascending=False).head(12)
    proj_rows = [["Project","Budget (NPR)","Status"]] + [
        [r["project_name"], f"{int(r['budget_npr']):,}", r.get("status","")] for _, r in ptop.iterrows()
    ]
    from reportlab.platypus import Table as TBL
    tp = TBL(proj_rows, colWidths=[260, 120, 80])
    tp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(tp)

    story.append(Spacer(1, 6))
    story.append(Paragraph(T["sources"], styles["Small"]))
    doc.build(story)
    pdf_bytes = buf.getvalue(); buf.close()
    return pdf_bytes

pdf_bytes = build_transparency_pdf(
    region=region, sector=sector, year=year, muni=muni,
    total_spend=total_spend, by_sector=(by_sector.to_dict() if not by_sector.empty else {}),
    bq=bq, pq=pq, T=T
)
st.download_button(
    label=T["download_pdf"],
    data=pdf_bytes,
    file_name=f"Transparency_{region}_{sector}_{year}.pdf",
    mime="application/pdf",
)

# CSV exports
st.download_button(
    label=T["dl_budgets"],
    data=bq.to_csv(index=False).encode("utf-8"),
    file_name=f"budgets_{region}_{sector}_{year}.csv",
    mime="text/csv"
)
st.download_button(
    label=T["dl_projects"],
    data=pq.to_csv(index=False).encode("utf-8"),
    file_name=f"projects_{region}_{sector}_{year}.csv",
    mime="text/csv"
)

# =============== ASK AI (optional) ===============
def try_gpt_answer(prompt: str, evidence: dict):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None, T["ai_disabled"]
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        system = ("You are an AI governance assistant for Nepal. "
                  "Use the provided <EVIDENCE> JSON to answer concisely. "
                  "Cite numbers and list top projects. If data is missing, say so.")
        content = f"{prompt}\n\n<EVIDENCE>\n{json.dumps(evidence, indent=2)}\n</EVIDENCE>"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":content}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip(), None
    except Exception as e:
        return None, T["ai_failed"] + str(e)

if ask and question.strip():
    ev = {
        "region": region, "sector": sector, "year": year, "municipality": muni,
        "budgets_total_npr": total_spend,
        "budgets_rows": int(bq.shape[0]),
        "top_projects": pq.sort_values("budget_npr", ascending=False).head(5)[
            ["project_name","budget_npr","status"]].to_dict(orient="records")
    }
    ai_text, warn = try_gpt_answer(question, ev)
    if ai_text:
        st.success(ai_text)
    else:
        st.warning(warn)
        lines = "\n".join([f"- {p['project_name']} — NPR {p['budget_npr']:,} ({p.get('status','')})" for p in ev["top_projects"]])
        st.code(f"Region: {region}\nSector: {sector}\nYear: {year}\nRows: {ev['budgets_rows']}\nTotal: NPR {ev['budgets_total_npr']:,}\nTop projects:\n{lines}", language="text")

