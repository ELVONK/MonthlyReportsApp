# Enhanced app.py with full sheet integration and explanations

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monthly Report Dashboard", layout="wide")

st.title("📊 Monthly Departmental Report Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the Excel report", type=[".xlsx"])

if uploaded_file:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        # Display available sheet names
        sheet_names = excel_file.sheet_names
        st.markdown(f"### 🗂 Available Sheets: {sheet_names}")

        # Sheet selector
        selected_sheet = st.selectbox("Select a sheet to visualize:", sheet_names)

        if selected_sheet:
            try:
                if selected_sheet in sheet_names:
                    df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

                    st.markdown(f"### 📄 Preview of '{selected_sheet}' Sheet")
                    st.dataframe(df)

                    sheet_key = selected_sheet.lower()

                    if "finance" in sheet_key:
                        st.markdown("### 💰 Finance and Accounts Summary")
                        st.markdown("""
                        Overview of contractor payments, supplier disbursements, and imprest management.
                        """)
                        if "Contractor Name" in df.columns and "Amount Paid" in df.columns:
                            st.bar_chart(df.set_index("Contractor Name")["Amount Paid"])

                    elif "supply chain" in sheet_key:
                        st.markdown("### 📦 Supply Chain Activities")
                        st.markdown("""
                        This section outlines purchases made, procurement plan implementation, and store levels.
                        """)
                        if "Description" in df.columns and "Amount" in df.columns:
                            st.bar_chart(df.set_index("Description")["Amount"])

                    elif "ict" in sheet_key:
                        st.markdown("### 💻 ICT Department Report")
                        st.markdown("""
                        Displays system downtime instances, equipment maintenance logs, and portal usage.
                        """)
                        st.dataframe(df)

                    elif "transport" in sheet_key:
                        st.markdown("### 🚚 Transport Department Report")
                        st.markdown("""
                        Visualizes fuel level monitoring and vehicle maintenance records.
                        """)
                        if "Vehicle" in df.columns and "Fuel Level" in df.columns:
                            st.line_chart(df.set_index("Vehicle")["Fuel Level"])

                    elif "survey" in sheet_key:
                        st.markdown("### 🗺️ Survey Department Summary")
                        st.markdown("""
                        Displays corridor mappings, topographical surveys, and disputes resolved.
                        """)
                        st.dataframe(df)

                    elif "human resources" in sheet_key:
                        st.markdown("### 👥 Human Resources Activities")
                        st.markdown("""
                        Lists staff training, complaints received, visitors attended to, and leave summaries.
                        """)
                        st.dataframe(df)

                    elif "road asset" in sheet_key:
                        st.markdown("### 🛣️ Road Asset & Corridor Management")
                        st.markdown("""
                        Summary of road works progress and ARWP alignment for FY 2025/2026.
                        """)
                        st.dataframe(df)

                    else:
                        st.markdown("ℹ️ No specific visualization template for this sheet yet. Showing preview only.")
                else:
                    st.error(f"❌ Sheet '{selected_sheet}' not found in Excel file.")
            except ValueError as ve:
                st.error(f"❌ Sheet '{selected_sheet}' could not be loaded. Error: {ve}")
    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")

else:
    st.warning("Please upload a valid Excel report to continue.")
