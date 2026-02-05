from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User

bp = Blueprint("auth", __name__)

@bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("auth.home"))
    return redirect(url_for("auth.login"))

@bp.get("/home")
@login_required
def home():
    if current_user.role == "chairman":
        return redirect(url_for("chairman.dashboard"))
    if current_user.role == "teacher":
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))

@bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        teachers = User.query.filter_by(role="teacher").all()
        return render_template("login.html", teachers=teachers)

    role = request.form.get("role", "")
    if role == "student":
        sid = (request.form.get("student_id") or "").strip()
        pw = request.form.get("password") or ""
        user = User.query.filter_by(role="student", student_id=sid).first()
        if not user or not user.check_password(pw):
            flash("بيانات الدخول غير صحيحة.", "danger")
            return redirect(url_for("auth.login"))
        login_user(user)
        if not user.teacher_id:
            return redirect(url_for("student.select_teacher"))
        return redirect(url_for("student.dashboard"))

    username = (request.form.get("username") or "").strip()
    pw = request.form.get("password") or ""
    user = User.query.filter_by(username=username).first()
    if not user or user.role not in ("chairman","teacher") or not user.check_password(pw):
        flash("بيانات الدخول غير صحيحة.", "danger")
        return redirect(url_for("auth.login"))
    login_user(user)
    return redirect(url_for("auth.home"))

@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
