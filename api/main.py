from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys, os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from queries.hr_queries import (
    top_departments_by_headcount,
    average_salary_by_department,
    employees_on_leave,
    gender_distribution,
    top_earners,
    get_manager_by_emp
)

logging.basicConfig(
    filename="hr_chatbot.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
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
    try:
        df = top_departments_by_headcount(limit)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"GET /top-departments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top departments")

@app.get("/avg-salary")
def get_avg_salary():
    try:
        df = average_salary_by_department()
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"GET /avg-salary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch average salary data")

@app.get("/employees-on-leave")
def get_employees_on_leave():
    try:
        df = employees_on_leave()
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"GET /employees-on-leave error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch employees on leave")

@app.get("/gender-distribution")
def get_gender_distribution():
    try:
        df = gender_distribution()
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"GET /gender-distribution error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch gender distribution")

@app.get("/top-earners")
def get_top_earners(limit: int = 10):
    try:
        df = top_earners(limit)
        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"GET /top-earners error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top earners")

@app.get("/manager/{emp_no}")
def get_manager(emp_no: int):
    try:
        df = get_manager_by_emp(emp_no)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No manager found for employee {emp_no}")
        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"GET /manager/{emp_no} error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch manager information")