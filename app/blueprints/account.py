"""
Handles logging in/registering/editing a user account
"""
from flask import (
    Blueprint,
    flash,
    request,
    render_template,
    current_app,
    redirect,
    url_for,
)
import flask_login
from sqlalchemy.exc import IntegrityError
from is_safe_url import is_safe_url
from tabletop_story.plugins import db
from tabletop_story.forms import ShortRegistrationForm, LoginForm
from tabletop_story.models import User, GameCharacter


blueprint = Blueprint(
    "account",
    __name__,
    static_folder="../static",
    template_folder="../templates/account",
)


@blueprint.route("/login", methods=["POST", "GET"])
def login():
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password_hash(form.password.data):
            flash("Logged in! ✔️", "success")
            flask_login.login_user(user, remember=form.rememberme.data)
            next_page = request.args.get("next")
            return (
                redirect(next_page)
                if next_page and is_safe_url(next_page, url_for("dashboard.index"))
                else redirect(url_for("dashboard.index"))
            )
        else:
            flash("Wrong email or password.", "danger")

    return render_template("login.html", is_logged_in=False, form=form)


@blueprint.route("/profile")
@flask_login.login_required
def user_dashboard():
    """ Let the user manage their account settings, change password """
    user_id = int(flask_login.current_user.get_id())
    return str(user_id)


@blueprint.route("/profile/edit")
@flask_login.login_required
def edit_user():
    pass


@blueprint.route("/changepassword", methods=["GET", "POST"])
@flask_login.login_required
def change_password():
    pass


@blueprint.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("dashboard.index"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = ShortRegistrationForm()
    if form.validate_on_submit():
        try:
            db.session.add(
                User(
                    email=form.email.data,
                    username="test",
                    password=form.password.data,
                    is_admin=False,
                )
            )
            db.session.commit()
        except IntegrityError:
            flash("That email is already taken. Log in below", "danger")
            db.session.rollback()
        else:
            flash("Successly signed up! Now you can log in", "success")
        return redirect(url_for("account.login"))

    return render_template("register.html", is_logged_in=False, form=form)
