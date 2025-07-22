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

# (The rest of the code remains unchanged from previous version...)

# You can re-use the existing form code and PDF generation logic without edits.
