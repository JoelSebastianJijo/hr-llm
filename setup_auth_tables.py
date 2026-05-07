from database.db import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            emp_no INT NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            role ENUM('employee', 'manager') NOT NULL DEFAULT 'employee',
            FOREIGN KEY (emp_no) REFERENCES employees(emp_no)
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR(100) PRIMARY KEY,
            emp_no INT NOT NULL,
            email VARCHAR(100) NOT NULL,
            role ENUM('employee', 'manager') NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY (emp_no) REFERENCES employees(emp_no)
        )
    """))
    conn.commit()
    print("✅ Tables created successfully!")