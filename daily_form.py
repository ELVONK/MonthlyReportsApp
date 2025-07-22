# daily_form.py - Module for Daily Work Form Integration

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

# Create folder to store PDFs
os.makedirs("submitted_forms", exist_ok=True)

# Email Configuration (secured using environment variables)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "admin@example.com")

def send_email_with_attachment(subject, body, to_email, file_path):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg.set_content(body)

        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
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

def generate_pdf(data, signature_path=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)

    pdf.cell(200, 10, txt="KENYA URBAN ROADS AUTHORITY (KURA)", ln=1, align='C')
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="DAILY WORK FORM", ln=1, align='C')
    pdf.ln(5)

    for key, value in data.items():
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, txt=f"{key}: {value if value else ''}")

    if signature_path and os.path.exists(signature_path):
        pdf.ln(10)
        pdf.set_font("Arial", "I", 11)
        pdf.cell(0, 10, "Signature:", ln=1)
        pdf.image(signature_path, x=10, y=pdf.get_y(), w=60)
        pdf.ln(25)

    # Add QR Code linking to a summary or archive (optional)
    qr = qrcode.make("KURA Daily Work Submission")
    qr_path = "submitted_forms/qr_temp.png"
    qr.save(qr_path)
    pdf.image(qr_path, x=150, y=pdf.get_y() - 20, w=40)

    file_name = f"submitted_forms/Daily_Work_Form_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    pdf.output(file_name)
    return file_name

def daily_work_form():
    st.title("📝 Daily Works Submission Form")

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

        weather = st.text_area("Weather Conditions")
        equipment = st.text_area("Plant and Equipment")
        materials = st.text_area("Materials Delivered")
        labour = st.text_area("Labour")
        operations = st.text_area("Operations")

        st.markdown("**Draw your signature:**")
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0.3)",
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
            "Weather Conditions": weather,
            "Plant and Equipment": equipment,
            "Materials Delivered": materials,
            "Labour": labour,
            "Operations": operations,
        }

        file_path = generate_pdf(data, sig_path)
        send_email_with_attachment(
            subject="📝 New Daily Work Form Submitted",
            body=f"Form for project '{project_name}' submitted on {date}.",
            to_email=RECIPIENT_EMAIL,
            file_path=file_path
        )

        st.session_state["submitted_form_path"] = file_path
        st.success("Form submitted successfully!")

    if "submitted_form_path" in st.session_state:
        with open(st.session_state["submitted_form_path"], "rb") as f:
            st.download_button(
                "📄 Download Submitted PDF",
                f,
                file_name=os.path.basename(st.session_state["submitted_form_path"]),
                mime="application/pdf"
            )
