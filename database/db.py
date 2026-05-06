from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

load_dotenv()

def get_engine():
    password = quote_plus(os.getenv("DB_PASSWORD"))
    return create_engine(f"mysql+mysqlconnector://root:{password}@localhost/employees")

def run_query(query, params=None):
    engine = get_engine()
    with engine.connect() as conn:
        if params:
            # Convert tuple to dict for SQLAlchemy: (5,) → {"param_0": 5}
            param_dict = {f"param_{i}": v for i, v in enumerate(params)}
            query = query.replace("%s", f":param_0")
            df = pd.read_sql(text(query), conn, params=param_dict)
        else:
            df = pd.read_sql(text(query), conn)
    return df
   