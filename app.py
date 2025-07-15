# Sample enhanced app.py for monthly report dashboard with visual explanations

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monthly Report Dashboard", layout="wide")

st.title("📊 Monthly Departmental Report Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the Excel report", type=[".xlsx"])

if uploaded_file:
    excel_file = pd.ExcelFile(uploaded_file)

    # Example section: Finance & Accounts - Contractor Payments
    st.markdown("### 🏗 Contractor Payments")
    st.markdown("""
    This chart displays the amounts paid to each road works contractor during the reporting period.
    It helps assess which contractors received the largest disbursements and may inform future planning.
    """)
    contractor_df = pd.read_excel(excel_file, sheet_name="Finance", usecols="A:B")
    st.bar_chart(contractor_df.set_index("Contractor Name"))

    # Example section: Supply Chain - Purchases
    st.markdown("### 🛍️ Purchases Made")
    st.markdown("""
    This section outlines the major purchases made during the month, along with the amounts spent.
    It supports audit trails and transparent procurement.
    """)
    purchase_df = pd.read_excel(excel_file, sheet_name="Supply Chain", usecols="A:B")
    st.bar_chart(purchase_df.set_index("Description"))

    # Example section: HR - Staff Training
    st.markdown("### 🎓 Staff Trainings Conducted")
    st.markdown("""
    Lists staff members who underwent training, along with the title of each course.
    Supports professional development tracking.
    """)
    training_df = pd.read_excel(excel_file, sheet_name="HR", usecols="A:B")
    st.dataframe(training_df)

    # Example section: Transport - Fuel Levels
    st.markdown("### ⛽ Fuel Levels Monitoring")
    st.markdown("""
    Shows current fuel levels or consumption trends. Helps detect unusual usage or possible inefficiencies.
    """)
    fuel_df = pd.read_excel(excel_file, sheet_name="Transport", usecols="A:B")
    st.line_chart(fuel_df.set_index("Vehicle"))

    # Add more sections similarly as needed

else:
    st.warning("Please upload a valid Excel report to continue.")
