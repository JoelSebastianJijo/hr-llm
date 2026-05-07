import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename="hr_chatbot.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    logging.error(f"Failed to initialize Groq client: {e}")
    raise

SCHEMA_DESCRIPTION = """
You are an expert MySQL SQL assistant. Convert natural language questions to SQL queries.

DATABASE SCHEMA:
- employees(emp_no, birth_date, first_name, last_name, gender, hire_date)
- departments(dept_no, dept_name)
- dept_emp(emp_no, dept_no, from_date, to_date) - links employees to departments
- dept_manager(emp_no, dept_no, from_date, to_date) - links managers to departments
- salaries(emp_no, salary, from_date, to_date)
- titles(emp_no, title, from_date, to_date)
- leave_requests(leave_id, emp_no, leave_type, start_date, end_date, status)

IMPORTANT RULES:
- Always filter current records using to_date = '9999-01-01' in dept_emp, dept_manager, salaries, titles
- leave_type values are: 'Annual', 'Sick', 'Maternity', 'Paternity', 'Unpaid'
- status values are: 'Approved', 'Pending', 'Rejected'
- gender values are: 'M', 'F'
- Return ONLY the SQL query. No explanation, no markdown, no backticks.
- Never use DROP, DELETE, UPDATE or INSERT statements.
- The employees table has no to_date column. Never filter employees by to_date.
- Always enforce the access restriction provided for the user role.

EXAMPLES:
Q: How many male and female employees are there?
SQL: SELECT gender, COUNT(*) AS total FROM employees GROUP BY gender;

Q: What are the top 5 departments by headcount?
SQL: SELECT d.dept_name, COUNT(de.emp_no) AS headcount FROM departments d JOIN dept_emp de ON d.dept_no = de.dept_no WHERE de.to_date = '9999-01-01' GROUP BY d.dept_name ORDER BY headcount DESC LIMIT 5;

Q: What is the average salary by department?
SQL: SELECT d.dept_name, ROUND(AVG(s.salary), 2) AS avg_salary FROM departments d JOIN dept_emp de ON d.dept_no = de.dept_no JOIN salaries s ON de.emp_no = s.emp_no WHERE de.to_date = '9999-01-01' AND s.to_date = '9999-01-01' GROUP BY d.dept_name ORDER BY avg_salary DESC;

Q: Which employees are currently on sick leave?
SQL: SELECT e.first_name, e.last_name, lr.start_date, lr.end_date FROM employees e JOIN leave_requests lr ON e.emp_no = lr.emp_no WHERE lr.leave_type = 'Sick' AND lr.status = 'Approved' AND CURDATE() BETWEEN lr.start_date AND lr.end_date;

Q: Who are the top 10 highest paid employees?
SQL: SELECT e.first_name, e.last_name, s.salary FROM employees e JOIN salaries s ON e.emp_no = s.emp_no WHERE s.to_date = '9999-01-01' ORDER BY s.salary DESC LIMIT 10;
"""

def nl_to_sql(question: str, emp_no: int, is_manager: bool = False) -> str:
    """
    Converts a natural language question to SQL.
    Enforces role-based access:
    - Employees can only query their own data
    - Managers can query their own data and their staff's data
    """
    try:
        if is_manager:
            role_instruction = f"""The user is a MANAGER with emp_no {emp_no}.
They can query their own data and data of employees in their department.
Always restrict queries to their department using:
dept_no IN (SELECT dept_no FROM dept_manager WHERE emp_no = {emp_no} AND to_date = '9999-01-01')"""
        else:
            role_instruction = f"""The user is an EMPLOYEE with emp_no {emp_no}.
They can ONLY query their own personal data.
Always add this restriction: WHERE emp_no = {emp_no}
Never return data belonging to any other employee."""

        full_prompt = f"{SCHEMA_DESCRIPTION}\n\nACCESS RESTRICTION:\n{role_instruction}\n\nQuestion: {question}"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert MySQL query writer for an HR system. Always enforce the access restrictions given. Return only the SQL query with no explanation."},
                {"role": "user", "content": full_prompt}
            ]
        )

        sql = response.choices[0].message.content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    except Exception as e:
        logging.error(f"nl_to_sql error | emp_no={emp_no} | is_manager={is_manager} | question={question} | error={e}")
        return "Sorry, I could not process your request. Please try again or contact support."


if __name__ == "__main__":
    print("=== Testing as Employee (emp_no=10001) ===")
    print(nl_to_sql("What is my current salary?", emp_no=10001, is_manager=False))

    print("\n=== Testing as Manager (emp_no=110022) ===")
    print(nl_to_sql("How many employees are in my department?", emp_no=110022, is_manager=True))
