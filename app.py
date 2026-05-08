import streamlit as st
import sys
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(__file__))
from auth.google_auth import (
    get_google_auth_url,
    exchange_code_for_token,
    get_user_email_from_token,
    get_user_account,
    create_session,
    validate_session,
    logout
)
from llm.nl_to_sql import nl_to_sql
from database.db import run_query

# ─────────────────────────────────────────────
# SESSION CHECK
# ─────────────────────────────────────────────
def get_current_session():
    session_id = st.session_state.get("session_id")
    if not session_id:
        return None
    session = validate_session(session_id)
    if not session:
        st.session_state.pop("session_id", None)
        return None
    return session

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
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
                ">
                    🔵 Login with Google
                </button>
            </a>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INTENT DETECTION
# ─────────────────────────────────────────────
def is_data_question(question: str) -> bool:
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a classifier. Respond with only 'yes' or 'no'. Does the following message require querying an HR database to answer? Be generous — if the message is asking about employees, salaries, departments, leave, or any HR topic, answer 'yes'."},
                {"role": "user", "content": question}
            ]
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"
    except Exception as e:
        return True

# ─────────────────────────────────────────────
# CHAT INTERFACE
# ─────────────────────────────────────────────
def show_chat(session):
    emp_no = session["emp_no"]
    role = session["role"]
    email = session["email"]
    is_manager = role == "manager"

    st.set_page_config(page_title="HR Chatbot", page_icon="🤖")
    st.title("🤖 HR AI Chatbot")
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

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "dataframe" in message:
                st.dataframe(message["dataframe"])
            if "sql" in message:
                with st.expander("Generated SQL"):
                    st.code(message["sql"], language="sql")

    if prompt := st.chat_input("Ask a question about HR data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if not is_data_question(prompt):
                        msg = "Hello! I'm your HR assistant. Ask me anything about employees, salaries, departments or leave data."
                        st.markdown(msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": msg
                        })
                    else:
                        sql = nl_to_sql(prompt, emp_no=emp_no, is_manager=is_manager)
                        df = run_query(sql)

                        if df.empty:
                            st.markdown("No results found for your question.")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "No results found for your question.",
                                "sql": sql
                            })
                        else:
                            st.markdown("Here are the results:")
                            st.dataframe(df)
                            with st.expander("Generated SQL"):
                                st.code(sql, language="sql")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "Here are the results:",
                                "dataframe": df,
                                "sql": sql
                            })

                except Exception as e:
                    error_msg = "Sorry, I couldn't process your question. Please try rephrasing it."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
session = get_current_session()

if session is None:
    show_login()
else:
    show_chat(session)