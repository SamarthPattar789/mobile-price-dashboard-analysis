from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import User

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        SessionLocal = current_app.session_factory
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("dashboard.index"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        SessionLocal = current_app.session_factory
        with SessionLocal() as db:
            exists = db.query(User).filter(User.email == email).first()
            if exists:
                flash("Email already registered", "warning")
            else:
                user = User(email=email, password_hash=generate_password_hash(password), role="user")
                db.add(user)
                db.commit()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("auth.login"))
    return render_template("signup.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


