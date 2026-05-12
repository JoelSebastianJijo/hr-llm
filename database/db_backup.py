import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os
import logging

load_dotenv()

logging.basicConfig(
    filename="hr_chatbot.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@st.cache_resource
def get_engine():
    try:
        password = quote_plus(os.getenv("DB_PASSWORD"))
        engine = create_engine(f"mysql+mysqlconnector://root:{password}@localhost/employees")
        return engine
    except Exception as e:
        logging.error(f"Failed to create database engine: {e}")
        raise

def run_query(query, params=None):
    """
    Execute a SQL query and return results as a DataFrame.
    params must be a dict, e.g. {"emp_no": 10001} matching :emp_no in the query.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            if params:
                df = pd.read_sql(text(query), conn, params=params)
            else:
                df = pd.read_sql(text(query), conn)
        return df
    except Exception as e:
        logging.error(f"run_query error | query={query} | params={params} | error={e}")
        raise