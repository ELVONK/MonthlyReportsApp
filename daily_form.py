# daily_form.py - Complete KURA Daily Work Form Streamlit Application (Error-safe version)

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
import qrcode
import altair as alt

# --- Setup folders ---
os.makedirs("submitted_forms", exist_ok=True)
os.makedirs("archived_reports", exist_ok=True)

# --- Email Configuration ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "admin@example.com")


# --- Email Utility ---
def send_email_with_attachment(subject, body, to_email, file_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg.set_content(body)

        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)
            msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except smtplib.SMTPAuthenticationError:
        st.error("❌ SMTP Authentication Error: Check your email credentials in secrets.toml")
    except smtplib.SMTPRecipientsRefused:
        st.error("❌ Recipient email address is not accepted.")
    except smtplib.SMTPConnectError:
        st.error("❌ Connection error: Failed to connect to SMTP server.")
    except Exception as e:
        st.error(f"❌ Email sending failed: {e}")


# --- PDF Generator ---
def generate_pdf(data, signature_path=None):
    def safe_str(value):
        """Convert any value to safe printable string for FPDF"""
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

    # Header info
    pdf.set_font("Arial", "", 10)
    for field in ["Location/Region", "Project Name", "Contract No.", "Contractor", "Day", "Date"]:
        pdf.cell(45, 7, f"{field}:", border=0)
        pdf.cell(70, 7, safe_str(data.get(field)), border=0)
        if field in ["Contractor", "Date"]:
            pdf.ln(8)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "TIME OF OPERATION", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 7, "From:", 1)
    pdf.cell(50, 7, safe_str(data.get("Time of Operation From")), 1)
    pdf.cell(40, 7, "To:", 1)
    pdf.cell(50, 7, safe_str(data.get("To")), 1, ln=1)
    pdf.ln(4)

    # WEATHER SECTION
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "WEATHER CONDITIONS", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(50, 7, "Time Duration", 1)
    pdf.cell(70, 7, "Weather Conditions", 1)
    pdf.cell(70, 7, "Remarks", 1, ln=1)
    for row in data.get("Weather", []):
        pdf.cell(50, 7, safe_str(row.get("Time Duration")), 1)
        pdf.cell(70, 7, safe_str(row.get("Weather Conditions")), 1)
        pdf.cell(70, 7, safe_str(row.get("Remarks")), 1, ln=1)
    pdf.ln(5)

    # PLANT AND EQUIPMENT
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "PLANT AND EQUIPMENT", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(60, 7, "Description", 1)
    pdf.cell(30, 7, "Plate No.", 1)
    pdf.cell(50, 7, "Time From", 1)
    pdf.cell(50, 7, "Time To", 1, ln=1)
    for row in data.get("Equipment", []):
        pdf.cell(60, 7, safe_str(row.get("Description")), 1)
        pdf.cell(30, 7, safe_str(row.get("Plate No.")), 1)
        pdf.cell(50, 7, safe_str(row.get("Time From")), 1)
        pdf.cell(50, 7, safe_str(row.get("Time To")), 1, ln=1)
    pdf.ln(5)

    # MATERIALS DELIVERED
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "MATERIALS DELIVERED TO SITE", ln=1)
    pdf.set_font("Arial", "", 9)
    headers = ["Description", "Unit", "Truck Plate No.", "Truck Capacity (m³)", "Freq", "Total Qty", "Remarks"]
    widths = [40, 20, 30, 25, 15, 25, 35]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 7, h, 1)
    pdf.ln(7)
    for row in data.get("Materials", []):
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 7, safe_str(row.get(h)), 1)
        pdf.ln(7)
    pdf.ln(5)

    # LABOUR
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "LABOUR", ln=1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(90, 7, "Personnel", 1)
    pdf.cell(90, 7, "No.", 1, ln=1)
    for row in data.get("Labour", []):
        pdf.cell(90, 7, safe_str(row.get("Personnel")), 1)
        pdf.cell(90, 7, safe_str(row.get("No.")), 1, ln=1)
    pdf.ln(5)

    # OPERATIONS
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "OPERATIONS", ln=1)
    pdf.set_font("Arial", "", 9)
    headers_ops = ["Chainage (From)", "Chainage (To)", "Activity Description", "Remarks"]
    widths_ops = [35, 35, 80, 40]
    for i, h in enumerate(headers_ops):
        pdf.cell(widths_ops[i], 7, h, 1)
    pdf.ln(7)
    for row in data.get("Operations", []):
        for i, h in enumerate(headers_ops):
            pdf.cell(widths_ops[i], 7, safe_str(row.get(h)), 1)
        pdf.ln(7)

    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, "Inspector: ____________________", ln=1)
    pdf.cell(0, 6, "Site Agent: ____________________", ln=1)
    pdf.cell(0, 6, "R.E. / A.R.E: ____________________", ln=1)

    # Signature
    if signature_path and os.path.exists(signature_path):
        pdf.image(signature_path, x=150, y=pdf.get_y() - 25, w=40)

    # Footer
    pdf.set_y(-20)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 6, "Form No.: KURA/MS/FM/029", ln=1, align="L")
    pdf.cell(0, 6, "ISSUE NO: 001   REV. NO: 003   ISSUE DATE: 24/2/2025", ln=1, align="R")

    file_name = f"submitted_forms/Daily_Work_Form_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    pdf.output(file_name)
    return file_name


