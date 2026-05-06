from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from queries.hr_queries import (
    top_departments_by_headcount,
    average_salary_by_department,
    employees_on_leave,
    gender_distribution,
    top_earners,
    get_manager_by_emp
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/top-departments")
def get_top_departments(limit: int = 5):
    df = top_departments_by_headcount(limit)
    return df.to_dict(orient="records")

@app.get("/avg-salary")
def get_avg_salary():
    df = average_salary_by_department()
    return df.to_dict(orient="records")

@app.get("/employees-on-leave")
def get_employees_on_leave():
    df = employees_on_leave()
    return df.to_dict(orient="records")

@app.get("/gender-distribution")
def get_gender_distribution():
    df = gender_distribution()
    return df.to_dict(orient="records")

@app.get("/top-earners")
def get_top_earners(limit: int = 10):
    df = top_earners(limit)
    return df.to_dict(orient="records")

@app.get("/manager/{emp_no}")
def get_manager(emp_no: int):
    df = get_manager_by_emp(emp_no)
    return df.to_dict(orient="records")