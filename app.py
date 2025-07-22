import streamlit as st
from daily_form import daily_work_form

st.set_page_config(page_title="KURA Reporting System", layout="wide")

menu = st.sidebar.selectbox("Navigation", ["Reports", "Daily Works"])

if menu == "Reports":
    st.title("📊 Monthly Report Dashboard")
    st.info("Report module coming soon...")
elif menu == "Daily Works":
    daily_work_form()
