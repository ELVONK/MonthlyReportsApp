
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from zipfile import ZipFile
import io

st.set_page_config(page_title="Monthly Report App", layout="wide")
st.title("📊 Monthly Departmental Report Dashboard")

uploaded_file = st.file_uploader("Upload your Excel report", type=["xlsx"])

if uploaded_file:
    output_dir = "output_reports"
    os.makedirs(output_dir, exist_ok=True)

    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    selected_sheet = st.selectbox("Select Department Sheet", sheet_names)
    df = excel_file.parse(selected_sheet)
    st.subheader(f"Data Preview - {selected_sheet}")
    st.dataframe(df.head())

    zip_buffer = io.BytesIO()

    def save_fig(fig, filename):
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath)
        plt.close(fig)
        return filepath

    file_paths = []

    if selected_sheet == "Finance and Accounts Department":
        contractors = df[["Contractor Name", "Amount Paid"]].dropna()
        if not contractors.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(contractors['Contractor Name'], contractors['Amount Paid'])
            ax.set_xlabel("Amount Paid (KES)")
            ax.set_title("Contractor Payments")
            st.pyplot(fig)
            file_paths.append(save_fig(fig, "contractor_payments.png"))

        suppliers = df[["Supplier Name", "Amount Paid.1"]].dropna()
        if not suppliers.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.bar(suppliers['Supplier Name'], suppliers['Amount Paid.1'])
            ax2.set_ylabel("Amount Paid (KES)")
            ax2.set_title("Supplier Payments")
            st.pyplot(fig2)
            file_paths.append(save_fig(fig2, "supplier_payments.png"))

    elif selected_sheet == "Supply Chain Department":
        desc_df = df[['Description', 'Amount']].dropna()
        if not desc_df.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(desc_df['Description'], desc_df['Amount'])
            ax.set_title("Purchase Amounts by Description")
            st.pyplot(fig)
            file_paths.append(save_fig(fig, "procurement_description.png"))

    elif selected_sheet == "ICT Department":
        downtime = df[['System Downtime (hours)', 'Equipment Name Serviced']].dropna()
        if not downtime.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.barh(downtime['Equipment Name Serviced'], downtime['System Downtime (hours)'])
            ax.set_xlabel("Downtime (hours)")
            ax.set_title("System Downtime by Equipment")
            st.pyplot(fig)
            file_paths.append(save_fig(fig, "system_downtime.png"))

    elif selected_sheet == "Transport Department":
        fuel = df[['Vehicle.1', 'Fuel Level (%)']].dropna()
        if not fuel.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(fuel['Vehicle.1'], fuel['Fuel Level (%)'])
            ax.set_ylabel("Fuel Level (%)")
            ax.set_title("Vehicle Fuel Levels")
            st.pyplot(fig)
            file_paths.append(save_fig(fig, "fuel_levels.png"))

    elif selected_sheet == "Survey Department":
        survey = df[['Topographical Survey', 'Status.1']].dropna()
        if not survey.empty:
            st.subheader("Topographical Survey Status")
            st.dataframe(survey)
            csv_path = os.path.join(output_dir, "survey_status.csv")
            survey.to_csv(csv_path, index=False)
            file_paths.append(csv_path)

    elif selected_sheet == "Human Resources Department":
        trainings = df[['Staff Name', 'Training Title']].dropna()
        if not trainings.empty:
            st.subheader("Staff Trainings")
            st.dataframe(trainings)
            csv_path = os.path.join(output_dir, "staff_trainings.csv")
            trainings.to_csv(csv_path, index=False)
            file_paths.append(csv_path)

    elif selected_sheet == "Road Asset and Corridor Managem":
        progress = df[['Contractor', 'Road Works Progress (%)']].dropna()
        if not progress.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(progress['Contractor'], progress['Road Works Progress (%)'])
            ax.set_title("Progress by Contractor")
            ax.set_ylabel("Progress (%)")
            st.pyplot(fig)
            file_paths.append(save_fig(fig, "roadworks_progress.png"))

    else:
        csv_path = os.path.join(output_dir, "sheet_preview.csv")
        df.to_csv(csv_path, index=False)
        file_paths.append(csv_path)

    # Create zip
    with ZipFile(zip_buffer, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))

    st.success("✅ Report generation complete!")
    st.download_button("📥 Download Report ZIP", data=zip_buffer.getvalue(), file_name="department_report_output.zip")
