import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCHEMA_DESCRIPTION = SCHEMA_DESCRIPTION = """
You are an expert MySQL SQL assistant. Convert natural language questions to SQL queries.

DATABASE SCHEMA:
- employees(emp_no, birth_date, first_name, last_name, gender, hire_date)
- departments(dept_no, dept_name)
- dept_emp(emp_no, dept_no, from_date, to_date) — links employees to departments
- dept_manager(emp_no, dept_no, from_date, to_date) — links managers to departments
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

EXAMPLES:
Q: How many male and female employees are there?
SQL: SELECT gender, COUNT(*) AS total FROM employees GROUP BY gender;
Note: the employees table has no to_date column. Never filter employees by to_date.
Q: What are the top 5 departments by headcount?
SQL: SELECT d.dept_name, COUNT(de.emp_no) AS headcount FROM departments d JOIN dept_emp de ON d.dept_no = de.dept_no WHERE de.to_date = '9999-01-01' GROUP BY d.dept_name ORDER BY headcount DESC LIMIT 5;

Q: What is the average salary by department?
SQL: SELECT d.dept_name, ROUND(AVG(s.salary), 2) AS avg_salary FROM departments d JOIN dept_emp de ON d.dept_no = de.dept_no JOIN salaries s ON de.emp_no = s.emp_no WHERE de.to_date = '9999-01-01' AND s.to_date = '9999-01-01' GROUP BY d.dept_name ORDER BY avg_salary DESC;

Q: Which employees are currently on sick leave?
SQL: SELECT e.first_name, e.last_name, lr.start_date, lr.end_date FROM employees e JOIN leave_requests lr ON e.emp_no = lr.emp_no WHERE lr.leave_type = 'Sick' AND lr.status = 'Approved' AND CURDATE() BETWEEN lr.start_date AND lr.end_date;

Q: Who are the top 10 highest paid employees?
SQL: SELECT e.first_name, e.last_name, s.salary FROM employees e JOIN salaries s ON e.emp_no = s.emp_no WHERE s.to_date = '9999-01-01' ORDER BY s.salary DESC LIMIT 10;
"""

def nl_to_sql(question: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SCHEMA_DESCRIPTION},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    questions = [
        "What are the top 5 departments by headcount?",
        "What is the average salary by department?",
        "How many male and female employees are there?",
        "Who are the top 10 highest paid employees?",
        "Which employees are currently on sick leave?"
    ]

    for q in questions:
        print(f"\nQuestion: {q}")
        print(f"SQL: {nl_to_sql(q)}")