import streamlit as st
import requests
import sys
import os

sys.path.append(os.path.dirname(__file__))
from llm.nl_to_sql import nl_to_sql
from database.db import run_query

API_URL = "http://127.0.0.1:8000"

# Temporary hardcoded user until auth is ready
TEMP_EMP_NO = 110039
TEMP_IS_MANAGER = True

st.set_page_config(page_title="HR Chatbot", page_icon="🤖")
st.title("🤖 HR AI Chatbot")
st.markdown("Ask any question about the HR data in plain English.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "dataframe" in message:
            st.dataframe(message["dataframe"])
        if "sql" in message:
            with st.expander("Generated SQL"):
                st.code(message["sql"], language="sql")

# Chat input
if prompt := st.chat_input("Ask a question about HR data..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Generate SQL
                sql = nl_to_sql(prompt, emp_no=TEMP_EMP_NO, is_manager=TEMP_IS_MANAGER)

                # Run query
                df = run_query(sql)

                if df.empty:
                    st.markdown("No results found for your question.")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "No results found for your question.",
                        "sql": sql
                    })
                else:
                    st.markdown(f"Here are the results:")
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