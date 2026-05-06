import mysql.connector
import random
from faker import Faker
from dotenv import load_dotenv
import os

load_dotenv()

fake = Faker()

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database="employees"
)

cursor = conn.cursor()

# Create leave table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        leave_id INT AUTO_INCREMENT PRIMARY KEY,
        emp_no INT NOT NULL,
        leave_type VARCHAR(50) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) NOT NULL,
        FOREIGN KEY (emp_no) REFERENCES employees(emp_no)
    )
""")

# Get a sample of employee numbers
cursor.execute("SELECT emp_no FROM employees LIMIT 1000")
emp_nos = [row[0] for row in cursor.fetchall()]

# Generate fake leave records
leave_types = ['Annual', 'Sick', 'Maternity', 'Paternity', 'Unpaid']
statuses = ['Approved', 'Pending', 'Rejected']

records = []
for _ in range(5000):
    emp_no = random.choice(emp_nos)
    leave_type = random.choice(leave_types)
    start_date = fake.date_between(start_date='-2y', end_date='today')
    end_date = fake.date_between(start_date=start_date, end_date='+30d')
    status = random.choice(statuses)
    records.append((emp_no, leave_type, start_date, end_date, status))

cursor.executemany("""
    INSERT INTO leave_requests (emp_no, leave_type, start_date, end_date, status)
    VALUES (%s, %s, %s, %s, %s)
""", records)

conn.commit()
print(f"Inserted {cursor.rowcount} leave records successfully")

cursor.close()
conn.close()