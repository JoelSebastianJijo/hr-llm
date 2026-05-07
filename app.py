import streamlit as st
import requests
import sys
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

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
                    sql = nl_to_sql(prompt, emp_no=TEMP_EMP_NO, is_manager=TEMP_IS_MANAGER)
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