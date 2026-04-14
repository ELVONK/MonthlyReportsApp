"""
daily_form.py - KURA Daily Works Form with Archive Dashboard + GitHub Storage
"""

import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
import os
from io import BytesIO
import smtplib
from email.message import EmailMessage
import zipfile
import base64
import json
import requests

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="KURA Daily Works",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# CUSTOM CSS  – industrial / utilitarian theme
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0D1117;
    border-right: 2px solid #F0A500;
}
[data-testid="stSidebar"] * { color: #E6EDF3 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 15px; }

/* Main background */
.main { background: #F5F5F0; }

/* Page title stripe */
.kura-header {
    background: #0D1117;
    color: #F0A500;
    padding: 18px 28px;
    border-left: 6px solid #F0A500;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 24px;
    letter-spacing: 1px;
}
.kura-sub {
    color: #6E7681;
    font-size: 13px;
    font-family: 'IBM Plex Mono', monospace;
    margin-top: -18px;
    margin-bottom: 20px;
}

/* Cards */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    border-top: 4px solid #F0A500;
    border-radius: 6px;
    padding: 20px 24px;
    text-align: center;
}
.kpi-number {
    font-size: 36px;
    font-weight: 700;
    color: #0D1117;
    font-family: 'IBM Plex Mono', monospace;
}
.kpi-label {
    font-size: 12px;
    color: #6E7681;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* Form card */
.form-card {
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    border-radius: 6px;
    padding: 28px;
    margin-bottom: 20px;
}

/* Archive table */
.archive-row {
    background: white;
    border: 1px solid #E6EDF3;
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
}
.badge {
    background: #F0A500;
    color: #0D1117;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}

/* Buttons */
.stButton > button {
    background: #0D1117 !important;
    color: #F0A500 !important;
    border: 1px solid #F0A500 !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
}
.stButton > button:hover {
    background: #F0A500 !important;
    color: #0D1117 !important;
}
.stDownloadButton > button {
    background: #1F6FEB !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# FOLDER SETUP
# ─────────────────────────────────────────
os.makedirs("submitted_forms", exist_ok=True)
os.makedirs("archived_reports", exist_ok=True)

# ─────────────────────────────────────────
# SECRETS (safe for deployment)
# ─────────────────────────────────────────
EMAIL_ADDRESS  = st.secrets.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD")
RECIPIENT_EMAIL = st.secrets.get("RECIPIENT_EMAIL", "admin@example.com")
GITHUB_TOKEN    = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO     = st.secrets.get("GITHUB_REPO", "")        # e.g. "username/kura-forms"
GITHUB_BRANCH   = st.secrets.get("GITHUB_BRANCH", "main")


# ─────────────────────────────────────────
# GITHUB STORAGE
# ─────────────────────────────────────────
def upload_to_github(local_path: str, github_filename: str) -> bool:
    """Push a PDF file to the GitHub repo under /archived_reports/."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False
    try:
        with open(local_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode()

        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/archived_reports/{github_filename}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Check if file already exists (need SHA for update)
        check = requests.get(api_url, headers=headers)
        payload = {
            "message": f"Add form: {github_filename}",
            "content": content_b64,
            "branch": GITHUB_BRANCH,
        }
        if check.status_code == 200:
            payload["sha"] = check.json()["sha"]

        resp = requests.put(api_url, headers=headers, json=payload)
        return resp.status_code in (200, 201)
    except Exception as e:
        st.warning(f"GitHub upload failed: {e}")
        return False


def list_github_files() -> list[dict]:
    """List PDF files stored in the GitHub repo archive folder."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return []
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/archived_reports"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        resp = requests.get(api_url, headers=headers)
        if resp.status_code == 200:
            return [f for f in resp.json() if f["name"].endswith(".pdf")]
        return []
    except Exception:
        return []


def download_from_github(download_url: str) -> bytes | None:
    """Fetch raw bytes of a file from GitHub."""
    try:
        resp = requests.get(download_url)
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception:
        return None


# ─────────────────────────────────────────
# EMAIL UTILITY
# ─────────────────────────────────────────
def send_email_with_attachment(subject, body, to_email, file_path):
    try:
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            return
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(body)
        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(), maintype="application", subtype="pdf",
                filename=os.path.basename(file_path),
            )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        st.warning(f"Email not sent: {e}")


# ─────────────────────────────────────────
# PDF GENERATOR  (full-featured form)
# ─────────────────────────────────────────
def generate_pdf(data: dict) -> str:
    def s(key): return str(data.get(key, ""))

    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_fill_color(13, 17, 23)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(240, 165, 0)
    pdf.cell(0, 10, "KENYA URBAN ROADS AUTHORITY", ln=0, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 8, "Transforming Urban Mobility  |  DAILY WORKS REPORT", ln=1, align="C")
    pdf.ln(6)

    # Reset colours
    pdf.set_text_color(0, 0, 0)

    # Two-column header info
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 237, 243)
    pdf.cell(0, 7, "PROJECT INFORMATION", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)

    left = [
        ("Project Name", s("Project Name")),
        ("Contract No.", s("Contract No.")),
        ("Contractor",   s("Contractor")),
    ]
    right = [
        ("Location/Region", s("Location/Region")),
        ("Date",            s("Date")),
        ("Day",             s("Day")),
    ]
    for (lk, lv), (rk, rv) in zip(left, right):
        pdf.set_font("Arial", "B", 9)
        pdf.cell(30, 7, lk + ":", border=0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(60, 7, lv, border=0)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(30, 7, rk + ":", border=0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 7, rv, border=0, ln=1)

    pdf.ln(4)

    # Works section
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 237, 243)
    pdf.cell(0, 7, "WORKS CARRIED OUT", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, s("Works Description") or "N/A")
    pdf.ln(3)

    # Labour section
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 237, 243)
    pdf.cell(0, 7, "LABOUR", ln=1, fill=True)

    labour_cols = ["Category", "No. Present", "Hours Worked"]
    col_w = [80, 50, 60]
    pdf.set_font("Arial", "B", 9)
    for i, col in enumerate(labour_cols):
        pdf.cell(col_w[i], 7, col, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", "", 9)
    for row in data.get("Labour", []):
        for i, col in enumerate(labour_cols):
            pdf.cell(col_w[i], 7, str(row.get(col, "")), border=1, align="C")
        pdf.ln()

    pdf.ln(4)

    # Plant & Equipment
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 237, 243)
    pdf.cell(0, 7, "PLANT & EQUIPMENT", ln=1, fill=True)
    plant_cols = ["Equipment", "No.", "Hours"]
    col_w2 = [100, 40, 50]
    pdf.set_font("Arial", "B", 9)
    for i, col in enumerate(plant_cols):
        pdf.cell(col_w2[i], 7, col, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", "", 9)
    for row in data.get("Plant", []):
        for i, col in enumerate(plant_cols):
            pdf.cell(col_w2[i], 7, str(row.get(col, "")), border=1, align="C")
        pdf.ln()

    pdf.ln(4)

    # Materials
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 237, 243)
    pdf.cell(0, 7, "MATERIALS USED", ln=1, fill=True)
    mat_cols = ["Material", "Unit", "Quantity"]
    col_w3 = [90, 50, 50]
    pdf.set_font("Arial", "B", 9)
    for i, col in enumerate(mat_cols):
        pdf.cell(col_w3[i], 7, col, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", "", 9)
    for row in data.get("Materials", []):
        for i, col in enumerate(mat_cols):
            pdf.cell(col_w3[i], 7, str(row.get(col, "")), border=1, align="C")
        pdf.ln()

    pdf.ln(4)

    # Remarks
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 237, 243)
    pdf.cell(0, 7, "REMARKS / ISSUES", ln=1, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, s("Remarks") or "None")

    pdf.ln(8)

    # Signature line
    pdf.set_font("Arial", "B", 9)
    pdf.cell(95, 7, "Resident Engineer Signature: ____________________")
    pdf.cell(0,  7, "Date: __________________")

    # Save
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname = f"Daily_Work_Form_{s('Project Name').replace(' ','_')}_{ts}.pdf"
    local_path = os.path.join("archived_reports", fname)
    pdf.output(local_path)
    return local_path, fname


# ─────────────────────────────────────────
# PRINTABLE HTML VIEW
# ─────────────────────────────────────────
def render_printable_html(data: dict) -> str:
    def s(k): return str(data.get(k, ""))

    labour_rows = "".join(
        f"<tr><td>{r.get('Category','')}</td><td>{r.get('No. Present','')}</td><td>{r.get('Hours Worked','')}</td></tr>"
        for r in data.get("Labour", [])
    ) or "<tr><td colspan='3'>—</td></tr>"

    plant_rows = "".join(
        f"<tr><td>{r.get('Equipment','')}</td><td>{r.get('No.','')}</td><td>{r.get('Hours','')}</td></tr>"
        for r in data.get("Plant", [])
    ) or "<tr><td colspan='3'>—</td></tr>"

    mat_rows = "".join(
        f"<tr><td>{r.get('Material','')}</td><td>{r.get('Unit','')}</td><td>{r.get('Quantity','')}</td></tr>"
        for r in data.get("Materials", [])
    ) or "<tr><td colspan='3'>—</td></tr>"

    return f"""
    <html><head><style>
    @media print {{ .no-print {{ display:none; }} }}
    body {{ font-family: Arial, sans-serif; font-size: 11px; margin: 20px; }}
    h1 {{ text-align:center; background:#0D1117; color:#F0A500; padding:10px; }}
    h2 {{ background:#E6EDF3; padding:5px 8px; font-size:12px; }}
    table {{ width:100%; border-collapse:collapse; margin-bottom:12px; }}
    th, td {{ border:1px solid #ccc; padding:5px; text-align:left; }}
    th {{ background:#f0f0f0; }}
    .meta {{ display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-bottom:12px; }}
    .meta div {{ padding:4px 0; border-bottom:1px solid #eee; }}
    .meta span {{ font-weight:bold; }}
    </style></head><body>
    <h1>KENYA URBAN ROADS AUTHORITY — DAILY WORKS REPORT</h1>
    <div class="meta">
      <div><span>Project:</span> {s("Project Name")}</div>
      <div><span>Location:</span> {s("Location/Region")}</div>
      <div><span>Contract No.:</span> {s("Contract No.")}</div>
      <div><span>Date:</span> {s("Date")}</div>
      <div><span>Contractor:</span> {s("Contractor")}</div>
      <div><span>Day:</span> {s("Day")}</div>
    </div>
    <h2>WORKS CARRIED OUT</h2>
    <p>{s("Works Description") or "N/A"}</p>
    <h2>LABOUR</h2>
    <table><tr><th>Category</th><th>No. Present</th><th>Hours Worked</th></tr>{labour_rows}</table>
    <h2>PLANT & EQUIPMENT</h2>
    <table><tr><th>Equipment</th><th>No.</th><th>Hours</th></tr>{plant_rows}</table>
    <h2>MATERIALS USED</h2>
    <table><tr><th>Material</th><th>Unit</th><th>Quantity</th></tr>{mat_rows}</table>
    <h2>REMARKS / ISSUES</h2>
    <p>{s("Remarks") or "None"}</p>
    <br/>
    <p>Resident Engineer Signature: _________________________ &nbsp;&nbsp; Date: _____________</p>
    <button class="no-print" onclick="window.print()" style="padding:8px 20px;background:#0D1117;color:#F0A500;border:none;cursor:pointer;font-size:13px;">
    🖨️ Print / Save as PDF</button>
    </body></html>
    """


# ─────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛣️ KURA Works")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📝 Submit Form", "📁 Archive Dashboard"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Storage**")
    if GITHUB_TOKEN and GITHUB_REPO:
        st.success(f"✅ GitHub: `{GITHUB_REPO}`")
    else:
        st.warning("⚠️ GitHub not configured\nAdd secrets to enable.")
    st.markdown("---")
    st.caption("KURA Daily Works v2.0")


# ═══════════════════════════════════════════════════════════════════
# PAGE 1 — SUBMISSION FORM
# ═══════════════════════════════════════════════════════════════════
if page == "📝 Submit Form":
    st.markdown('<div class="kura-header">📝 DAILY WORKS SUBMISSION</div>', unsafe_allow_html=True)
    st.markdown('<div class="kura-sub">Complete all sections then submit to generate & archive the report.</div>', unsafe_allow_html=True)

    with st.form("daily_form"):

        # ── Project Info ──────────────────────────────────────
        st.markdown("#### 🏗️ Project Information")
        c1, c2, c3 = st.columns(3)
        project_name  = c1.text_input("Project Name *")
        contract_no   = c2.text_input("Contract No.")
        location      = c3.text_input("Location / Region")

        c4, c5, c6 = st.columns(3)
        contractor = c4.text_input("Contractor *")
        date       = c5.date_input("Date", value=datetime.date.today())
        day        = c6.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])

        st.markdown("---")

        # ── Works Description ─────────────────────────────────
        st.markdown("#### 🔨 Works Carried Out")
        works_desc = st.text_area("Describe work done today", height=100)

        st.markdown("---")

        # ── Labour ────────────────────────────────────────────
        st.markdown("#### 👷 Labour")
        st.caption("Fill in rows that apply; leave others blank.")
        labour_categories = ["Foreman","Skilled Labourers","Unskilled Labourers","Operators","Drivers"]
        labour_data = []
        l_cols = st.columns(3)
        l_cols[0].markdown("**Category**")
        l_cols[1].markdown("**No. Present**")
        l_cols[2].markdown("**Hours Worked**")
        for cat in labour_categories:
            lc1, lc2, lc3 = st.columns(3)
            lc1.markdown(cat)
            n  = lc2.number_input("", min_value=0, key=f"l_n_{cat}", label_visibility="collapsed")
            hr = lc3.number_input("", min_value=0.0, step=0.5, key=f"l_h_{cat}", label_visibility="collapsed")
            if n > 0:
                labour_data.append({"Category": cat, "No. Present": int(n), "Hours Worked": hr})

        st.markdown("---")

        # ── Plant & Equipment ─────────────────────────────────
        st.markdown("#### 🚜 Plant & Equipment")
        plant_types = ["Grader","Roller","Tipper Truck","Excavator","Water Bowser","Generator","Compactor"]
        plant_data = []
        p_cols = st.columns(3)
        p_cols[0].markdown("**Equipment**")
        p_cols[1].markdown("**No.**")
        p_cols[2].markdown("**Hours**")
        for pt in plant_types:
            pc1, pc2, pc3 = st.columns(3)
            pc1.markdown(pt)
            pn  = pc2.number_input("", min_value=0, key=f"p_n_{pt}", label_visibility="collapsed")
            phr = pc3.number_input("", min_value=0.0, step=0.5, key=f"p_h_{pt}", label_visibility="collapsed")
            if pn > 0:
                plant_data.append({"Equipment": pt, "No.": int(pn), "Hours": phr})

        st.markdown("---")

        # ── Materials ─────────────────────────────────────────
        st.markdown("#### 🧱 Materials Used")
        mat_list = [
            ("Gravel/Hardcore", "m³"), ("Bitumen", "litres"), ("Cement", "bags"),
            ("Sand", "m³"), ("Culverts", "No."), ("Steel Reinforcement", "kg"),
        ]
        mat_data = []
        m_cols = st.columns(3)
        m_cols[0].markdown("**Material**")
        m_cols[1].markdown("**Unit**")
        m_cols[2].markdown("**Quantity**")
        for mat, unit in mat_list:
            mc1, mc2, mc3 = st.columns(3)
            mc1.markdown(mat)
            mc2.markdown(unit)
            qty = mc3.number_input("", min_value=0.0, step=0.5, key=f"m_{mat}", label_visibility="collapsed")
            if qty > 0:
                mat_data.append({"Material": mat, "Unit": unit, "Quantity": qty})

        st.markdown("---")

        # ── Remarks ───────────────────────────────────────────
        st.markdown("#### 📋 Remarks / Issues")
        remarks = st.text_area("Any issues, delays or special notes", height=80)

        confirm   = st.checkbox("✅ I confirm the information above is accurate")
        submitted = st.form_submit_button("📤 Submit & Generate Report", use_container_width=True)

    # ── Handle submission ──────────────────────────────────
    if submitted:
        if not confirm:
            st.error("Please confirm the data before submitting.")
        elif not project_name or not contractor:
            st.error("Project Name and Contractor are required.")
        else:
            data = {
                "Project Name":    project_name,
                "Contract No.":    contract_no,
                "Location/Region": location,
                "Contractor":      contractor,
                "Date":            date.strftime("%Y-%m-%d"),
                "Day":             day,
                "Works Description": works_desc,
                "Labour":          labour_data,
                "Plant":           plant_data,
                "Materials":       mat_data,
                "Remarks":         remarks,
            }

            with st.spinner("Generating report…"):
                local_path, fname = generate_pdf(data)

            # GitHub upload
            gh_ok = upload_to_github(local_path, fname)

            # Email
            send_email_with_attachment(
                f"KURA Daily Works — {project_name} — {date}",
                f"New daily works submission for {project_name}.",
                RECIPIENT_EMAIL,
                local_path,
            )

            st.success("✅ Report generated and archived!")
            if gh_ok:
                st.info(f"☁️ Synced to GitHub: `{GITHUB_REPO}/archived_reports/{fname}`")

            # Store in session for inline preview
            st.session_state["preview_data"] = data
            st.session_state["preview_path"] = local_path

            # Download button
            with open(local_path, "rb") as f:
                st.download_button(
                    "📄 Download PDF Now",
                    f,
                    file_name=fname,
                    mime="application/pdf",
                )

    # Inline print preview
    if "preview_data" in st.session_state:
        with st.expander("🖨️ Print Preview", expanded=False):
            html = render_printable_html(st.session_state["preview_data"])
            st.components.v1.html(html, height=700, scrolling=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE 2 — ARCHIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════
else:
    st.markdown('<div class="kura-header">📁 ARCHIVE DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown('<div class="kura-sub">Browse, download, and print all submitted reports.</div>', unsafe_allow_html=True)

    # ── Tabs: local vs GitHub ─────────────────────────────────
    tab_local, tab_github = st.tabs(["💾 Local Archive", "☁️ GitHub Archive"])

    # ── LOCAL ────────────────────────────────────────────────
    with tab_local:
        local_files = sorted(
            [f for f in os.listdir("archived_reports") if f.endswith(".pdf")],
            reverse=True,
        )

        if not local_files:
            st.info("No local reports yet. Submit a form to get started.")
        else:
            # KPIs
            k1, k2, k3 = st.columns(3)
            k1.markdown(f'<div class="kpi-card"><div class="kpi-number">{len(local_files)}</div><div class="kpi-label">Total Reports</div></div>', unsafe_allow_html=True)

            # All-in-one ZIP
            zip_buf = BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as z:
                for f in local_files:
                    z.write(os.path.join("archived_reports", f), arcname=f)
            zip_buf.seek(0)

            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"**{len(local_files)} report(s) found**")
            col_b.download_button(
                "📦 Download All (ZIP)",
                zip_buf,
                file_name="kura_reports.zip",
                mime="application/zip",
            )

            st.markdown("---")

            # Search / filter
            search = st.text_input("🔍 Filter by filename", "")
            filtered = [f for f in local_files if search.lower() in f.lower()] if search else local_files

            for fname in filtered:
                fpath = os.path.join("archived_reports", fname)
                fsize = os.path.getsize(fpath)
                fcols = st.columns([5, 1, 1, 1])
                fcols[0].markdown(f"📄 `{fname}`  \n<small style='color:#6E7681'>{fsize/1024:.1f} KB</small>", unsafe_allow_html=True)

                with open(fpath, "rb") as f:
                    fcols[1].download_button(
                        "⬇️ PDF",
                        f,
                        file_name=fname,
                        mime="application/pdf",
                        key=f"dl_{fname}",
                    )

                if fcols[2].button("🖨️ Print", key=f"pr_{fname}"):
                    st.session_state["print_file"] = fpath
                    st.session_state["print_fname"] = fname

                # GitHub sync button
                if GITHUB_TOKEN and GITHUB_REPO:
                    if fcols[3].button("☁️ Sync", key=f"gh_{fname}"):
                        with st.spinner("Uploading…"):
                            ok = upload_to_github(fpath, fname)
                        if ok:
                            st.success(f"Synced {fname} to GitHub!")
                        else:
                            st.error("Upload failed.")

            # Print preview panel
            if "print_file" in st.session_state:
                st.markdown("---")
                st.markdown(f"#### 🖨️ Print Preview — `{st.session_state['print_fname']}`")
                st.caption("Use your browser's print dialog (Ctrl+P / ⌘+P) or click the button inside the preview.")

                # Render as embedded PDF viewer
                with open(st.session_state["print_file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()

                pdf_display = f"""
                <div style="border:2px solid #F0A500; border-radius:4px; overflow:hidden;">
                <iframe
                    src="data:application/pdf;base64,{b64}#toolbar=1&navpanes=0&scrollbar=1"
                    width="100%" height="700px"
                    style="border:none;">
                </iframe>
                </div>
                <br/>
                <button onclick="window.frames[0].print()"
                    style="background:#0D1117;color:#F0A500;border:1px solid #F0A500;
                           padding:8px 20px;border-radius:4px;cursor:pointer;font-size:13px;">
                🖨️ Print this Report
                </button>
                """
                st.markdown(pdf_display, unsafe_allow_html=True)

    # ── GITHUB ────────────────────────────────────────────────
    with tab_github:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            st.warning("""
**GitHub not configured.**  
Add these secrets to your Streamlit deployment:

| Secret | Value |
|--------|-------|
| `GITHUB_TOKEN` | Your Personal Access Token |
| `GITHUB_REPO` | `username/repo-name` |
| `GITHUB_BRANCH` | `main` (or your branch) |
            """)
        else:
            st.info(f"Browsing `{GITHUB_REPO}` / `archived_reports/`")

            with st.spinner("Fetching from GitHub…"):
                gh_files = list_github_files()

            if not gh_files:
                st.info("No files found in GitHub archive yet.")
            else:
                g1, g2 = st.columns([4, 1])
                g1.markdown(f"**{len(gh_files)} file(s) on GitHub**")

                for gf in gh_files:
                    gc1, gc2 = st.columns([6, 1])
                    gc1.markdown(f"☁️ `{gf['name']}`  \n<small style='color:#6E7681'>{gf.get('size',0)/1024:.1f} KB</small>", unsafe_allow_html=True)

                    raw_url = gf.get("download_url", "")
                    if gc2.button("⬇️ Download", key=f"ghd_{gf['name']}"):
                        file_bytes = download_from_github(raw_url)
                        if file_bytes:
                            st.download_button(
                                "Save PDF",
                                file_bytes,
                                file_name=gf["name"],
                                mime="application/pdf",
                                key=f"ghsave_{gf['name']}",
                            )
