# Enhanced app.py with merged sheet integration and detailed visual explanations

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

st.set_page_config(page_title="Monthly Report Dashboard", layout="wide")

st.title("📊 Monthly Departmental Report Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the Excel report", type=[".xlsx"])

if uploaded_file:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names

        st.markdown(f"### 🗂 Merging Sheets: {sheet_names}")

        # Read all sheets into a single dataframe with a column identifying the sheet name
        merged_data = []
        for sheet in sheet_names:
            try:
                df = pd.read_excel(uploaded_file, sheet_name=sheet)
                df["Department"] = sheet
                merged_data.append(df)
            except Exception as e:
                st.warning(f"⚠️ Could not read sheet '{sheet}': {e}")

        if merged_data:
            full_df = pd.concat(merged_data, ignore_index=True)

            st.markdown("### 📄 Merged Departmental Data")
            st.dataframe(full_df)

            # Visualization: Records Per Department
            if "Department" in full_df.columns:
                st.markdown("### 📈 Records Per Department")
                count_df = full_df["Department"].value_counts().reset_index()
                count_df.columns = ["Department", "Record Count"]
                chart = alt.Chart(count_df).mark_bar().encode(
                    x=alt.X("Department", sort="-y"),
                    y="Record Count",
                    tooltip=["Department", "Record Count"]
                ).properties(width=700, height=400)
                st.altair_chart(chart)

            # Visualization: Total Amounts by Description
            if "Amount" in full_df.columns and "Description" in full_df.columns:
                st.markdown("### 💵 Total Amounts by Description")
                amount_summary = full_df.groupby("Description")["Amount"].sum().reset_index()
                chart = alt.Chart(amount_summary).mark_bar().encode(
                    x=alt.X("Description", sort="-y"),
                    y="Amount",
                    tooltip=["Description", "Amount"]
                ).properties(width=700, height=400)
                st.altair_chart(chart)

        else:
            st.warning("No valid sheets could be merged from the uploaded file.")

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
else:
    st.warning("Please upload a valid Excel report to continue.")

