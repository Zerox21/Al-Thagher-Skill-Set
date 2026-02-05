from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import User, Skill, StudentSkillStatus, Question, Attempt, Report, Remediation
from app.utils import iso_week_key, now_utc
from app.reporting import generate_report_pdf
from app.mailer import send_email
import os

bp = Blueprint("student", __name__)

def _require_student():
    if current_user.role != "student":
        abort(403)

@bp.get("/select-teacher")
@login_required
def select_teacher():
    _require_student()
    teachers = User.query.filter_by(role="teacher").all()
    return render_template("student_select_teacher.html", teachers=teachers)

@bp.post("/select-teacher")
@login_required
def select_teacher_post():
    _require_student()
    tid = request.form.get("teacher_id")
    teacher = User.query.filter_by(role="teacher", id=tid).first()
    if not teacher:
        flash("الرجاء اختيار معلم صحيح.", "danger")
        return redirect(url_for("student.select_teacher"))
    current_user.teacher_id = teacher.id
    db.session.commit()
    flash("تم حفظ المعلم بنجاح.", "success")
    return redirect(url_for("student.dashboard"))

@bp.get("/dashboard")
@login_required
def dashboard():
    _require_student()
    statuses = StudentSkillStatus.query.filter_by(student_id=current_user.id).all()
    skill_ids = [s.skill_id for s in statuses if s.unlocked]
    skills = Skill.query.filter(Skill.id.in_(skill_ids)).order_by(Skill.order.asc()).all() if skill_ids else []
    attempts = Attempt.query.filter_by(student_id=current_user.id).order_by(Attempt.id.desc()).all()
    rem = Remediation.query.filter_by(student_id=current_user.id).order_by(Remediation.created_at.desc()).all()
    return render_template("student_dashboard.html", skills=skills, statuses=statuses, attempts=attempts, remediations=rem)

def _can_attempt(student_id: int, skill_id: int) -> tuple[bool,str]:
    wk = iso_week_key()
    existing = Attempt.query.filter_by(student_id=student_id, skill_id=skill_id, week_key=wk).first()
    if not existing:
        return True, wk
    status = StudentSkillStatus.query.filter_by(student_id=student_id, skill_id=skill_id).first()
    if status and status.extra_attempt_week == wk:
        status.extra_attempt_week = None
        db.session.commit()
        return True, wk
    return False, wk

@bp.get("/skill/<int:skill_id>/start")
@login_required
def start(skill_id: int):
    _require_student()
    status = StudentSkillStatus.query.filter_by(student_id=current_user.id, skill_id=skill_id).first()
    if not status or not status.unlocked:
        flash("هذه المهارة غير متاحة حالياً.", "danger")
        return redirect(url_for("student.dashboard"))

    ok, wk = _can_attempt(current_user.id, skill_id)
    if not ok:
        flash("لا يمكن إعادة الاختبار لهذه المهارة هذا الأسبوع.", "warning")
        return redirect(url_for("student.dashboard"))

    attempt = Attempt(student_id=current_user.id, skill_id=skill_id, week_key=wk, status="in_progress")
    db.session.add(attempt)
    db.session.commit()
    return redirect(url_for("student.take", attempt_id=attempt.id))

@bp.get("/attempt/<int:attempt_id>")
@login_required
def take(attempt_id: int):
    _require_student()
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.student_id != current_user.id:
        abort(403)
    if attempt.status == "submitted":
        return redirect(url_for("student.attempt_result", attempt_id=attempt.id))

    skill = Skill.query.get(attempt.skill_id)
    questions = Question.query.filter_by(skill_id=skill.id).order_by(Question.id.asc()).all()
    return render_template("student_take_test.html", attempt=attempt, skill=skill, questions=questions)

