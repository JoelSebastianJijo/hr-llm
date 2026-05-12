# STRIDE Threat Analysis — HR AI Chatbot

**Project:** HR AI Chatbot (NL→SQL)  
**Stack:** Streamlit, Groq API (llama-3.3-70b-versatile), MySQL, SQLAlchemy  
**Date:** Day 6 — Security Hardening  
**Authors:** [Your Name], [Teammate Name]

---

## Overview

This document covers the STRIDE threat analysis for the HR AI Chatbot, which converts
natural language questions into SQL queries and executes them against a MySQL employee
database. The system handles sensitive HR data including salaries, personal details,
and organisational structure.

---

## 1. Spoofing — Identity Threats

### Threat
Any user who gains access to the app URL could impersonate another employee or manager
and query HR data they are not authorised to see.

### Mitigations In Place
- **Google OAuth** — authentication is delegated to Google; the app never handles raw passwords
- **bcrypt** — passwords (where used) are hashed with bcrypt before storage
- **8-hour sessions** — sessions expire automatically; session IDs are stored server-side and validated on every request via `validate_session()`
- **Role enforcement** — `session["role"]` is set at login time from the database, not from user input

### Residual Risk
| Risk | Status |
|------|--------|
| No MFA (multi-factor authentication) | ⚠️ Unmitigated |
| No brute-force lockout on login attempts | ⚠️ Unmitigated |
| Session fixation attacks | ⚠️ Low risk, not explicitly handled |

---

## 2. Tampering — Data Integrity Threats

### Threat
The LLM could generate write SQL (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.) either
through prompt injection or model error, modifying or destroying HR data.

### Mitigations In Place
- **`validate_sql()` blocklist** — blocks all write and DDL keywords before any query reaches the database:
  ```
  DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE, REPLACE
  ```
- **Prompt hardening** — system prompt in `nl_to_sql()` explicitly instructs the model to generate SELECT-only queries
- **`hr_app` MySQL user** — database user has `SELECT` privilege only; even if a write query bypassed `validate_sql()`, the database would reject it at the connection level
- **Two-layer defence** — prompt rules + `validate_sql()` + DB-level permissions (defence in depth)

### Residual Risk
| Risk | Status |
|------|--------|
| Novel SQL constructs not in blocklist | ⚠️ Low risk — DB user is SELECT-only as final backstop |
| Tampering with flat log file (`chatbot.log`) | ⚠️ Unmitigated |

---

## 3. Repudiation — Audit Trail Threats

### Threat
Users could deny having made sensitive queries. Without a tamper-proof audit trail,
there is no way to prove who queried what data and when.

### Mitigations In Place
- **`chatbot.log`** — errors and security events are logged with `emp_no`, question, SQL, and timestamp via Python `logging`
- Every security block in `validate_sql()` is logged before the warning is shown to the user

### Residual Risk
| Risk | Status |
|------|--------|
| Flat log file is not tamper-proof — any admin can edit it | ⚠️ Unmitigated |
| Successful queries are not logged (only errors and blocks) | ⚠️ Unmitigated |
| No centralised audit log in the database | ⚠️ Unmitigated — production systems should use DB-backed logging |

> **Note:** The current flat-file log is insufficient for production. A database-backed
> audit table (recording every query, user, result row count, and timestamp) is required
> before this system handles real employee data.

---

## 4. Information Disclosure — Data Leakage Threats

### Threat
Sensitive HR data (salaries, personal details, org structure) could be leaked through
prompt injection, Unicode tricks, aggregation attacks, or schema probing.

### Mitigations In Place
- **`validate_sql()` blocks schema probing** — `INFORMATION_SCHEMA` and `SHOW TABLES` are blocked
- **Role-based query restriction** — employees can only query their own `emp_no`; managers are blocked from hardcoding other employees' `emp_nos`
- **Prompt injection mitigated** — system prompt instructs the model to ignore user attempts to override instructions
- **`hr_app` SELECT-only user** — limits blast radius if any query bypasses application-level checks

