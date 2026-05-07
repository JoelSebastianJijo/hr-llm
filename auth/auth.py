import bcrypt
import os
import secrets
from datetime import datetime, timedelta
from sqlalchemy import text
from database.db import get_engine

def create_tables():
    """Create users and sessions tables if they don't exist."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       INT PRIMARY KEY AUTO_INCREMENT,
                username      VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                emp_no        INT UNIQUE,
                is_manager    BOOLEAN DEFAULT FALSE,
                created_at    DATETIME DEFAULT NOW(),
                FOREIGN KEY (emp_no) REFERENCES employees(emp_no)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_token VARCHAR(255) PRIMARY KEY,
                emp_no        INT NOT NULL,
                is_manager    BOOLEAN DEFAULT FALSE,
                created_at    DATETIME DEFAULT NOW(),
                expires_at    DATETIME NOT NULL,
                FOREIGN KEY (emp_no) REFERENCES employees(emp_no)
            )
        """))
        conn.commit()
    print("✅ Tables created successfully.")

def register_user(username: str, password: str, emp_no: int, is_manager: bool = False):
    """
    Register a new user.
    - Hashes password with bcrypt before storing
    - Never stores plain text password
    """
    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    engine = get_engine()
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                INSERT INTO users (username, password_hash, emp_no, is_manager)
                VALUES (:username, :password_hash, :emp_no, :is_manager)
            """), {
                "username": username,
                "password_hash": password_hash,
                "emp_no": emp_no,
                "is_manager": is_manager
            })
            conn.commit()
            print(f"✅ User '{username}' registered successfully.")
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            raise

def login(username: str, password: str):
    """
    Verify credentials and create a session.
    Returns session_token if successful, None if failed.
    """
    engine = get_engine()
    with engine.connect() as conn:
        # Step 1: Find the user
        result = conn.execute(text("""
            SELECT user_id, password_hash, emp_no, is_manager
            FROM users WHERE username = :username
        """), {"username": username})
        user = result.fetchone()

        if user is None:
            return None  # User doesn't exist

        # Step 2: Verify password against stored hash
        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            user.password_hash.encode("utf-8")
        )

        if not password_matches:
            return None  # Wrong password

        # Step 3: Create a session token
        # secrets.token_hex generates a cryptographically secure random token
        session_token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=8)  # Session lasts 8 hours

        conn.execute(text("""
            INSERT INTO sessions (session_token, emp_no, is_manager, expires_at)
            VALUES (:token, :emp_no, :is_manager, :expires_at)
        """), {
            "token": session_token,
            "emp_no": user.emp_no,
            "is_manager": user.is_manager,
            "expires_at": expires_at
        })
        conn.commit()
        return session_token

def validate_session(session_token: str):
    """
    Check if a session token is valid and not expired.
    Returns (emp_no, is_manager) if valid, None if invalid/expired.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT emp_no, is_manager FROM sessions
            WHERE session_token = :token
            AND expires_at > NOW()
        """), {"token": session_token})
        session = result.fetchone()

        if session is None:
            return None  # Expired or doesn't exist

        return {"emp_no": session.emp_no, "is_manager": session.is_manager}

def logout(session_token: str):
    """Delete the session from DB — clean logout."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            DELETE FROM sessions WHERE session_token = :token
        """), {"token": session_token})
        conn.commit()