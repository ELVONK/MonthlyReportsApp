# Enhanced app.py with individual sheet visualizations, filtering, pie charts, and department-specific templates

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

        st.markdown(f"### 🗂 Sheets Found: {sheet_names}")

        for sheet in sheet_names:
            try:
                st.markdown(f"## 📄 {sheet}")
                df = pd.read_excel(uploaded_file, sheet_name=sheet)

                # Filtering for specific columns if present
                if 'Department' in df.columns:
                    departments = df['Department'].dropna().unique().tolist()
                    selected_dept = st.selectbox(f"Filter by Department in '{sheet}'", departments)
                    df = df[df['Department'] == selected_dept]

                st.dataframe(df)

                numeric_columns = df.select_dtypes(include=['number']).columns

                if not numeric_columns.empty:
                    for col in numeric_columns:
                        chart_data = df[[col]].dropna()
                        if not chart_data.empty:
                            st.markdown(f"#### 🔢 Bar Chart for: {col}")
                            chart = alt.Chart(chart_data.reset_index()).mark_bar().encode(
                                x=alt.X("index:O", title="Record Index"),
                                y=alt.Y(f"{col}:Q", title=col),
                                tooltip=[f"{col}:Q"]
                            ).properties(width=700, height=300)
                            st.altair_chart(chart)

                            st.markdown(f"#### 🥧 Pie Chart for: {col}")
                            fig, ax = plt.subplots()
                            chart_data[col].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
                            ax.set_ylabel('')
                            ax.set_title(col)
                            st.pyplot(fig)
                else:
                    st.info("ℹ️ No numeric columns found for visualization in this sheet.")

                # Example: custom message for known department sheets
                if "finance" in sheet.lower():
                    st.success("This sheet contains finance-related data including payments and budgets.")
                elif "hr" in sheet.lower():
                    st.success("This sheet contains HR metrics like training and complaints.")
                elif "ict" in sheet.lower():
                    st.success("This sheet captures ICT infrastructure and support metrics.")

            except Exception as e:
                st.warning(f"⚠️ Could not process sheet '{sheet}': {e}")

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
else:
    st.warning("Please upload a valid Excel report to continue.")

