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

# Create folder to store PDFs
os.makedirs("submitted_forms", exist_ok=True)

# Email Configuration (secured using environment variables)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "admin@example.com")

def send_email_with_attachment(subject, body, to_email, file_path):
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

def generate_pdf(data, signature_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 33)
    pdf.cell(200, 10, txt="KENYA URBAN ROADS AUTHORITY", ln=True, align='C')
    pdf.cell(200, 10, txt="Daily Works Form", ln=True, align='C')
    pdf.ln(10)

    for key, value in data.items():
        if key != "Signature Path":
            pdf.multi_cell(0, 10, f"{key}: {value}")

    if signature_path and os.path.exists(signature_path):
        pdf.ln(10)
        pdf.image(signature_path, x=10, y=pdf.get_y(), w=60)
        pdf.ln(20)
        pdf.cell(0, 10, "Digital Signature", ln=True)

    filename = f"submitted_forms/Daily_Work_Form_{data['Date']}_{data['Project Name'].replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

def view_submitted_forms():
    st.markdown("### 📂 Submitted Daily Forms")
    files = os.listdir("submitted_forms")
    if not files:
        st.info("No forms submitted yet.")
        return
    for file in sorted(files, reverse=True):
        with open(f"submitted_forms/{file}", "rb") as f:
            st.download_button(label=f"⬇️ {file}", data=f, file_name=file, mime="application/pdf")

def daily_work_form():
    st.title("📝 Daily Work Form Submission")

    with st.form("daily_work_form"):
        st.markdown("### 🧾 Project Information")
        location = st.text_input("Location/Region")
        project = st.text_input("Project Name")
        contract_no = st.text_input("Contract No.")
        contractor = st.text_input("Contractor")
        date = st.date_input("Date", value=datetime.date.today())
        day = st.text_input("Day")
        sheet_no = st.text_input("Sheet No.")
        total_sheets = st.text_input("Total Sheets")
        time_from = st.time_input("Operation Start Time")
        time_to = st.time_input("Operation End Time")

        st.markdown("### 🌤️ Weather Conditions")
        weather = st.text_area("Weather Summary")

        st.markdown("### ⚙️ Plant and Equipment")
        equipment = st.text_area("List equipment with plate numbers and time deployed")

        st.markdown("### 🚛 Materials Delivered")
        materials = st.text_area("Describe materials delivered (description, units, truck no, etc.)")

        st.markdown("### 👷 Labour")
        labour = st.text_area("Personnel info (roles and number of personnel)")

        st.markdown("### 🛠️ Operations")
        operations = st.text_area("Chainage and activity descriptions")

        st.markdown("### ✍️ Signatures")
        inspector = st.text_input("Inspector Name")
        site_agent = st.text_input("Site Agent Name")
        engineer = st.text_input("R.E. / A.R.E Name")
        confirm = st.checkbox("I confirm the above information is correct")

        st.markdown("### ✒️ Draw Signature")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#fff",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas",
        )

        submitted = st.form_submit_button("Submit Form")

        if submitted and confirm:
            signature_path = None
            if canvas_result.image_data is not None:
                sig_img = BytesIO()
                img = PIL.Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                img.save(sig_img, format="PNG")
                sig_img.seek(0)
                signature_path = f"submitted_forms/signature_{project.replace(' ', '_')}_{date}.png"
                with open(signature_path, "wb") as f:
                    f.write(sig_img.read())

            data = {
                "Location/Region": location,
                "Project Name": project,
                "Contract No.": contract_no,
                "Contractor": contractor,
                "Date": str(date),
                "Day": day,
                "Sheet No.": sheet_no,
                "Total Sheets": total_sheets,
                "Time of Operation From": time_from.strftime("%H:%M"),
                "To": time_to.strftime("%H:%M"),
                "Weather Conditions": weather,
                "Plant and Equipment": equipment,
                "Materials Delivered": materials,
                "Labour": labour,
                "Operations": operations,
                "Inspector": inspector,
                "Site Agent": site_agent,
                "R.E. / A.R.E": engineer,
                "Signature Path": signature_path
            }
            file_path = generate_pdf(data, signature_path)
            st.session_state['submitted_form_path'] = file_path
            st.success("Form submitted and saved successfully!")

            try:
                send_email_with_attachment(
                    subject="New Daily Work Form Submission",
                    body=f"Daily Work Form submitted for project: {project} on {date}",
                    to_email=RECIPIENT_EMAIL,
                    file_path=file_path
                )
                st.success("📧 Email notification sent successfully.")
            except Exception as e:
                st.warning(f"Email failed: {e}")

    # ✅ Render download button AFTER the form
    if 'submitted_form_path' in st.session_state:
        with open(st.session_state['submitted_form_path'], "rb") as f:
            st.download_button(
                "📄 Download Submitted PDF",
                f,
                file_name=os.path.basename(st.session_state['submitted_form_path']),
                mime="application/pdf"
            )

    st.divider()
    view_submitted_forms()

# In your main app.py or menu system:
# import daily_form
# if menu_selection == "Daily Work Form":
#     daily_form.daily_work_form()
