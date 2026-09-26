# Library Inventory & Issue Management System

A mini project built with **Flask**, **SQLAlchemy**, and **Bootstrap** for managing library books, students, and book issue/return records.

## Features
- Admin login (Flask-Login)
- Dashboard with live stats (total books, copies, issued, overdue, students)
- Book CRUD (add / edit / delete / search)
- Student CRUD (add / edit / delete)
- Issue a book to a student (auto due date: 14 days)
- Mark a book as returned
- Overdue books highlighted automatically

## Tech Stack
- Backend: Flask
- Database: SQLite (via SQLAlchemy ORM)
- Auth: Flask-Login + password hashing (Werkzeug)
- Frontend: Bootstrap 5 (via CDN)

## Project Structure
```
library_management_system/
├── app.py                 # Routes and app logic
├── models.py               # Database models (Admin, Book, Student, IssueRecord)
├── wsgi.py                 # WSGI entry point for PythonAnywhere
├── requirements.txt
├── test_app.py             # Application regression tests
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── books.html
│   ├── book_form.html
│   ├── students.html
│   ├── student_form.html
│   ├── issue.html
│   └── issue_form.html
└── README.md
```

## Setup & Run

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Initialize the database and create an admin account:
   ```
   python -m flask --app app init-db
   python -m flask --app app create-admin
   ```
   The admin command prompts for a username and password. The SQLite database is stored in the ignored `instance/` directory.

4. Run the app locally:
   ```
   python app.py
   ```
   Open `http://127.0.0.1:5000`.

Set `SECRET_KEY` to a long random value for a stable session key. Set `SESSION_COOKIE_SECURE=1` when serving over HTTPS.

## Deploy to PythonAnywhere

1. Push or merge this project to GitHub, then create a PythonAnywhere account and open a Bash console.
2. Clone the repository and install dependencies in a virtual environment using the same Python version selected for the web app:
   ```
   git clone --branch karthik10580-library-management-fix https://github.com/karthik10580/library-management-system.git
   cd library-management-system
   python3 -m venv ~/.virtualenvs/library-management-system
   source ~/.virtualenvs/library-management-system/bin/activate
   pip install -r requirements.txt
   ```
   If PythonAnywhere selected a versioned interpreter, use that version's command (for example, `python3.13`) instead of `python3`.
3. Initialize the hosted database and create your own admin login:
   ```
   python -m flask --app app init-db
   python -m flask --app app create-admin
   ```
   Keep the `instance/` directory and `instance/library.db` on PythonAnywhere; they contain the library data.
4. In the PythonAnywhere **Web** tab, create a manual Flask web app, select the virtual environment above, and set the source-code directory to the cloned project directory.
5. In the WSGI configuration file linked from the Web tab, add the project path and environment settings. Replace the username and use a newly generated secret:
   ```python
   import os
   import sys

   project_home = '/home/YOUR_USERNAME/library-management-system'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ['SECRET_KEY'] = 'PASTE_A_LONG_RANDOM_SECRET_HERE'
   os.environ['SESSION_COOKIE_SECURE'] = '1'

   from wsgi import application
   ```
   Generate a secret in the Bash console with `python -c "import secrets; print(secrets.token_hex(32))"`. Keep it private and never commit it.
6. Save the WSGI file and click **Reload** on the Web tab. PythonAnywhere will display the public URL to share.

After updating the code, pull the changes in the PythonAnywhere Bash console, reinstall dependencies if they changed, and reload the web app. Never use a default admin password on a public deployment.

## Database Schema (summary)
- **Admin** — id, username, password_hash
- **Book** — id, title, author, isbn, category, total_copies, available_copies
- **Student** — id, name, roll_number, email, department
- **IssueRecord** — id, book_id (FK), student_id (FK), issue_date, due_date, return_date, returned

## Possible Extensions (for viva / bonus marks)
- Email/SMS reminders for due dates
- Fine calculation for overdue books
- Export reports to PDF/Excel
- Barcode/QR scanning for books
- Student self-service portal (view issued books, request renewal)
