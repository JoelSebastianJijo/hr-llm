import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
from db import run_query

def top_departments_by_headcount(limit=5):
    query = """
        SELECT d.dept_name, COUNT(de.emp_no) AS headcount
        FROM departments d
        JOIN dept_emp de ON d.dept_no = de.dept_no
        WHERE de.to_date = '9999-01-01'
        GROUP BY d.dept_name
        ORDER BY headcount DESC
        LIMIT :limit
    """
    return run_query(query, params={"limit": limit})

def average_salary_by_department():
    query = """
        SELECT d.dept_name, ROUND(AVG(s.salary), 2) AS avg_salary
        FROM departments d
        JOIN dept_emp de ON d.dept_no = de.dept_no
        JOIN salaries s ON de.emp_no = s.emp_no
        WHERE de.to_date = '9999-01-01' AND s.to_date = '9999-01-01'
        GROUP BY d.dept_name
        ORDER BY avg_salary DESC
    """
    return run_query(query)

def employees_on_leave():
    query = """
        SELECT e.emp_no, e.first_name, e.last_name,
               el.leave_type, el.start_date, el.end_date
        FROM employees e
        JOIN leave_requests el ON e.emp_no = el.emp_no
        WHERE CURDATE() BETWEEN el.start_date AND el.end_date
        LIMIT 10
    """
    return run_query(query)

def gender_distribution():
    query = """
        SELECT gender, COUNT(*) AS total
        FROM employees
        GROUP BY gender
    """
    return run_query(query)

def top_earners(limit=10):
    query = """
        SELECT e.emp_no, e.first_name, e.last_name, s.salary
        FROM employees e
        JOIN salaries s ON e.emp_no = s.emp_no
        WHERE s.to_date = '9999-01-01'
        ORDER BY s.salary DESC
        LIMIT :limit
    """
    return run_query(query, params={"limit": limit})

def get_manager_by_emp(emp_no):
    query = """
        SELECT e.first_name, e.last_name, d.dept_name,
               m.first_name AS manager_first, m.last_name AS manager_last
        FROM employees e
        JOIN dept_emp de ON e.emp_no = de.emp_no
        JOIN dept_manager dm ON de.dept_no = dm.dept_no
        JOIN employees m ON dm.emp_no = m.emp_no
        JOIN departments d ON de.dept_no = d.dept_no
        WHERE e.emp_no = :emp_no
        AND de.to_date = '9999-01-01'
        AND dm.to_date = '9999-01-01'
    """
    return run_query(query, params={"emp_no": emp_no})