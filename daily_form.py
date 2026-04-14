# daily_form.py - READY TO DEPLOY VERSION

import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
import os
from io import BytesIO
import smtplib
from email.message import EmailMessage
from streamlit_drawable_canvas import st_canvas
import PIL.Image
import zipfile
import altair as alt

# --- Setup folders ---
os.makedirs("submitted_forms", exist_ok=True)
os.makedirs("archived_reports", exist_ok=True)

# --- Email Configuration (SAFE FOR DEPLOYMENT) ---
EMAIL_ADDRESS = st.secrets.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD")
RECIPIENT_EMAIL = st.secrets.get("RECIPIENT_EMAIL", "admin@example.com")


# --- Email Utility ---
def send_email_with_attachment(subject, body, to_email, file_path):
    try:
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            return  # Skip email if not configured

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(body)

        with open(file_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(file_path))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        st.warning(f"Email not sent: {e}")


# --- PDF Generator ---
def generate_pdf(data, signature_path=None):
    def safe_str(value):
        return str(value) if value is not None else ""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "KENYA URBAN ROADS AUTHORITY", ln=1, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Transforming Urban Mobility", ln=1, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "DAILY WORK FORM", ln=1, align="C")
    pdf.ln(6)

    pdf.set_font("Arial", "", 10)
    for field in ["Location/Region", "Project Name", "Contract No.", "Contractor", "Day", "Date"]:
        pdf.cell(45, 7, f"{field}:", border=0)
        pdf.cell(70, 7, safe_str(data.get(field)), border=0)
        if field in ["Contractor", "Date"]:
            pdf.ln(8)

    pdf.ln(5)

    # Save file
    file_name = f"submitted_forms/Daily_Work_Form_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    pdf.output(file_name)
    return file_name


# --- KPI ---
def display_kpi_summary(df):
    st.subheader("📊 Summary")
    col1, col2 = st.columns(2)
    col1.metric("Projects", df["Project Name"].nunique())
    col2.metric("Entries", len(df))


# --- MAIN FORM ---
def daily_work_form():
    st.title("📝 KURA Daily Works Submission Form")

    with st.form("form"):
        project_name = st.text_input("Project Name")
        contractor = st.text_input("Contractor")
        date = st.date_input("Date", value=datetime.date.today())

        confirm = st.checkbox("Confirm data")
        submitted = st.form_submit_button("Submit")

    if submitted and confirm:
        data = {
            "Project Name": project_name,
            "Contractor": contractor,
            "Date": date.strftime("%Y-%m-%d"),
        }

        # Generate PDF
        file_path = generate_pdf(data)

        # Move to archive (IMPORTANT FIX)
        archive_path = os.path.join("archived_reports", os.path.basename(file_path))
        os.rename(file_path, archive_path)

        # Save correct path
        st.session_state["last_file"] = archive_path

        # Send email
        send_email_with_attachment(
            "New Submission",
            f"{project_name} submitted",
            RECIPIENT_EMAIL,
            archive_path
        )

        st.success("✅ Form submitted and archived!")

        df = pd.DataFrame([data])
        display_kpi_summary(df)

    # --- DOWNLOAD SECTION (ARCHIVE ONLY) ---
    st.markdown("## 📁 Download Reports")

    files = [f for f in os.listdir("archived_reports") if f.endswith(".pdf")]

    if files:
        selected = st.selectbox("Select report", files)

        file_path = os.path.join("archived_reports", selected)

        with open(file_path, "rb") as f:
            st.download_button("📄 Download Selected", f, file_name=selected)

        # ZIP download
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            for file in files:
                z.write(os.path.join("archived_reports", file), arcname=file)

        zip_buffer.seek(0)

        st.download_button(
            "📦 Download All (ZIP)",
            zip_buffer,
            file_name="reports.zip"
        )

    else:
        st.info("No reports yet.")


# --- RUN ---
if __name__ == "__main__":
    daily_work_form()
