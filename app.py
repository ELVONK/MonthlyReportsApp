# Enhanced app.py with proper chart formatting and readable tooltips

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
            visible_columns = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1)) if cell.value is not None and not ws.column_dimensions[cell.column_letter].hidden]
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

            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            label_column = st.selectbox("Select label column (x-axis / category):", [None] + df.columns.tolist())
            value_column = st.selectbox("Select numeric column (y-axis / value):", numeric_columns)

            selected_rows = []
            if label_column:
                unique_labels = df[label_column].dropna().unique().tolist()
                selected_rows = st.multiselect("Select rows to include in the chart (based on label):", unique_labels, default=unique_labels)
                chart_data = df[df[label_column].isin(selected_rows)]
            else:
                chart_data = df[[value_column]].dropna().reset_index()
                chart_data.rename(columns={'index': 'index_label'}, inplace=True)
                chart_data['index_label'] = chart_data['index_label'].astype(str)
                label_column = 'index_label'
                chart_data[label_column] = chart_data[label_column]

            def format_currency(val):
                if abs(val) >= 1_000_000:
                    return f"KES {val/1_000_000:.2f}M"
                elif abs(val) >= 1_000:
                    return f"KES {val/1_000:.2f}K"
                return f"KES {val:.2f}"

            st.markdown("### 📊 Selected Data Preview")
            formatted_data = chart_data[[label_column, value_column]].copy()
            formatted_data[value_column] = formatted_data[value_column].apply(format_currency)
            st.dataframe(formatted_data)

            chart_types = st.multiselect(
                "Select chart types to display:",
                ["Bar Chart", "Pie Chart", "Line Chart"],
                default=["Bar Chart"]
            )

            chart_width = st.slider("Chart width", 400, 1000, 700)
            chart_height = st.slider("Chart height", 200, 600, 300)

            if not chart_data.empty:
                tooltip_vals = [label_column, alt.Tooltip(f"{value_column}:Q", title="Value (KES)", format=".2s")]

                if "Bar Chart" in chart_types:
                    st.markdown(f"#### 🔢 Bar Chart for: {value_column}")
                    bar_chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X(f"{label_column}:O", sort="-y"),
                        y=alt.Y(f"{value_column}:Q", axis=alt.Axis(format="~s")),
                        tooltip=tooltip_vals
                    ).properties(width=chart_width, height=chart_height)
                    st.altair_chart(bar_chart)

                if "Pie Chart" in chart_types:
                    st.markdown(f"#### 🥧 Pie Chart for: {value_column}")
                    fig, ax = plt.subplots()
                    pie_series = chart_data.set_index(label_column)[value_column]
                    pie_series.plot.pie(autopct='%1.1f%%', ax=ax, startangle=90)
                    ax.set_ylabel('')
                    ax.set_title(f"{value_column} Distribution")
                    st.pyplot(fig)

                if "Line Chart" in chart_types:
                    st.markdown(f"#### 📈 Line Chart for: {value_column}")
                    line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
                        x=alt.X(f"{label_column}:O"),
                        y=alt.Y(f"{value_column}:Q", axis=alt.Axis(format="~s")),
                        tooltip=tooltip_vals
                    ).properties(width=chart_width, height=chart_height)
                    st.altair_chart(line_chart)
            else:
                st.info("ℹ️ No data selected for chart generation.")

            if "finance" in selected_sheet.lower():
                st.success("This sheet contains finance-related data including payments and budgets.")
            elif "hr" in selected_sheet.lower():
                st.success("This sheet contains HR metrics like training and complaints.")
            elif "ict" in selected_sheet.lower():
                st.success("This sheet captures ICT infrastructure and support metrics.")

            with ZipFile("workbook_export.zip", "w") as zipf:
                for sheet in sheet_names:
                    ws = wb[sheet]
                    visible_columns = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1)) if cell.value is not None and not ws.column_dimensions[cell.column_letter].hidden]
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

