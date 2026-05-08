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
- ALWAYS filter current records using to_date = '9999-01-01' in dept_emp, dept_manager, salaries, titles. This is mandatory for every query involving these tables, no exceptions.
- For personal salary queries, ALWAYS use: WHERE s.emp_no = <emp_no> AND s.to_date = '9999-01-01' LIMIT 1
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

Q: What is my salary?
SQL: SELECT s.salary FROM salaries s WHERE s.emp_no = <emp_no> AND s.to_date = '9999-01-01' LIMIT 1;

Q: Who are the top 10 highest paid employees?
SQL: SELECT e.first_name, e.last_name, s.salary FROM employees e JOIN salaries s ON e.emp_no = s.emp_no WHERE s.to_date = '9999-01-01' ORDER BY s.salary DESC LIMIT 10;
"""

def nl_to_sql(question: str, emp_no: int, is_manager: bool = False) -> str:
    try:
        if is_manager:
            role_instruction = (
                f"The user is a MANAGER with emp_no {emp_no}.\n\n"
                "They have TWO types of access:\n\n"
                "1. PERSONAL queries (about themselves e.g. my salary, my leave, my title, my department):\n"
                f"   - Restrict using: WHERE emp_no = {emp_no} AND to_date = '9999-01-01' LIMIT 1\n\n"
                "2. ORGANIZATIONAL queries (about employees, rankings, departments, headcount, averages):\n"
                "   - Do NOT restrict by emp_no at all.\n"
                "   - Query freely across ALL employees in the database.\n"
                "   - Examples: top 5 highest paid, how many employees, average salary by department\n\n"
                "If the question contains words like my, me, or I, treat it as a PERSONAL query.\n"
                "Otherwise, treat it as an ORGANIZATIONAL query and do NOT add any emp_no restriction."
            )
        else:
            role_instruction = (
                f"The user is an EMPLOYEE with emp_no {emp_no}.\n"
                "They can ONLY query their own personal data.\n"
                f"Always add this restriction: WHERE emp_no = {emp_no} AND to_date = '9999-01-01'\n"
                "Never return data belonging to any other employee."
            )

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
