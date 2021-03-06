import os
import tempfile
import pytest
import flask_login
from flask import request
from tabletop_story.__init__ import create_app
from tabletop_story.app import init_app, plugins
from tabletop_story.models import User


def nav_selected_bytes(route):
    return bytes(
        f'<li class="nav-item active">\n                        <a class="nav-link" href="{route}">',
        "utf-8",
    )


@pytest.fixture
def client():
    global app, db, bcrypt, login_manager
    app = create_app()
    db, migrate, bcrypt, login_manager = plugins
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite+pysqlite:///" + db_path
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app = init_app(app)
    client = app.test_client()
    with app.app_context():
        with client:
            yield client
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def admin_logged_in_client():
    global app, db, bcrypt, login_manager
    app = create_app()
    db, migrate, bcrypt, login_manager = plugins
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite+pysqlite:///" + db_path
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app = init_app(app)
    client = app.test_client()
    with app.app_context():
        with client:
            db.create_all()
            user = User(
                email="test@example.com",
                username="test",
                password="password",
                is_admin=True,
            )
            db.session.add(user)
            db.session.commit()
            client.post(
                "/account/login",
                data={"email": "test@example.com", "password": "password"},
                follow_redirects=True,
            )
            yield client
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def user_logged_in_client():
    global app, db, bcrypt, login_manager
    app = create_app()
    db, migrate, bcrypt, login_manager = plugins
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite+pysqlite:///" + db_path
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app = init_app(app)
    client = app.test_client()
    with app.app_context():
        with client:
            db.create_all()
            user = User(
                email="test@example.com",
                username="test",
                password="password",
                is_admin=False,
            )
            db.session.add(user)
            db.session.commit()
            client.post(
                "/account/login",
                data={"email": "test@example.com", "password": "password"},
                follow_redirects=True,
            )
            yield client
    os.close(db_fd)
    os.unlink(db_path)


def test_index(client):
    resp = client.get("/")
    assert nav_selected_bytes("/") in resp.data
    assert resp.status_code == 200


def test_about_page(client):
    resp = client.get("/about")
    assert nav_selected_bytes("/about") in resp.data


def test_404_page(client):
    resp = client.get("/invalid")
    assert nav_selected_bytes("/") in resp.data
    assert resp.status_code == 404


def test_login_success(client):
    db.create_all()
    user = User(
        email="test@example.com",
        username="test",
        password="password",
        is_admin=False,
    )
    db.session.add(user)
    db.session.commit()
    resp = client.post(
        "/account/login",
        data={"email": "test@example.com", "password": "password"},
        follow_redirects=True,
    )
    assert bytes("Logged in! ✔️", "utf-8") in resp.data
    assert flask_login.current_user == user


def test_login_failure(client):
    db.create_all()
    user = User(
        email="test@example.com", username="test", password="password", is_admin=False
    )
    db.session.add(user)
    db.session.commit()
    resp = client.post(
        "/account/login",
        data={"email": "test@example.com", "password": "wordpass"},
        follow_redirects=True,
    )
    assert b"Wrong email or password" in resp.data
    assert flask_login.current_user != user


def test_registration_success(client):
    db.create_all()
    assert User.query.filter_by(email="test@example.com").first() is None
    resp = client.post(
        "/account/register",
        data={
            "email": "test@example.com",
            "password": "password",
            "confirmp": "password",
        },
        follow_redirects=True,
    )
    assert User.query.filter_by(email="test@example.com").first() is not None


def test_registration_failure(client):
    db.create_all()
    assert User.query.filter_by(email="test@example.com").first() is None
    resp = client.post(
        "/account/register",
        data={
            "email": "test@example.com",
            "password": "password",
            "confirmp": "",
        },
        follow_redirects=True,
    )
    assert User.query.filter_by(email="test@example.com").first() is None
    resp = client.post(
        "/account/register",
        data={
            "email": "nodomainname",
            "password": "password",
            "confirmp": "password",
        },
        follow_redirects=True,
    )
    assert User.query.filter_by(email="nodomainname").first() is None


def test_reregistration_failure(client):
    test_registration_success(client)
    resp = client.post(
        "/account/register",
        data={
            "email": "test@example.com",
            "password": "password",
            "confirmp": "password",
        },
        follow_redirects=True,
    )
    assert len(User.query.filter_by(email="test@example.com").all()) == 1


def test_admin_privilege(admin_logged_in_client):
    resp = admin_logged_in_client.get("/inventory/add")
    assert resp.status_code == 200


def test_user_privilege(client):
    db.create_all()
    user = User(
        email="test@example.com",
        username="test",
        password="password",
        is_admin=False,
    )
    db.session.add(user)
    db.session.commit()
    resp = client.get("/account/profile")
    assert resp.status_code == 302
    resp = client.get("/inventory/add")
    assert resp.status_code == 302
    client.post(
        "/account/login",
        data={"email": "test@example.com", "password": "password"},
        follow_redirects=True,
    )
    assert flask_login.current_user == user
    resp = client.get("/account/profile")
    assert resp.status_code == 200
    assert nav_selected_bytes("/") not in resp.data
    resp = client.get("/inventory/add")
    assert resp.status_code == 403
    assert nav_selected_bytes("/") in resp.data


def test_user_create_bard(user_logged_in_client):
    user_logged_in_client.get("/character/create/bard", follow_redirects=True)
    assert request.url == "http://localhost/character/edit/1"
    resp = user_logged_in_client.get("/character/view/1")
    assert resp.status_code == 200


def test_user_create_paladin(user_logged_in_client):
    user_logged_in_client.get("/character/create/paladin", follow_redirects=True)
    assert request.url == "http://localhost/character/edit/1"
    resp = user_logged_in_client.get("/character/view/1")
    assert resp.status_code == 200


def test_user_create_fighter(user_logged_in_client):
    user_logged_in_client.get("/character/create/fighter", follow_redirects=True)
    assert request.url == "http://localhost/character/edit/1"
    resp = user_logged_in_client.get("/character/view/1")
    assert resp.status_code == 200
