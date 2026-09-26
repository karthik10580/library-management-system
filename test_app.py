import re

import pytest
from werkzeug.security import generate_password_hash

from app import app
from models import Admin, Book, Student, IssueRecord, db


@pytest.fixture
def client():
    app.config.update(TESTING=True, SECRET_KEY='test-secret-key', SQLALCHEMY_DATABASE_URI='sqlite://')
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def csrf_token(client):
    response = client.get('/login')
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
    assert match is not None
    return match.group(1)


def test_login_success_redirects_to_dashboard(client):
    response = client.post(
        '/login',
        data={'username': 'admin', 'password': 'admin123', 'csrf_token': csrf_token(client)},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers['Location'] == '/'


def test_login_requires_csrf_token(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'admin123'})

    assert response.status_code == 400


def test_issue_flow_and_delete_blocking(client):
    with app.app_context():
        book = Book(title='Clean Code', author='Robert Martin', isbn='9780132350884', category='Technology', total_copies=3, available_copies=3)
        student = Student(name='Alice', roll_number='CS2024001', email='alice@example.com', department='Computer Science')
        db.session.add_all([book, student])
        db.session.commit()

        login_response = client.post(
            '/login',
            data={'username': 'admin', 'password': 'admin123', 'csrf_token': csrf_token(client)},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        assert client.get(f'/books/delete/{book.id}').status_code == 405
        assert client.get(f'/students/delete/{student.id}').status_code == 405
        assert client.get('/issues/return/1').status_code == 405

        issue_response = client.post(
            '/issues/add',
            data={'book_id': str(book.id), 'student_id': str(student.id), 'csrf_token': csrf_token(client)},
            follow_redirects=True,
        )
        assert issue_response.status_code == 200
        assert IssueRecord.query.count() == 1
        assert db.session.get(Book, book.id).available_copies == 2

        invalid_issue_response = client.post(
            '/issues/add',
            data={'book_id': 'bad', 'student_id': str(student.id), 'csrf_token': csrf_token(client)},
            follow_redirects=True,
        )
        assert invalid_issue_response.status_code == 200
        assert 'A valid book and student selection are required' in invalid_issue_response.get_data(as_text=True)

        delete_book_response = client.post(
            f'/books/delete/{book.id}',
            data={'csrf_token': csrf_token(client)},
            follow_redirects=True,
        )
        assert delete_book_response.status_code == 200
        assert 'Cannot delete a book with existing issue records' in delete_book_response.get_data(as_text=True)

        delete_student_response = client.post(
            f'/students/delete/{student.id}',
            data={'csrf_token': csrf_token(client)},
            follow_redirects=True,
        )
        assert delete_student_response.status_code == 200
        assert 'Cannot delete a student with existing issue records' in delete_student_response.get_data(as_text=True)

        return_response = client.post(
            f'/issues/return/{IssueRecord.query.first().id}',
            data={'csrf_token': csrf_token(client)},
            follow_redirects=True,
        )
        assert return_response.status_code == 200
        assert IssueRecord.query.first().returned is True
