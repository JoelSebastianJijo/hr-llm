import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("🏢 HR Dashboard")
st.markdown("Click a button to query the HR database through the API.")

if st.button("📊 Top 5 Departments by Headcount"):
    data = requests.get(f"{API_URL}/top-departments").json()
    st.dataframe(data)

if st.button("💰 Average Salary by Department"):
    data = requests.get(f"{API_URL}/avg-salary").json()
    st.dataframe(data)

if st.button("🏖️ Employees Currently on Leave"):
    data = requests.get(f"{API_URL}/employees-on-leave").json()
    st.dataframe(data)

if st.button("👥 Gender Distribution"):
    data = requests.get(f"{API_URL}/gender-distribution").json()
    st.dataframe(data)

if st.button("🏆 Top 10 Earners"):
    data = requests.get(f"{API_URL}/top-earners").json()
    st.dataframe(data)