# --- KPI & Chart Dashboard ---
def display_kpi_summary(df):
    st.subheader("📊 Daily Work Report Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Projects", df["Project Name"].nunique())
    col2.metric("Total Labour Records", df["Labour Count"].sum())
    col3.metric("Total Materials Entries", df["Materials Count"].sum())

    daily_count = df.groupby("Date").size().reset_index(name="Submissions")
    chart = (
        alt.Chart(daily_count)
        .mark_line(point=True)
        .encode(x="Date:T", y="Submissions:Q", tooltip=["Date", "Submissions"])
        .properties(title="Submission Trend Over Time", height=300)
    )
    st.altair_chart(chart, use_container_width=True)


# --- Main Streamlit Form ---
def daily_work_form():
    st.title("📝 KURA Daily Works Submission Form")

    with st.form("daily_work_form"):
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Location/Region")
            project_name = st.text_input("Project Name")
            contract_no = st.text_input("Contract No.")
            contractor = st.text_input("Contractor")
            date = st.date_input("Date", value=datetime.date.today())
            day = st.text_input("Day")
        with col2:
            sheet_no = st.text_input("Sheet No.")
            total_sheets = st.text_input("Total Sheets")
            time_from = st.text_input("Time of Operation From")
            time_to = st.text_input("To")
            inspector = st.text_input("Inspector")
            site_agent = st.text_input("Site Agent")
            re_are = st.text_input("R.E. / A.R.E")

        # Structured Inputs
        st.markdown("### ☁️ Weather Conditions")
        weather_data = st.data_editor(pd.DataFrame(columns=["Time Duration", "Weather Conditions", "Remarks"]),
                                      use_container_width=True, num_rows="dynamic")

        st.markdown("### ⚙️ Plant and Equipment")
        equipment_data = st.data_editor(pd.DataFrame(columns=["Description", "Plate No.", "Time From", "Time To"]),
                                        use_container_width=True, num_rows="dynamic")

        st.markdown("### 🧱 Materials Delivered to Site")
        materials_data = st.data_editor(pd.DataFrame(columns=["Description", "Unit", "Truck Plate No.",
                                                              "Truck Capacity (m³)", "Freq", "Total Qty", "Remarks"]),
                                        use_container_width=True, num_rows="dynamic")

        st.markdown("### 👷 Labour")
        labour_data = st.data_editor(pd.DataFrame(columns=["Personnel", "No."]),
                                     use_container_width=True, num_rows="dynamic")

        st.markdown("### 🚧 Operations")
        operations_data = st.data_editor(pd.DataFrame(columns=["Chainage (From)", "Chainage (To)",
                                                               "Activity Description", "Remarks"]),
                                         use_container_width=True, num_rows="dynamic")

        # Signature
        st.markdown("**Draw your signature:**")
        canvas_result = st_canvas(
            fill_color="rgba(0,0,0,0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#ffffff",
            update_streamlit=True,
            height=150,
            drawing_mode="freedraw",
            key="canvas",
        )

        confirm = st.checkbox("I confirm the above information is correct")
        submitted = st.form_submit_button("Submit Form")

    # --- Form Submission ---
    if submitted and confirm:
        sig_path = None
        if canvas_result.image_data is not None:
            img = PIL.Image.fromarray((canvas_result.image_data).astype("uint8"))
            sig_path = f"submitted_forms/signature_{project_name.replace(' ', '_')}.png"
            img.save(sig_path)

        data = {
            "Location/Region": location,
            "Project Name": project_name,
            "Contract No.": contract_no,
            "Contractor": contractor,
            "Date": date.strftime("%Y-%m-%d"),
            "Day": day,
            "Sheet No.": sheet_no,
            "Total Sheets": total_sheets,
            "Time of Operation From": time_from,
            "To": time_to,
            "Inspector": inspector,
            "Site Agent": site_agent,
            "R.E. / A.R.E": re_are,
            "Weather": weather_data.to_dict(orient="records"),
            "Equipment": equipment_data.to_dict(orient="records"),
            "Materials": materials_data.to_dict(orient="records"),
            "Labour": labour_data.to_dict(orient="records"),
            "Operations": operations_data.to_dict(orient="records"),
        }

        file_path = generate_pdf(data, sig_path)
        send_email_with_attachment(
            subject="📝 New Daily Work Form Submitted",
            body=f"Form for project '{project_name}' submitted on {date}.",
            to_email=RECIPIENT_EMAIL,
            file_path=file_path
        )

        st.session_state["submitted_form_path"] = file_path
        st.success("✅ Form submitted successfully!")

        archive_path = os.path.join("archived_reports", os.path.basename(file_path))
        os.rename(file_path, archive_path)
        st.success(f"Form archived in: {archive_path}")

        # KPI dashboard summary
        df_summary = pd.DataFrame([{
            "Project Name": project_name,
            "Date": date,
            "Labour Count": len(labour_data),
            "Materials Count": len(materials_data)
        }])
        display_kpi_summary(df_summary)

    # Download
    if "submitted_form_path" in st.session_state and os.path.exists(st.session_state["submitted_form_path"]):
        with open(st.session_state["submitted_form_path"], "rb") as f:
            st.download_button(
                "📄 Download Submitted PDF",
                f,
                file_name=os.path.basename(st.session_state["submitted_form_path"]),
                mime="application/pdf"
            )


# --- Entry Point ---
if __name__ == "__main__":
    daily_work_form()
