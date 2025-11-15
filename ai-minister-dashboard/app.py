# app.py — AI Minister – Nepal (final)
import io, os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# PDF deps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader

# ───────────────────────── Page config ─────────────────────────
st.set_page_config(
    page_title="AI Minister – Nepal",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Styles ─────────────────────────
st.markdown("""
<style>
:root { --bg:#0b0f19; --card:#111827; --muted:#9ca3af; --text:#e5e7eb; --primary:#ef4444; --primary600:#dc2626; }
html, body, [class*="css"] { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, sans-serif; }
section[data-testid="stSidebar"] { background:#0e1423; border-right:1px solid rgba(255,255,255,.06); }
.block-container { padding-top: .8rem; }
.header { padding: 14px 18px; border-radius: 14px;
  background: radial-gradient(1200px 200px at 20% -30%, rgba(239,68,68,.12), transparent 60%), #0f172a;
  border:1px solid rgba(255,255,255,.06); box-shadow:0 10px 30px rgba(0,0,0,.35); margin: 8px 0 16px; }
.header h1 { margin:0; font-size:2rem; color:#fff; display:inline-flex; gap:.6rem; }
.flag { font-size:2rem; line-height:1; filter:drop-shadow(0 0 8px rgba(239,68,68,.55)); transform:translateY(2px); }
.card{ background:#111827; border-radius:14px; padding:16px; border:1px solid rgba(255,255,255,.06); box-shadow:0 8px 28px rgba(0,0,0,.25); }
.kpi-label{color:#9ca3af; font-size:.9rem; margin-bottom:6px}
.kpi-value{color:#e5e7eb; font-size:1.6rem; font-weight:800}
.kpi-delta-pos{color:#34d399; font-weight:600}
.kpi-delta-neg{color:#f87171; font-weight:600}
.small-muted{ color:#9ca3af; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────── Language strings ─────────────────────────
TEXT = {
    "en": {
        "title": "AI Minister – Nepal",
        "subtitle": "Transparent budgets & projects dashboard • anomaly flags • instant PDF exports",
        "filters": "Filter", "region": "Region", "sector": "Sector", "year": "Fiscal Year",
        "k_total_budget": "Total Budget", "k_total_spent": "Total Spent",
        "k_exec_rate": "Execution Rate", "k_anomalies": "Anomaly Flags", "delta_vs": "vs.",
        "tab_overview": "Overview", "tab_projects": "Projects", "tab_anomalies": "Anomalies",
        "chart_title": "Budget vs Spent by sector",
        "downloads": "Downloads", "dl_csv": "⬇️ CSV (filtered)", "dl_json": "⬇️ JSON (filtered)",
        "btn_pdf": "🖨️ Generate PDF Transparency Report",
        "no_data": "No data for the current filter.", "list_projects": "Project list",
        "anomaly_flags": "Anomaly flags", "no_anoms": "No anomalies detected for the current filter.",
        "tip": "Tip: Use the red button on the landing page to open this dashboard directly.",
        "contact": "Contact", "footer": "© 2025 Narayan Ranabhat • AI Minister – Nepal",
        "ask_ai": "🤖 Ask AI (beta)", "ask_ai_ph": "e.g. Which region spent the most in 2025?",
        "ask_ai_error": "AI unavailable. Set OPENAI_API_KEY in Streamlit Secrets.",
        "pdf_title_en": "AI Minister – Nepal",
        "pdf_title_ne": "एआइ मन्त्री – नेपाल",
        "pdf_tr_title": "Transparency Report",
        "pdf_headers": ["Project","Region","Sector","Year","Budget","Spent","Anom"],
    },
    "ne": {
        "title": "एआइ मन्त्री – नेपाल",
        "subtitle": "पारदर्शी बजेट र परियोजना ड्यासबोर्ड • अनियमितता संकेत • तुरुन्त PDF प्रतिवेदन",
        "filters": "फिल्टर", "region": "प्रदेश/क्षेत्र", "sector": "क्षेत्र/सेक्टर", "year": "आर्थिक वर्ष",
        "k_total_budget": "जम्मा बजेट", "k_total_spent": "खर्च भएको",
        "k_exec_rate": "कार्यान्वयन दर", "k_anomalies": "अनियमितता सङ्केत", "delta_vs": "को तुलनामा",
        "tab_overview": "समग्र अवलोकन", "tab_projects": "परियोजनाहरू", "tab_anomalies": "अनियमितता",
        "chart_title": "सेक्टरअनुसार बजेट बनाम खर्च",
        "downloads": "डाउनलोड", "dl_csv": "⬇️ CSV (छानिएको)", "dl_json": "⬇️ JSON (छानिएको)",
        "btn_pdf": "🖨️ पारदर्शिता प्रतिवेदन (PDF) बनाउनुहोस्",
        "no_data": "यो छनोटमा डाटा छैन।", "list_projects": "परियोजना सूची",
        "anomaly_flags": "अनियमितता सङ्केत", "no_anoms": "यो छनोटमा अनियमितता फेला परेन।",
        "tip": "सुझाव: Landing page को रातो बटनबाट यो ड्यासबोर्ड सिधै खोल्न सकिन्छ।",
        "contact": "सम्पर्क", "footer": "© २०२५ नरायण रानाभाट • एआइ मन्त्री – नेपाल",
        "ask_ai": "🤖 एआइलाई सोध्नुहोस् (beta)", "ask_ai_ph": "उदाहरण: २०२५ मा सबैभन्दा बढी खर्च कहाँ भयो?",
        "ask_ai_error": "एआइ उपलब्ध छैन। Streamlit Secrets मा OPENAI_API_KEY राख्नुहोस्।",
        "pdf_title_en": "AI Minister – Nepal",
        "pdf_title_ne": "एआइ मन्त्री – नेपाल",
        "pdf_tr_title": "पारदर्शिता प्रतिवेदन",
        "pdf_headers": ["परियोजना","प्रदेश/क्षेत्र","सेक्टर","वर्ष","बजेट","खर्च","अनियम"],
    }
}

# ───────────────────────── Language selector ─────────────────────────
_, _, colR = st.columns([1,1,1])
with colR:
    lang = st.selectbox("Language / भाषा", options=[("en","English"),("ne","नेपाली")],
                        index=0, format_func=lambda x: x[1])[0]
T = TEXT[lang]

# ───────────────────────── Header ─────────────────────────
st.markdown(f"""
<div class="header">
  <h1>🏛️ {T['title']} <span class="flag">🇳🇵</span></h1>
  <div class="small-muted">{T['subtitle']}</div>
</div>
""", unsafe_allow_html=True)

# ───────────────────────── Sidebar filters ─────────────────────────
st.sidebar.subheader(T["filters"])
regions_en = ["All Nepal","Province 1","Madhesh","Bagmati","Gandaki","Lumbini","Karnali","Sudurpashchim"]
regions_ne = ["सारा नेपाल","प्रदेश १","मधेस","बागमती","गण्डकी","लुम्बिनी","कर्णाली","सुदूरपश्चिम"]
sectors_en = ["All","Health","Education","Infrastructure","Agriculture","Energy","Tourism"]
sectors_ne = ["सबै","स्वास्थ्य","शिक्षा","पूर्वाधार","कृषि","ऊर्जा","पर्यटन"]

regions = regions_en if lang=="en" else regions_ne
sectors = sectors_en if lang=="en" else sectors_ne
years = list(range(2018, 2026))

region = st.sidebar.selectbox(T["region"], regions, index=0)
sector = st.sidebar.selectbox(T["sector"], sectors, index=0)
year   = st.sidebar.select_slider(T["year"], options=years, value=max(years))
st.sidebar.markdown("---")
st.sidebar.caption(T["tip"])
st.sidebar.markdown(f"**{T['contact']}:** narayanranabhat777@gmail.com")

# ───────────────────────── Demo data ─────────────────────────
@st.cache_data
def load_demo(regions_list, sectors_list, years_list):
    rng = np.random.default_rng(0)
    rows = []
    for r in regions_list:
        if r in ("All Nepal","सारा नेपाल"):  # skip label
            continue
        for s in sectors_list:
            if s in ("All","सबै"):  # skip label
                continue
            for y in years_list:
                budget = int(rng.integers(5_000_000, 200_000_000))
                spent  = int(budget * rng.uniform(0.6, 1.05))
                anomaly = int(rng.binomial(1, 0.12))
                rows.append((r, s, y, f"{s} Program {int(rng.integers(100,999))}", budget, spent, anomaly))
    return pd.DataFrame(rows, columns=["region","sector","year","project","budget","spent","anomaly"])

df = load_demo(regions, sectors, years)

# ───────────────────────── Filtering & KPIs ─────────────────────────
q = df.copy()
if region not in ("All Nepal","सारा नेपाल"): q = q[q["region"] == region]
if sector not in ("All","सबै"):             q = q[q["sector"] == sector]
q = q[q["year"] == year]

total_budget = int(q["budget"].sum()) if not q.empty else 0
total_spent  = int(q["spent"].sum())  if not q.empty else 0
exec_rate = (total_spent/total_budget*100) if total_budget else 0.0
anomalies = int(q["anomaly"].sum()) if not q.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="card"><div class="kpi-label">{T["k_total_budget"]}</div><div class="kpi-value">रु {total_budget:,.0f}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="card"><div class="kpi-label">{T["k_total_spent"]}</div><div class="kpi-value">रु {total_spent:,.0f}</div></div>', unsafe_allow_html=True)
with c3:
    prev = max(years[0], year-1)
    pv = df[df["year"]==prev]
    if region not in ("All Nepal","सारा नेपाल"): pv = pv[pv["region"]==region]
    if sector not in ("All","सबै"):             pv = pv[pv["sector"]==sector]
    prev_budget = pv["budget"].sum() if not pv.empty else 1
    delta = (total_budget - prev_budget)/prev_budget*100
    cls = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
    st.markdown(f'<div class="card"><div class="kpi-label">{T["k_exec_rate"]}</div><div class="kpi-value">{exec_rate:0.1f}%</div><div class="{cls}">{delta:+0.1f}% {T["delta_vs"]} {prev}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="card"><div class="kpi-label">{T["k_anomalies"]}</div><div class="kpi-value">{anomalies}</div></div>', unsafe_allow_html=True)

def fmt(n): return f"{int(n):,}"

# ───────────────────────── PDF report ─────────────────────────
def build_pdf_report(region, sector, year, total_budget, total_spent, exec_rate, anomalies, df_filtered, lang_key="en") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    x, y = 2*cm, H - 2*cm
    Tpdf = TEXT[lang_key]

    # Coat of arms at TOP-RIGHT
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "nepal_coat.png")
    try:
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            lw, lh = 2.8*cm, 2.8*cm
            c.drawImage(logo, W - lw - 2*cm, H - lh - 1.5*cm,
                        width=lw, height=lh, preserveAspectRatio=True, mask='auto')
        else:
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(W - 2*cm, H - 2.5*cm, "🇳🇵 Government of Nepal")
    except Exception:
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(W - 2*cm, H - 2.5*cm, "🇳🇵 Government of Nepal")

    # Title block (left)
    def line(txt, size=12, color=colors.HexColor("#000000"), dy=0.7*cm, bold=False):
        nonlocal y
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, txt); y -= dy
        if y < 2*cm:
            c.showPage(); y = H - 2*cm

    line(Tpdf["pdf_title_en"], size=18, bold=True)
    line(Tpdf["pdf_title_ne"], size=14, color=colors.HexColor("#444444"))
    line(f"{Tpdf['pdf_tr_title']} • Region: {region} • Sector: {sector} • Fiscal Year: {year}",
         size=11, color=colors.HexColor("#6b7280"))
    y -= 0.2*cm
    c.setFillColor(colors.HexColor("#ef4444")); c.setStrokeColor(colors.HexColor("#ef4444"))
    c.setLineWidth(1); c.line(x, y, W - 2*cm, y); y -= 0.5*cm

    # KPIs
    line(f"{TEXT['en']['k_total_budget'] if lang_key=='en' else TEXT['ne']['k_total_budget']}: रु {fmt(total_budget)}", size=11)
    line(f"{TEXT['en']['k_total_spent'] if lang_key=='en' else TEXT['ne']['k_total_spent']}:  रु {fmt(total_spent)}", size=11)
    line(f"{TEXT['en']['k_exec_rate'] if lang_key=='en' else TEXT['ne']['k_exec_rate']}: {exec_rate:0.1f}%", size=11)
    line(f"{TEXT['en']['k_anomalies'] if lang_key=='en' else TEXT['ne']['k_anomalies']}: {anomalies}", size=11)
    y -= 0.2*cm

    # Table header
    headers = Tpdf["pdf_headers"]
    col_x = [x, x+7.6*cm, x+11.5*cm, x+14.6*cm, x+16.6*cm, x+19.4*cm, x+21.6*cm]
    def draw_header():
        c.setFont("Helvetica-Bold", 10); c.setFillColor(colors.HexColor("#2563eb"))
        for hx, htxt in zip(col_x, headers): c.drawString(hx, y, htxt)
    draw_header(); y -= 0.45*cm
    c.setFillColor(colors.black); c.setFont("Helvetica", 9)

    # Rows + page breaks + repeat header
    if df_filtered.empty:
        c.setFillColor(colors.HexColor("#f87171")); c.drawString(x, y, TEXT[lang_key]["no_data"]); y -= 0.5*cm
    else:
        for _, r in df_filtered.iterrows():
            cells = [str(r["project"])[:40], str(r["region"])[:18], str(r["sector"])[:14],
                     str(r["year"]), fmt(r["budget"]), fmt(r["spent"]), str(int(r["anomaly"]))]
            for cx, cell in zip(col_x, cells):
                if cx >= col_x[-2]: c.drawRightString(cx+2.2*cm, y, cell)
                else:               c.drawString(cx, y, cell)
            y -= 0.38*cm
            if y < 2*cm:
                c.showPage(); y = H - 2*cm; draw_header(); y -= 0.45*cm
                c.setFillColor(colors.black); c.setFont("Helvetica", 9)

    # QR (bottom-right)
    try:
        target_url = "http://localhost:8506/"  # change to public URL on deploy
        qr_widget = qr.QrCodeWidget(target_url)
        bounds = qr_widget.getBounds(); w, h = bounds[2]-bounds[0], bounds[3]-bounds[1]
        size_cm = 3.0*cm
        d = Drawing(size_cm, size_cm, transform=[size_cm/w,0,0,size_cm/h,0,0]); d.add(qr_widget)
        renderPDF.draw(d, c, W - size_cm - 2*cm, 1.8*cm)
        c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#6b7280"))
        c.drawRightString(W - 2*cm, 1.5*cm, "Scan to view dashboard")
    except Exception:
        pass

    # Footer
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#9ca3af"))
    c.drawString(2*cm, 1.5*cm, "© 2025 Narayan Ranabhat • AI Minister – Nepal")
    c.save(); pdf_bytes = buf.getvalue(); buf.close(); return pdf_bytes

# ───────────────────────── Tabs ─────────────────────────
tab_over, tab_proj, tab_anom = st.tabs([f"📊 {T['tab_overview']}", f"🧭 {T['tab_projects']}", f"⚠️ {T['tab_anomalies']}"])

with tab_over:
    agg = q.groupby("sector", as_index=False)[["budget","spent"]].sum() if not q.empty else pd.DataFrame(columns=["sector","budget","spent"])
    if agg.empty:
        st.info(T["no_data"])
    else:
        base = alt.Chart(agg).encode(x=alt.X('sector:N', sort='-y', title=T["sector"]))
        chart = alt.layer(
            base.mark_bar().encode(y=alt.Y('budget:Q', title='रु'), color=alt.value('#ef4444')),
            base.mark_bar().encode(y='spent:Q', color=alt.value('#1f6feb'))
        ).properties(height=360, title=T["chart_title"])
        st.altair_chart(chart, use_container_width=True)

    st.markdown(f"#### {T['downloads']}")
    colA, colB, colC = st.columns(3)
    is_empty = q.empty
    with colA:
        st.download_button(T["dl_csv"], q.to_csv(index=False).encode("utf-8"),
                           file_name=f"budgets_{region}_{sector}_{year}.csv",
                           mime="text/csv", disabled=is_empty)
    with colB:
        st.download_button(T["dl_json"], q.to_json(orient="records").encode("utf-8"),
                           file_name=f"budgets_{region}_{sector}_{year}.json",
                           mime="application/json", disabled=is_empty)
    with colC:
        pdf_bytes = build_pdf_report(region, sector, year, total_budget, total_spent, exec_rate, anomalies, q, lang_key=lang)
        st.download_button(T["btn_pdf"], pdf_bytes,
                           file_name=f"transparency_{region}_{sector}_{year}.pdf",
                           mime="application/pdf", disabled=False)

    # Ask AI (beta) — optional, fails gracefully if no key
    st.markdown(f"### {T['ask_ai']}")
    user_q = st.text_input(T["ask_ai"], placeholder=T["ask_ai_ph"], label_visibility="collapsed")
    if user_q:
        try:
            import openai
            api_key = st.secrets.get("OPENAI_API_KEY", None)
            if not api_key:
                st.error(T["ask_ai_error"])
            else:
                openai.api_key = api_key
                df_json = q.to_json(orient="records")
                prompt = ("You are an AI analyst for Nepal's public budget data. "
                          "Analyze this JSON and answer briefly.\n"
                          f"DATA:\n{df_json}\n\nQUESTION: {user_q}")
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=180, temperature=0.2,
                )
                st.success(resp["choices"][0]["message"]["content"].strip())
        except Exception as e:
            st.error(f"{T['ask_ai_error']} ({e})")

with tab_proj:
    st.markdown(f"#### {T['list_projects']}")
    st.dataframe(q.sort_values("budget", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=420)

with tab_anom:
    st.markdown(f"#### {T['anomaly_flags']}")
    problems = q[q["anomaly"]==1].copy()
    if problems.empty:
        st.success(T["no_anoms"])
    else:
        problems["score"] = (problems["spent"] - problems["budget"]) / problems["budget"]
        st.dataframe(
            problems.sort_values("score", ascending=False)[["project","sector","region","year","budget","spent","score"]],
            use_container_width=True, height=420
        )

# ───────────────────────── Footer ─────────────────────────
st.markdown(f"<div class='small-muted' style='text-align:center;margin-top:8px'>{T['footer']}</div>", unsafe_allow_html=True)

