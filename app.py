import os
import secrets
from datetime import date, timedelta

import click
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Admin, Book, Student, IssueRecord


def _clean_form_value(field_name, default=''):
    value = request.form.get(field_name, default)
    if value is None:
        return default
    return str(value).strip()


def _parse_positive_int(value, minimum=0):
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed < minimum:
        return None
    return parsed

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///library.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', '').lower() in {'1', 'true', 'yes'},
)

os.makedirs(app.instance_path, exist_ok=True)

db.init_app(app)
CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class AdminUser(UserMixin):
    def __init__(self, admin):
        self.id = admin.id
        self.username = admin.username


@login_manager.user_loader
def load_user(user_id):
    admin = db.session.get(Admin, int(user_id))
    return AdminUser(admin) if admin else None


# ---------- Auth ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = _clean_form_value('username')
        password = _clean_form_value('password')
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('login.html')

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(AdminUser(admin))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---------- Dashboard ----------

@app.route('/')
@login_required
def dashboard():
    total_books = Book.query.count()
    total_copies = db.session.query(db.func.sum(Book.total_copies)).scalar() or 0
    issued_count = IssueRecord.query.filter_by(returned=False).count()
    total_students = Student.query.count()
    overdue_count = IssueRecord.query.filter(
        IssueRecord.returned == False, IssueRecord.due_date < date.today()
    ).count()
    return render_template(
        'dashboard.html',
        total_books=total_books,
        total_copies=total_copies,
        issued_count=issued_count,
        total_students=total_students,
        overdue_count=overdue_count,
    )


# ---------- Books CRUD ----------

@app.route('/books')
@login_required
def books():
    query = request.args.get('q', '')
    if query:
        book_list = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | (Book.author.ilike(f'%{query}%'))
        ).all()
    else:
        book_list = Book.query.all()
    return render_template('books.html', books=book_list, query=query)


@app.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = _clean_form_value('title')
        author = _clean_form_value('author')
        isbn = _clean_form_value('isbn')
        category = _clean_form_value('category')
        total_copies = _parse_positive_int(request.form.get('total_copies'), minimum=1)

        if not title or not author or not category or total_copies is None:
            flash('Title, author, category, and valid total copies are required', 'danger')
            return render_template('book_form.html', book=None)

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            total_copies=total_copies,
            available_copies=total_copies,
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully', 'success')
        return redirect(url_for('books'))
    return render_template('book_form.html', book=None)


@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = db.get_or_404(Book, book_id)
    if request.method == 'POST':
        title = _clean_form_value('title')
        author = _clean_form_value('author')
        isbn = _clean_form_value('isbn')
        category = _clean_form_value('category')
        total_copies = _parse_positive_int(request.form.get('total_copies'), minimum=1)

        if not title or not author or not category or total_copies is None:
            flash('Title, author, category, and valid total copies are required', 'danger')
            return render_template('book_form.html', book=book)

        diff = total_copies - book.total_copies
        book.title = title
        book.author = author
        book.isbn = isbn
        book.category = category
        book.total_copies = total_copies
        book.available_copies = max(0, book.available_copies + diff)
        db.session.commit()
        flash('Book updated successfully', 'success')
        return redirect(url_for('books'))
    return render_template('book_form.html', book=book)


@app.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    if book.issues:
        flash('Cannot delete a book with existing issue records', 'danger')
        return redirect(url_for('books'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted', 'info')
    return redirect(url_for('books'))


# ---------- Students CRUD ----------

@app.route('/students')
@login_required
def students():
    student_list = Student.query.all()
    return render_template('students.html', students=student_list)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = _clean_form_value('name')
        roll_number = _clean_form_value('roll_number')
        email = _clean_form_value('email')
        department = _clean_form_value('department')

        if not name or not roll_number:
            flash('Name and roll number are required', 'danger')
            return render_template('student_form.html', student=None)

        student = Student(
            name=name,
            roll_number=roll_number,
            email=email,
            department=department,
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully', 'success')
        return redirect(url_for('students'))
    return render_template('student_form.html', student=None)


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = db.get_or_404(Student, student_id)
    if request.method == 'POST':
        name = _clean_form_value('name')
        roll_number = _clean_form_value('roll_number')
        email = _clean_form_value('email')
        department = _clean_form_value('department')

        if not name or not roll_number:
            flash('Name and roll number are required', 'danger')
            return render_template('student_form.html', student=student)

        student.name = name
        student.roll_number = roll_number
        student.email = email
        student.department = department
        db.session.commit()
        flash('Student updated successfully', 'success')
        return redirect(url_for('students'))
    return render_template('student_form.html', student=student)


@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    if student.issues:
        flash('Cannot delete a student with existing issue records', 'danger')
        return redirect(url_for('students'))
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted', 'info')
    return redirect(url_for('students'))


# ---------- Issue / Return ----------

@app.route('/issues')
@login_required
def issues():
    records = IssueRecord.query.order_by(IssueRecord.issue_date.desc()).all()
    return render_template('issue.html', records=records, today=date.today())


@app.route('/issues/add', methods=['GET', 'POST'])
@login_required
def add_issue():
    if request.method == 'POST':
        book_id = _parse_positive_int(request.form.get('book_id'))
        student_id = _parse_positive_int(request.form.get('student_id'))

        if book_id is None or student_id is None:
            flash('A valid book and student selection are required', 'danger')
            return redirect(url_for('add_issue'))

        book = db.session.get(Book, book_id)
        student = db.session.get(Student, student_id)
        if not book or not student:
            flash('Selected book or student was not found', 'danger')
            return redirect(url_for('add_issue'))
        if book.available_copies < 1:
            flash('Book not available for issue', 'danger')
            return redirect(url_for('add_issue'))

        record = IssueRecord(
            book_id=book.id,
            student_id=student.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            returned=False,
        )
        book.available_copies -= 1
        db.session.add(record)
        db.session.commit()
        flash('Book issued successfully', 'success')
        return redirect(url_for('issues'))
    books_available = Book.query.filter(Book.available_copies > 0).all()
    student_list = Student.query.all()
    return render_template('issue_form.html', books=books_available, students=student_list)


@app.route('/issues/return/<int:record_id>', methods=['POST'])
@login_required
def return_book(record_id):
    record = db.get_or_404(IssueRecord, record_id)
    if not record.returned:
        record.returned = True
        record.return_date = date.today()
        record.book.available_copies += 1
        db.session.commit()
        flash('Book marked as returned', 'success')
    return redirect(url_for('issues'))


# ---------- CLI helpers ----------

@app.cli.command('init-db')
def init_db():
    """Create the database tables."""
    db.create_all()
    click.echo('Database initialized.')


@app.cli.command('create-admin')
@click.option('--username', prompt=True)
@click.password_option(confirmation_prompt=True)
def create_admin(username, password):
    """Create an admin account without using a default password."""
    username = username.strip()
    if not username:
        raise click.ClickException('Username cannot be empty.')
    if Admin.query.filter_by(username=username).first():
        raise click.ClickException(f'An admin with username "{username}" already exists.')

    admin = Admin(username=username, password_hash=generate_password_hash(password))
    db.session.add(admin)
    db.session.commit()
    click.echo(f'Admin account "{username}" created.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
