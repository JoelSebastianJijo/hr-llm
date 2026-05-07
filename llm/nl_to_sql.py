import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCHEMA_DESCRIPTION = """
You are an expert SQL assistant. The database is MySQL and contains these tables:

- employees(emp_no, birth_date, first_name, last_name, gender, hire_date)
- departments(dept_no, dept_name)
- dept_emp(emp_no, dept_no, from_date, to_date) — links employees to departments. to_date='9999-01-01' means currently active.
- dept_manager(emp_no, dept_no, from_date, to_date) — links managers to departments. to_date='9999-01-01' means currently active.
- salaries(emp_no, salary, from_date, to_date) — to_date='9999-01-01' means current salary.
- titles(emp_no, title, from_date, to_date) — to_date='9999-01-01' means current title.
- leave_requests(leave_id, emp_no, leave_type, start_date, end_date, status)

Rules:
- Always use to_date='9999-01-01' to filter current records in dept_emp, dept_manager, salaries, titles.
- Use parameterised queries with %s for any user inputs.
- Return only the SQL query, nothing else. No explanation, no markdown, no backticks.
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