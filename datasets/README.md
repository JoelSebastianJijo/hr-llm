# Dataset Evaluation

## Candidates Evaluated

### 1. ClassicModels (MySQL Sample Database)
- **Coverage:** Has an employees table but represents sales staff, not HR data. Missing salary, leave, and proper department-manager relationships.
- **Licence:** Free, open sample database
- **Row count:** Small — ~23 employees, 8 offices
- **Data quality:** Clean but not suitable for HR use case
- **Verdict:** ❌ Rejected — not an HR dataset

### 2. IBM HR Analytics Employee Attrition Dataset (Kaggle)
- **Coverage:** Has employee info, job roles, salary, attrition. No leave data. Single flat table — not normalised.
- **Licence:** Free, CC0 public domain
- **Row count:** 1,470 rows
- **Data quality:** Clean but synthetic and small
- **Verdict:** ❌ Rejected — too small, not normalised, no leave data

### 3. MySQL Employees Database (datacharmer/test_db)
- **Coverage:** Full HR schema — employees, departments, salaries, titles, manager relationships
- **Licence:** Free, Creative Commons
- **Row count:** 300,024 employees, 2.8M salary records
- **Data quality:** Realistic, fully normalised, well documented
- **Verdict:** ✅ Selected — best coverage, largest dataset, already normalised