@bp.post("/attempt/<int:attempt_id>/submit")
@login_required
def submit(attempt_id: int):
    _require_student()
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.student_id != current_user.id:
        abort(403)
    if attempt.status == "submitted":
        return redirect(url_for("student.attempt_result", attempt_id=attempt.id))

    skill = Skill.query.get(attempt.skill_id)
    questions = Question.query.filter_by(skill_id=skill.id).order_by(Question.id.asc()).all()

    elapsed = int((now_utc() - attempt.started_at).total_seconds())
    max_seconds = int(skill.time_limit_min or 10) * 60
    if elapsed > max_seconds + 5:
        elapsed = max_seconds

    answers = {}
    correct = 0
    for q in questions:
        key = f"q_{q.id}"
        if q.qtype in ("mcq_single","tf","video_checkpoint"):
            val = request.form.get(key) or ""
            answers[str(q.id)] = [val] if val else []
            if q.correct_json and val and val in (q.correct_json.get("answers") or []):
                correct += 1
        elif q.qtype == "mcq_multi":
            vals = request.form.getlist(key)
            answers[str(q.id)] = vals
            if q.correct_json and sorted(vals) == sorted(q.correct_json.get("answers") or []):
                correct += 1
        elif q.qtype in ("short","numeric"):
            val = (request.form.get(key) or "").strip()
            answers[str(q.id)] = [val]
            if q.correct_json and val and val == str((q.correct_json.get("answers") or [""])[0]):
                correct += 1

    total = max(len(questions), 1)
    score = int(round((correct / total) * 100))

    attempt.answers_json = answers
    attempt.score = score
    attempt.status = "submitted"
    attempt.ended_at = now_utc()
    attempt.time_seconds = elapsed
    db.session.commit()

    status = StudentSkillStatus.query.filter_by(student_id=current_user.id, skill_id=skill.id).first()
    passed = score >= int(skill.pass_threshold or 60)
    if status and passed:
        status.completed = True
        db.session.commit()

    teacher = User.query.get(current_user.teacher_id) if current_user.teacher_id else None
    from flask import current_app
    reports_dir = current_app.config["REPORTS_DIR"]
    pdf_path = os.path.join(reports_dir, f"report_attempt_{attempt.id}.pdf")

    # weak skills (top 3)
    rows = (db.session.query(Attempt.skill_id, func.avg(Attempt.score))
            .filter(Attempt.student_id == current_user.id, Attempt.status=="submitted")
            .group_by(Attempt.skill_id).all())
    rows_sorted = sorted(rows, key=lambda r: r[1])
    weak_skill_ids = [r[0] for r in rows_sorted[:3]]
    weak_lines = []
    if weak_skill_ids:
        weak_skills = Skill.query.filter(Skill.id.in_(weak_skill_ids)).all()
        weak_lines = [f"- {s.name_ar}" for s in weak_skills]

    lines = [
        f"اسم الطالب: {current_user.name_ar} ({current_user.student_id})",
        f"المهارة: {skill.name_ar}",
        f"النتيجة: {score}% | الحالة: {'ناجح' if passed else 'راسب'}",
        f"الوقت المستهلك: {elapsed} ثانية",
        f"التاريخ: {now_utc().strftime('%Y-%m-%d %H:%M UTC')}",
        "—",
        "تفاصيل الإجابات:",
    ]
    for q in questions:
        a = answers.get(str(q.id), [])
        ca = (q.correct_json or {}).get("answers") if q.correct_json else []
        lines.append(f"س: {q.prompt_ar[:120]}")
        lines.append(f"إجابة الطالب: {', '.join(a) if a else '-'}")
        lines.append(f"الإجابة الصحيحة: {', '.join(ca) if ca else '-'}")
        lines.append(" ")

    if weak_lines:
        lines.append("أضعف المهارات (الأكثر احتياجاً):")
        lines.extend(weak_lines)

    generate_report_pdf(pdf_path, "تقرير نتيجة الاختبار", lines)

    if teacher:
        rep = Report(attempt_id=attempt.id, teacher_id=teacher.id, url=f"/media/report/{attempt.id}", storage_key=pdf_path)
        db.session.add(rep)
        db.session.commit()
        if teacher.email:
            send_email(teacher.email, "تقرير اختبار الطالب", "مرفق تقرير اختبار الطالب.", attachment_path=pdf_path)

    return redirect(url_for("student.attempt_result", attempt_id=attempt.id))

@bp.get("/attempt/<int:attempt_id>/result")
@login_required
def attempt_result(attempt_id: int):
    _require_student()
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.student_id != current_user.id:
        abort(403)
    skill = Skill.query.get(attempt.skill_id)
    rems = Remediation.query.filter_by(student_id=current_user.id, skill_id=skill.id).order_by(Remediation.created_at.desc()).all()
    return render_template("student_attempt_result.html", attempt=attempt, skill=skill, remediations=rems)
