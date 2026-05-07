import streamlit as st
import sys
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(__file__))
from auth.auth import login, validate_session, logout
from llm.nl_to_sql import nl_to_sql
from database.db import run_query

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
    is_manager = session["is_manager"]

    st.set_page_config(page_title="HR Chatbot", page_icon="🤖")
    st.title("🤖 HR AI Chatbot")
    st.markdown(f"Logged in as **Employee #{emp_no}** | {'👔 Manager' if is_manager else '👤 Employee'}")

    with st.sidebar:
        st.markdown(f"**Emp No:** {emp_no}")
        st.markdown(f"**Role:** {'Manager' if is_manager else 'Employee'}")
        if st.button("🚪 Logout"):
            logout(st.session_state["session_token"])
            st.session_state.pop("session_token", None)
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