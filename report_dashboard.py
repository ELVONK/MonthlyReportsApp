# report_dashboard.py

import streamlit as st
import pandas as pd
import altair as alt
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from zipfile import ZipFile

def report_dashboard():
    st.title("📊 Monthly Report Dashboard")
    uploaded_file = st.file_uploader("Upload Monthly Excel Report", type=[".xlsx"])

    if uploaded_file:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            selected_sheet = st.selectbox("Select Sheet", sheet_names)

            wb = load_workbook(uploaded_file, data_only=True)
            ws = wb[selected_sheet]

            header_row = next(ws.iter_rows(min_row=1, max_row=1))
            visible_col_info = [
                (get_column_letter(cell.column), cell.value)
                for cell in header_row
                if cell.value is not None and not ws.column_dimensions[get_column_letter(cell.column)].hidden
            ]
            visible_letters = [col[0] for col in visible_col_info]
            visible_headers = [col[1] for col in visible_col_info]

            visible_data = []
            for row in ws.iter_rows(min_row=2):
                if not ws.row_dimensions[row[0].row].hidden:
                    row_data = [cell.value for cell in row if get_column_letter(cell.column) in visible_letters]
                    if any(cell is not None and cell != "" for cell in row_data):
                        visible_data.append(row_data)

            df = pd.DataFrame(visible_data, columns=visible_headers)

            # Clean Date Column
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
                df = df.dropna(subset=['Date'])

            if 'Department' in df.columns:
                departments = df['Department'].dropna().unique().tolist()
                selected_dept = st.selectbox("Filter by Department", departments)
                df = df[df['Department'] == selected_dept]

            st.dataframe(df, use_container_width=True)

            # Download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Filtered CSV", csv, f"{selected_sheet}_filtered.csv", "text/csv")

            # Charts
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()

            if numeric_cols and non_numeric_cols:
                x_col = st.selectbox("X-axis", non_numeric_cols)
                y_col = st.selectbox("Y-axis", numeric_cols)

                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(x_col, sort='-y'),
                    y=alt.Y(y_col),
                    color=x_col,
                    tooltip=[x_col, y_col]
                ).properties(width=700, height=400)

                st.altair_chart(chart)

        except Exception as e:
            st.error(f"Failed to process file: {e}")
