# app.py

import streamlit as st
from daily_form import daily_work_form
from report_dashboard import report_dashboard

st.set_page_config(page_title="KURA Management System", layout="wide")

st.sidebar.title("📁 Main Menu")
menu = st.sidebar.radio("Navigate to:", ["📊 Reports", "📝 Daily Works"])

if menu == "📊 Reports":
    report_dashboard()
elif menu == "📝 Daily Works":
    daily_work_form()
