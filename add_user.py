from database.db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO user_accounts (emp_no, email, role) 
        VALUES (10001, 'shezaraziya01@gmail.com', 'employee')
    """))
    conn.commit()
print("✅ User added!")