import streamlit as st
import requests
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from auth.auth import login, validate_session, logout

API_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────────
# SESSION CHECK
# ─────────────────────────────────────────────
def get_current_session():
    token = st.session_state.get("session_token")
    if not token:
        return None
    session = validate_session(token)
    if not session:
        st.session_state.pop("session_token", None)
        return None
    return session

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
    st.title("🔐 HR System Login")
    st.markdown("Please log in to continue.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
            return
        token = login(username, password)
        if token is None:
            st.error("❌ Invalid username or password.")
        else:
            st.session_state["session_token"] = token
            st.success("✅ Logged in successfully!")
            st.rerun()

# ─────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────
def show_dashboard(session):
    emp_no = session["emp_no"]
    is_manager = session["is_manager"]

    st.title("🏢 HR Dashboard")
    st.markdown(f"Logged in as **Employee #{emp_no}** | {'👔 Manager' if is_manager else '👤 Employee'}")

    with st.sidebar:
        st.markdown(f"**Emp No:** {emp_no}")
        st.markdown(f"**Role:** {'Manager' if is_manager else 'Employee'}")
        if st.button("🚪 Logout"):
            logout(st.session_state["session_token"])
            st.session_state.pop("session_token", None)
            st.rerun()

    st.markdown("---")

    if st.button("📊 Top 5 Departments by Headcount"):
        data = requests.get(f"{API_URL}/top-departments").json()
        st.dataframe(data)

    if st.button("💰 Average Salary by Department"):
        data = requests.get(f"{API_URL}/avg-salary").json()
        st.dataframe(data)

    if st.button("🖐️ Employees Currently on Leave"):
        data = requests.get(f"{API_URL}/employees-on-leave").json()
        st.dataframe(data)

    if st.button("👥 Gender Distribution"):
        data = requests.get(f"{API_URL}/gender-distribution").json()
        st.dataframe(data)

    if st.button("🏆 Top 10 Earners"):
        data = requests.get(f"{API_URL}/top-earners").json()
        st.dataframe(data)

    st.markdown("---")
    st.subheader("🔍 Find Manager by Employee Number")

    emp_input = st.text_input("Enter Employee Number", placeholder="e.g. 10001")

    if st.button("Find Manager"):
        if not emp_input.strip():
            st.warning("Please enter an employee number.")
        else:
            try:
                response = requests.get(f"{API_URL}/manager/{emp_input.strip()}").json()
                if not response:
                    st.error("❌ No manager found for that employee number.")
                else:
                    row = response[0]
                    st.success("✅ Manager found!")
                    st.markdown(f"**Employee:** {row['first_name']} {row['last_name']}")
                    st.markdown(f"**Department:** {row['dept_name']}")
                    st.markdown(f"**Manager:** {row['manager_first']} {row['manager_last']}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
session = get_current_session()

if session is None:
    show_login()
else:
    show_dashboard(session)