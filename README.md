# MoneyMate Backend API 💰

A complete Django REST Framework backend for the **MoneyMate** expense tracker app.

---

## Tech Stack
- **Django 4.2** + **Django REST Framework**
- **PostgreSQL** (database)
- **JWT Authentication** (djangorestframework-simplejwt)
- **ML Integration** via `requests` → https://ml-reposit.onrender.com

---

## Setup

### 1. Install PostgreSQL
Download from https://www.postgresql.org/download/windows/  
Set a password for the `postgres` user during install.

### 2. Create Database
Open **pgAdmin** or **psql** and run:
```sql
CREATE DATABASE moneymate_db;
```

### 3. Configure Environment
Edit `.env` and set your PostgreSQL password:
```
DB_PASSWORD=your_postgres_password_here
```

### 4. Create & Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 5. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 6. Run Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Admin User
```powershell
python manage.py createsuperuser
```

### 8. Start Server
```powershell
python manage.py runserver
```

API is live at: **http://127.0.0.1:8000**  
Admin panel: **http://127.0.0.1:8000/admin/**

---

## API Endpoints

All endpoints require `Authorization: Bearer <access_token>` **except** register and login.

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/register/` | Register (returns tokens) |
| POST | `/api/auth/login/` | Login (returns tokens) |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET/PUT | `/api/auth/profile/` | User profile |

### Accounts Screen
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/accounts/` | List / create account |
| GET/PUT/DELETE | `/api/accounts/<id>/` | Account detail |
| GET | `/api/accounts/summary/` | Total balance + breakdown |
| POST | `/api/accounts/<id>/balance/` | Adjust balance |

### Categories Screen
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/categories/` | List / create category |
| GET/PUT/DELETE | `/api/categories/<id>/` | Category detail |
| POST | `/api/categories/initialize/` | Create all default categories |

Filters: `?type=income` or `?type=expense`

### Record Screen (Transactions)
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/transactions/` | List / add transaction |
| GET/PUT/DELETE | `/api/transactions/<id>/` | Edit / delete transaction |
| GET | `/api/transactions/summary/` | Income & expense totals |

Filters: `?type=income|expense|transfer`, `?category=<id>`, `?account=<id>`, `?month=YYYY-MM`, `?year=YYYY`, `?start_date=`, `?end_date=`, `?search=`

### Budgets Screen
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/budgets/` | List / create budget |
| GET/PUT/DELETE | `/api/budgets/<id>/` | Budget detail |
| GET | `/api/budgets/overview/` | Full overview with progress |

Filters: `?month=10&year=2026`

### Charts & Analytics Screens
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/analytics/charts/` | Pie chart data |
| GET | `/api/analytics/income-flow/` | Income sources & monthly trend |
| GET | `/api/analytics/expense-flow/` | Spending patterns + 30-day daily trend |
| GET | `/api/analytics/account/<id>/` | Per-account analysis |

### Split Screen
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/splits/` | List / create split |
| GET/PUT/DELETE | `/api/splits/<id>/` | Split detail |
| POST | `/api/splits/<id>/mark-paid/` | Mark member paid/unpaid |
| POST | `/api/splits/calculator/equal/` | Equal split calculator |

### Cash Calculator
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/calculator/cash/` | Total from denominations |

### Future Budget Predictor (ML)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/ml/status/` | ML service health |
| GET | `/api/ml/predict/daily/` | Daily prediction |
| GET | `/api/ml/predict/monthly/` | Monthly prediction |
| GET | `/api/ml/predict/future-budget/` | Full predictor (main screen) |

---

## First-Time App Flow (for frontend team)
1. `POST /api/auth/register/` → save `access` + `refresh` tokens
2. `POST /api/categories/initialize/` → create default categories
3. `POST /api/accounts/` → create first account (e.g. Cash)
4. Start adding transactions via `POST /api/transactions/`

---

## Notes
- Account balances update **automatically** on transaction create/edit/delete
- ML endpoints handle Render cold-start timeouts gracefully with retry messages
- CORS is open for all origins (restrict in production)
- JWT access token: 1 day | refresh token: 7 days
