# Enhanced app.py with chart selection controls and formatting customization

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import io
from zipfile import ZipFile
from openpyxl import load_workbook

st.set_page_config(page_title="Monthly Report Dashboard", layout="wide")

st.title("📊 Monthly Departmental Report Dashboard")

uploaded_file = st.file_uploader("Upload the Excel report", type=[".xlsx"])

if uploaded_file:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names

        st.markdown("### 🗂 Select a Sheet to View")
        selected_sheet = st.selectbox("Choose a sheet", sheet_names)

        try:
            st.markdown(f"## 📄 {selected_sheet}")
            wb = load_workbook(uploaded_file, data_only=True)
            ws = wb[selected_sheet]
            visible_columns = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1)) if not ws.column_dimensions[cell.column_letter].hidden]
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, usecols=visible_columns)

            if 'Department' in df.columns:
                departments = df['Department'].dropna().unique().tolist()
                selected_dept = st.selectbox(f"Filter by Department in '{selected_sheet}'", departments)
                df = df[df['Department'] == selected_dept]

            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Table as CSV",
                data=csv,
                file_name=f"{selected_sheet}_filtered_data.csv",
                mime="text/csv"
            )

            numeric_columns = df.select_dtypes(include=['number']).columns
            label_column = None
            for col in ['Description', 'Name', 'Item', 'Team', 'Supplier', 'Contractor Name']:
                if col in df.columns:
                    label_column = col
                    break

            chart_types = st.multiselect(
                "Select chart types to display:",
                ["Bar Chart", "Pie Chart", "Line Chart"],
                default=["Bar Chart", "Pie Chart"]
            )

            chart_width = st.slider("Chart width", 400, 1000, 700)
            chart_height = st.slider("Chart height", 200, 600, 300)

            if not numeric_columns.empty:
                for col in numeric_columns:
                    chart_data = df[[label_column, col]].dropna() if label_column else df[[col]].dropna()
                    if not chart_data.empty:
                        if label_column:
                            x_axis = label_column
                            tooltip_vals = [label_column, col]
                        else:
                            chart_data = chart_data.reset_index()
                            x_axis = 'index'
                            tooltip_vals = [col]

                        if "Bar Chart" in chart_types:
                            st.markdown(f"#### 🔢 Bar Chart for: {col}")
                            bar_chart = alt.Chart(chart_data).mark_bar().encode(
                                x=alt.X(f"{x_axis}:O", sort="-y"),
                                y=alt.Y(f"{col}:Q"),
                                tooltip=tooltip_vals
                            ).properties(width=chart_width, height=chart_height)
                            st.altair_chart(bar_chart)

                        if "Pie Chart" in chart_types:
                            st.markdown(f"#### 🥧 Pie Chart for: {col}")
                            fig, ax = plt.subplots()
                            chart_data.groupby(x_axis)[col].sum().plot.pie(autopct='%1.1f%%', ax=ax)
                            ax.set_ylabel('')
                            ax.set_title(f"{col} Distribution")
                            st.pyplot(fig)

                        if "Line Chart" in chart_types:
                            st.markdown(f"#### 📈 Line Chart for: {col}")
                            line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
                                x=alt.X(f"{x_axis}:O"),
                                y=alt.Y(f"{col}:Q"),
                                tooltip=tooltip_vals
                            ).properties(width=chart_width, height=chart_height)
                            st.altair_chart(line_chart)

            else:
                st.info("ℹ️ No numeric columns found for visualization in this sheet.")

            if "finance" in selected_sheet.lower():
                st.success("This sheet contains finance-related data including payments and budgets.")
            elif "hr" in selected_sheet.lower():
                st.success("This sheet contains HR metrics like training and complaints.")
            elif "ict" in selected_sheet.lower():
                st.success("This sheet captures ICT infrastructure and support metrics.")

            with ZipFile("workbook_export.zip", "w") as zipf:
                for sheet in sheet_names:
                    ws = wb[sheet]
                    visible_columns = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1)) if not ws.column_dimensions[cell.column_letter].hidden]
                    df_sheet = pd.read_excel(uploaded_file, sheet_name=sheet, usecols=visible_columns)
                    csv_bytes = df_sheet.to_csv(index=False).encode("utf-8")
                    zipf.writestr(f"{sheet}.csv", csv_bytes)
            with open("workbook_export.zip", "rb") as f:
                st.download_button(
                    label="⬇️ Download Entire Workbook as ZIP of CSVs",
                    data=f.read(),
                    file_name="Workbook_Export.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.warning(f"⚠️ Could not process sheet '{selected_sheet}': {e}")

    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
else:
    st.warning("Please upload a valid Excel report to continue.")



