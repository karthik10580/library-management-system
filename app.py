from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Admin, Book, Student, IssueRecord

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class AdminUser(UserMixin):
    def __init__(self, admin):
        self.id = admin.id
        self.username = admin.username


@login_manager.user_loader
def load_user(user_id):
    admin = Admin.query.get(int(user_id))
    return AdminUser(admin) if admin else None


# ---------- Auth ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(AdminUser(admin))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
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
        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            isbn=request.form['isbn'],
            category=request.form['category'],
            total_copies=int(request.form['total_copies']),
            available_copies=int(request.form['total_copies']),
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully', 'success')
        return redirect(url_for('books'))
    return render_template('book_form.html', book=None)


@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        diff = int(request.form['total_copies']) - book.total_copies
        book.title = request.form['title']
        book.author = request.form['author']
        book.isbn = request.form['isbn']
        book.category = request.form['category']
        book.total_copies = int(request.form['total_copies'])
        book.available_copies = max(0, book.available_copies + diff)
        db.session.commit()
        flash('Book updated successfully', 'success')
        return redirect(url_for('books'))
    return render_template('book_form.html', book=book)


@app.route('/books/delete/<int:book_id>')
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
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
        student = Student(
            name=request.form['name'],
            roll_number=request.form['roll_number'],
            email=request.form['email'],
            department=request.form['department'],
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully', 'success')
        return redirect(url_for('students'))
    return render_template('student_form.html', student=None)


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.roll_number = request.form['roll_number']
        student.email = request.form['email']
        student.department = request.form['department']
        db.session.commit()
        flash('Student updated successfully', 'success')
        return redirect(url_for('students'))
    return render_template('student_form.html', student=student)


@app.route('/students/delete/<int:student_id>')
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
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
        book = Book.query.get(int(request.form['book_id']))
        student = Student.query.get(int(request.form['student_id']))
        if not book or book.available_copies < 1:
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


@app.route('/issues/return/<int:record_id>')
@login_required
def return_book(record_id):
    record = IssueRecord.query.get_or_404(record_id)
    if not record.returned:
        record.returned = True
        record.return_date = date.today()
        record.book.available_copies += 1
        db.session.commit()
        flash('Book marked as returned', 'success')
    return redirect(url_for('issues'))


# ---------- CLI helper to create DB + default admin ----------

@app.cli.command('init-db')
def init_db():
    """Create tables and a default admin user (admin / admin123)."""
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
    print('Database initialized. Login with admin / admin123')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