### Day 5 Attack Vectors — All Confirmed Blocked ✅
| # | Attack Vector | Result |
|---|---------------|--------|
| 1 | Direct prompt injection | Blocked |
| 2 | Unicode/homoglyph trick | Blocked |
| 3 | Aggregation leak (inferring salary via avg) | Blocked |
| 4 | INFORMATION_SCHEMA probe | Blocked |
| 5 | SHOW TABLES schema probe | Blocked |
| 6 | Cross-employee emp_no injection | Blocked |
| 7 | DDL via prompt (DROP TABLE) | Blocked |
| 8 | Role escalation attempt | Blocked |
| 9 | Blind SQL inference | Blocked |
| 10 | Multi-statement injection | Blocked |

### Residual Risk
| Risk | Status |
|------|--------|
| Manager can still run broad aggregation queries over their department | ⚠️ By design — acceptable |
| LLM may occasionally hallucinate column names, leaking schema hints in error messages | ⚠️ Low risk |

---

## 5. Denial of Service — Availability Threats

### Threat
A malicious or careless user could submit queries that return enormous result sets or
hammer the Groq API, degrading or crashing the service for other users.

### Mitigations In Place
- **Groq API error handling** — `_call_groq()` in `nl_to_sql.py` handles `APITimeoutError` (retry once with 2s backoff) and `RateLimitError` (surfaces wait time to user)
- **`ProgrammingError` handling** — invalid SQL is caught before it causes unhandled crashes

### Residual Risk
| Risk | Status |
|------|--------|
| No `LIMIT` clause enforced on queries — a query could return millions of rows | ⚠️ Unmitigated |
| No per-user rate limiter on questions per minute | ⚠️ Unmitigated |
| No query timeout on the MySQL connection | ⚠️ Unmitigated |

> **Recommended fix:** Append `LIMIT 500` in `run_query()` as a safety net, and add
> a per-user rate limiter (e.g. max 20 questions per minute) in `show_chat()`.

---

## 6. Elevation of Privilege — Access Control Threats

### Threat
An employee could attempt to gain manager-level access, or a manager could attempt to
query data outside their department or act as an admin.

### Mitigations In Place
- **Role set at login from DB** — `role` is read from the `hr_accounts` table at login; users cannot self-assign roles
- **`is_manager` flag passed through the stack** — `nl_to_sql()`, `validate_sql()`, and `show_chat()` all enforce role-specific rules
- **Prompt hardening by role** — the system prompt passed to the LLM differs based on `is_manager`, restricting what SQL it will generate
- **`validate_sql()` double-checks** — even if the LLM generates a query outside the user's role, `validate_sql()` blocks it
- **DDL fully blocked** — no user, including managers, can elevate to schema-modification level

### Residual Risk
| Risk | Status |
|------|--------|
| No MFA — a compromised Google account means full role access | ⚠️ Unmitigated |
| Manager department scope is enforced by prompt, not hard DB query | ⚠️ Medium risk — relies on LLM compliance |

---

## Summary Table

| Threat | Severity | Mitigated | Residual Risk |
|--------|----------|-----------|---------------|
| Spoofing | High | Partially | No MFA, no brute-force lockout |
| Tampering | Critical | Yes | Flat log is editable |
| Repudiation | Medium | Partially | Flat log insufficient for production |
| Information Disclosure | Critical | Yes | All 10 Day 5 vectors blocked |
| Denial of Service | Medium | Partially | No LIMIT clause, no rate limiter |
| Elevation of Privilege | High | Yes | Manager scope relies partly on LLM |

---

## Recommended Next Steps (Priority Order)

1. **Add `LIMIT 500`** to `run_query()` — prevents DoS from large result sets
2. **Per-user rate limiter** — max N questions per minute in `show_chat()`
3. **DB-backed audit log** — replace `chatbot.log` with a tamper-proof DB table
4. **MFA** — add TOTP or hardware key requirement for manager accounts
5. **Brute-force lockout** — lock account after N failed login attempts
6. **Query timeout** — set `connect_timeout` and `read_timeout` on the MySQL connection