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
├── requirements.txt
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

1. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the app:
   ```
   python app.py
   ```
   The database (`library.db`) and a default admin account are created automatically on first run.

4. Open your browser at `http://127.0.0.1:5000`

**Default login:** `admin` / `admin123`

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
