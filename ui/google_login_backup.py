import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from auth.google_auth import (
    get_google_auth_url,
    exchange_code_for_token,
    get_user_email_from_token,
    get_user_account,
    create_session,
    validate_session,
    logout
)

def get_current_session():
    """Check if there's a valid session in st.session_state."""
    session_id = st.session_state.get("session_id")
    if not session_id:
        return None
    session = validate_session(session_id)
    if not session:
        st.session_state.pop("session_id", None)
        return None
    return session

def show_login():
    """Show the Google login page."""
    st.title("🔐 HR Chatbot Login")
    st.markdown("Please log in with your Google account to continue.")

    params = st.query_params
    code = params.get("code")

    if code:
        with st.spinner("Verifying your Google account..."):
            try:
                token_data = exchange_code_for_token(code)
                if not token_data:
                    st.error("❌ Failed to get token from Google. Please try again.")
                    return

                email = get_user_email_from_token(token_data)
                if not email:
                    st.error("❌ Could not verify your Google account.")
                    return

                user = get_user_account(email)
                if not user:
                    st.error(f"❌ Your email ({email}) is not registered in the HR system. Contact your administrator.")
                    return

                session_id = create_session(
                    emp_no=user["emp_no"],
                    email=email,
                    role=user["role"]
                )
                if not session_id:
                    st.error("❌ Failed to create session. Please try again.")
                    return

                st.session_state["session_id"] = session_id
                st.session_state["emp_no"] = user["emp_no"]
                st.session_state["role"] = user["role"]
                st.session_state["email"] = email

                st.query_params.clear()
                st.rerun()

            except Exception as e:
                st.error(f"❌ Login failed: {str(e)}")
    else:
        auth_url = get_google_auth_url()
        st.markdown(f"""
            <a href="{auth_url}" target="_self">
                <button style="
                    background-color: #4285F4;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                ">
                    🔵 Login with Google
                </button>
            </a>
        """, unsafe_allow_html=True)

def show_dashboard(session):
    """Main HR dashboard — shown after login."""
    import requests

    API_URL = "http://127.0.0.1:8000"
    emp_no = session["emp_no"]
    role = session["role"]
    email = session["email"]
    is_manager = role == "manager"

    st.title("🏢 HR Dashboard")
    st.markdown(f"Logged in as **{email}** | {'👔 Manager' if is_manager else '👤 Employee'}")

    with st.sidebar:
        st.markdown(f"**Email:** {email}")
        st.markdown(f"**Emp No:** {emp_no}")
        st.markdown(f"**Role:** {role.capitalize()}")
        if st.button("🚪 Logout"):
            logout(st.session_state["session_id"])
            for key in ["session_id", "emp_no", "role", "email"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown("---")

    # ─────────────────────────────────────────────
    # MANAGER-ONLY SECTION
    # ─────────────────────────────────────────────
    if is_manager:
        st.subheader("📋 Manager Overview")

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
    # EMPLOYEE-ONLY SECTION
    # ─────────────────────────────────────────────
    else:
        st.subheader("👤 My Information")

        if st.button("💼 My Salary"):
            data = requests.get(f"{API_URL}/my-salary/{emp_no}").json()
            st.dataframe(data)

        if st.button("🏖️ My Leave Balance"):
            data = requests.get(f"{API_URL}/my-leave/{emp_no}").json()
            st.dataframe(data)

        if st.button("🏢 My Department"):
            data = requests.get(f"{API_URL}/my-department/{emp_no}").json()
            st.dataframe(data)

        if st.button("👔 My Manager"):
            try:
                response = requests.get(f"{API_URL}/manager/{emp_no}").json()
                if not response:
                    st.error("❌ No manager found.")
                else:
                    row = response[0]
                    st.success("✅ Manager found!")
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