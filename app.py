import streamlit as st
from report_dashboard import report_dashboard
from daily_form import daily_work_form

st.set_page_config(page_title="KURA Reporting System", layout="wide")

menu = st.sidebar.selectbox("Navigation", ["Reports", "Daily Works"])

if menu == "Reports":
    report_dashboard()
elif menu == "Daily Works":
    daily_work_form()

