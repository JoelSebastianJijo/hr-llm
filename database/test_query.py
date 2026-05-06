from db import run_query

# Parameterised query - top N departments by headcount
query = """
    SELECT d.dept_name, COUNT(de.emp_no) AS headcount
    FROM departments d
    JOIN dept_emp de ON d.dept_no = de.dept_no
    WHERE de.to_date = '9999-01-01'
    GROUP BY d.dept_name
    ORDER BY headcount DESC
    LIMIT %s
"""

df = run_query(query, params=(5,))
print(df)