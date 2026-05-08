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
- The employees table has NO to_date column. Never filter employees by to_date. Use hire_date directly.
- The leave_requests table has NO to_date column. Never add to_date filter on leave_requests.
- "currently on leave" means CURDATE() BETWEEN leave_requests.start_date AND leave_requests.end_date. Never use to_date for this.
- leave_type values are: 'Annual', 'Sick', 'Maternity', 'Paternity', 'Unpaid'
- status values are: 'Approved', 'Pending', 'Rejected'
- gender values are: 'M', 'F'
- Return ONLY the SQL query. No explanation, no markdown, no backticks.
- Never use DROP, DELETE, UPDATE or INSERT statements.
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

Q: When was I hired? / What is my hire date? / When did I join?
SQL: SELECT hire_date FROM employees WHERE emp_no = <emp_no>;

Q: Show my leave requests / What are my leave requests? / List my time off
SQL: SELECT leave_type, start_date, end_date, status FROM leave_requests WHERE emp_no = <emp_no>;

Q: List my team / Who are my team members? / Who reports to me? / Show employees in my department
SQL: SELECT e.emp_no, e.first_name, e.last_name FROM employees e JOIN dept_emp de ON e.emp_no = de.emp_no WHERE de.dept_no = (SELECT dept_no FROM dept_manager WHERE emp_no = <emp_no> AND to_date = '9999-01-01') AND de.to_date = '9999-01-01' AND de.emp_no != <emp_no>;

Q: Which employees are currently on sick leave? / Who is on sick leave?
SQL: SELECT e.first_name, e.last_name, lr.start_date, lr.end_date FROM employees e JOIN leave_requests lr ON e.emp_no = lr.emp_no WHERE lr.leave_type = 'Sick' AND lr.status = 'Approved' AND CURDATE() BETWEEN lr.start_date AND lr.end_date;

Q: Who is currently on leave? / Find employees currently on leave? / Who is out today?
SQL: SELECT e.first_name, e.last_name, lr.leave_type, lr.start_date, lr.end_date FROM employees e JOIN leave_requests lr ON e.emp_no = lr.emp_no WHERE lr.status = 'Approved' AND CURDATE() BETWEEN lr.start_date AND lr.end_date;

Q: Show all pending leave requests / Which leave requests are pending?
SQL: SELECT e.first_name, e.last_name, lr.leave_type, lr.start_date, lr.end_date FROM employees e JOIN leave_requests lr ON e.emp_no = lr.emp_no WHERE lr.status = 'Pending';

Q: What is my current title / job title / role?
SQL: SELECT title FROM titles WHERE emp_no = <emp_no> AND to_date = '9999-01-01' LIMIT 1;

Q: What department am I in? / Which department do I belong to?
SQL: SELECT d.dept_name FROM departments d JOIN dept_emp de ON d.dept_no = de.dept_no WHERE de.emp_no = <emp_no> AND de.to_date = '9999-01-01';
"""

def nl_to_sql(question: str, emp_no: int, is_manager: bool = False) -> str:
    try:
        if is_manager:
            role_instruction = (
                f"The user is a MANAGER with emp_no {emp_no}.\n\n"
                "They have TWO types of access:\n\n"
                "1. PERSONAL queries (about themselves e.g. my salary, my leave, my title, my hire date, my department):\n"
                f"   - For salaries/titles/dept_emp: restrict using WHERE emp_no = {emp_no} AND to_date = '9999-01-01'\n"
                f"   - For employees table (hire_date, name, gender): restrict using WHERE emp_no = {emp_no} (NO to_date filter)\n"
                f"   - For leave_requests: restrict using WHERE emp_no = {emp_no} (NO to_date filter)\n\n"
                "2. ORGANIZATIONAL queries (about employees, rankings, departments, headcount, averages, leave across company):\n"
                "   - Do NOT restrict by emp_no at all.\n"
                "   - Query freely across ALL employees in the database.\n\n"
                "3. TEAM queries (list my team, who reports to me, my department members):\n"
                f"   - Find the manager's dept_no from dept_manager WHERE emp_no = {emp_no} AND to_date = '9999-01-01'\n"
                f"   - Then list all employees in that dept_no from dept_emp WHERE to_date = '9999-01-01' AND emp_no != {emp_no}\n\n"
                "If the question contains words like my, me, or I, treat it as PERSONAL or TEAM query.\n"
                "Otherwise, treat it as an ORGANIZATIONAL query and do NOT add any emp_no restriction."
            )
        else:
            role_instruction = (
                f"The user is an EMPLOYEE with emp_no {emp_no}.\n"
                "They can ONLY query their own personal data.\n\n"
                "Apply restrictions based on the table being queried:\n"
                f"- For salaries, titles, dept_emp, dept_manager: WHERE emp_no = {emp_no} AND to_date = '9999-01-01'\n"
                f"- For employees table (hire_date, name, gender, birth_date): WHERE emp_no = {emp_no} (NO to_date - employees has no to_date column)\n"
                f"- For leave_requests: WHERE emp_no = {emp_no} (NO to_date - leave_requests has no to_date column)\n"
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
