"""
seed_data.py -- Populate the Library Management System with sample demo data.
Run with: python seed_data.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import app
from models import db, Admin, Book, Student, IssueRecord

BOOKS = [
    ("The Great Gatsby",        "F. Scott Fitzgerald", "9780743273565", "Fiction",       5),
    ("To Kill a Mockingbird",   "Harper Lee",          "9780061935466", "Fiction",       4),
    ("1984",                    "George Orwell",       "9780451524935", "Dystopian",     6),
    ("Sapiens",                 "Yuval Noah Harari",   "9780062316097", "History",       3),
    ("Clean Code",              "Robert C. Martin",   "9780132350884", "Technology",    4),
    ("The Alchemist",           "Paulo Coelho",        "9780062315007", "Fiction",       5),
    ("Atomic Habits",           "James Clear",         "9780735211292", "Self-Help",     4),
    ("Introduction to Algorithms","Thomas H. Cormen",  "9780262033848", "Technology",    2),
    ("Thinking, Fast and Slow", "Daniel Kahneman",     "9780374533557", "Psychology",   3),
    ("The Pragmatic Programmer","Andrew Hunt",         "9780135957059", "Technology",    3),
]

STUDENTS = [
    ("Alice Johnson",  "CS2021001", "alice@example.com",   "Computer Science"),
    ("Bob Smith",      "EE2021002", "bob@example.com",     "Electrical Eng."),
    ("Carol White",    "ME2021003", "carol@example.com",   "Mechanical Eng."),
    ("David Brown",    "CS2022004", "david@example.com",   "Computer Science"),
    ("Eva Martinez",   "BT2022005", "eva@example.com",     "Biotechnology"),
    ("Frank Lee",      "CS2023006", "frank@example.com",   "Computer Science"),
    ("Grace Kim",      "PH2023007", "grace@example.com",   "Physics"),
    ("Henry Davis",    "MA2023008", "henry@example.com",   "Mathematics"),
]

def seed():
    with app.app_context():
        db.create_all()

        # Ensure default admin exists
        if not Admin.query.filter_by(username="admin").first():
            db.session.add(Admin(
                username="admin",
                password_hash=generate_password_hash("admin123")
            ))
            print("✔  Admin user created  (admin / admin123)")

        # Add books
        added_books = 0
        for title, author, isbn, category, copies in BOOKS:
            if not Book.query.filter_by(isbn=isbn).first():
                db.session.add(Book(
                    title=title, author=author, isbn=isbn,
                    category=category,
                    total_copies=copies, available_copies=copies
                ))
                added_books += 1
        db.session.commit()
        print(f"✔  {added_books} book(s) added")

        # Add students
        added_students = 0
        for name, roll, email, dept in STUDENTS:
            if not Student.query.filter_by(roll_number=roll).first():
                db.session.add(Student(
                    name=name, roll_number=roll, email=email, department=dept
                ))
                added_students += 1
        db.session.commit()
        print(f"✔  {added_students} student(s) added")

        # Add issue records (mix of active, returned, and overdue)
        records_added = 0
        issues = [
            # (book_isbn,        student_roll,  issue_offset, return_offset, returned)
            ("9780743273565",   "CS2021001",   -10, None,  False),   # active
            ("9780061935466",   "EE2021002",   -20, -5,    True),    # returned
            ("9780451524935",   "CS2022004",   -5,  None,  False),   # active
            ("9780062316097",   "BT2022005",   -18, -2,    True),    # returned
            ("9780132350884",   "CS2023006",   -30, None,  False),   # overdue
            ("9780062315007",   "PH2023007",   -8,  None,  False),   # active
            ("9780735211292",   "MA2023008",   -25, None,  False),   # overdue
            ("9780374533557",   "CS2021001",   -3,  None,  False),   # active
            ("9780135957059",   "ME2021003",   -12, -1,    True),    # returned
            ("9780062316097",   "CS2022004",   -2,  None,  False),   # active
        ]

        today = date.today()
        for isbn, roll, issue_off, return_off, returned in issues:
            book = Book.query.filter_by(isbn=isbn).first()
            student = Student.query.filter_by(roll_number=roll).first()
            if not book or not student:
                continue
            issue_date = today + timedelta(days=issue_off)
            due_date   = issue_date + timedelta(days=14)
            return_date = (today + timedelta(days=return_off)) if return_off is not None else None

            record = IssueRecord(
                book_id=book.id,
                student_id=student.id,
                issue_date=issue_date,
                due_date=due_date,
                returned=returned,
                return_date=return_date,
            )
            if not returned:
                book.available_copies = max(0, book.available_copies - 1)
            db.session.add(record)
            records_added += 1

        db.session.commit()
        print(f"✔  {records_added} issue record(s) added")
        print("\n🎉 Demo data seeded successfully!")
        print("   Open http://127.0.0.1:5000 and log in with  admin / admin123")

if __name__ == "__main__":
    seed()
