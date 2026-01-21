from __future__ import annotations
import csv, io
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .. import db
from ..models import User, Skill, StudentSkill, Attempt, Question

bp = Blueprint("chairman", __name__)

def _ensure_admin():
    if current_user.role != "chairman":
        flash("Chairman access only.", "error")
        return False
    return True

@bp.get("/dashboard")
@login_required
def dashboard():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    teachers = User.query.filter_by(role="teacher").all()
    students = User.query.filter_by(role="student").all()
    skills = Skill.query.filter_by(is_active=True).order_by(Skill.order_index.asc()).all()
    attempts = Attempt.query.filter(Attempt.finished_at.isnot(None)).all()

    perf = []
    for t in teachers:
        t_attempts = [a for a in attempts if a.teacher_id == t.id]
        avg = round(100 * (sum([a.score or 0 for a in t_attempts]) / len(t_attempts)), 2) if t_attempts else 0.0
        perf.append({"teacher": t, "attempts": len(t_attempts), "avg": avg})
    perf.sort(key=lambda x: x["avg"], reverse=True)

    sperf = []
    for s in students:
        s_attempts = [a for a in attempts if a.student_id == s.id]
        avg = round(100 * (sum([a.score or 0 for a in s_attempts]) / len(s_attempts)), 2) if s_attempts else 0.0
        sperf.append({"student": s, "attempts": len(s_attempts), "avg": avg})
    sperf.sort(key=lambda x: x["avg"])

    return render_template("chairman_dashboard.html", teachers=teachers, students=students, skills=skills, perf=perf, sperf=sperf)

@bp.get("/users")
@login_required
def users():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    teachers = User.query.filter_by(role="teacher").order_by(User.name.asc()).all()
    students = User.query.filter_by(role="student").order_by(User.name.asc()).all()
    return render_template("chairman_users.html", teachers=teachers, students=students)

@bp.post("/users/add_teacher")
@login_required
def add_teacher():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    tid = (request.form.get("tid") or "").strip()
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    pin = (request.form.get("pin") or "1234").strip()

    if not tid or not name:
        flash("Teacher ID and name required.", "error")
        return redirect(url_for("chairman.users"))

    if User.query.filter_by(id=tid).first():
        flash("ID already exists.", "error")
        return redirect(url_for("chairman.users"))

    db.session.add(User(
        id=tid,
        role="teacher",
        name=name,
        email=email or None,
        pin_hash=generate_password_hash(pin),
    ))
    db.session.commit()
    flash("Teacher added.", "ok")
    return redirect(url_for("chairman.users"))

@bp.post("/users/import_students")
@login_required
def import_students():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    f = request.files.get("csv_file")
    if not f or not f.filename:
        flash("Upload CSV file.", "error")
        return redirect(url_for("chairman.users"))

    content = f.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    created, updated = 0, 0

    skills = Skill.query.filter_by(is_active=True).order_by(Skill.order_index.asc()).all()

    for row in reader:
        sid = (row.get("student_id") or "").strip()
        name = (row.get("name") or "").strip()
        pin = (row.get("pin") or "1234").strip()
        teacher_id = (row.get("teacher_id") or "").strip()

        if not sid or not name:
            continue

        u = User.query.filter_by(id=sid, role="student").first()
        if not u:
            u = User(
                id=sid,
                role="student",
                name=name,
                teacher_id=teacher_id or None,
                pin_hash=generate_password_hash(pin),
            )
            db.session.add(u)
            created += 1
        else:
            u.name = name
            u.teacher_id = teacher_id or u.teacher_id
            updated += 1

        db.session.flush()

        for sk in skills:
            perm = StudentSkill.query.filter_by(student_id=u.id, skill_id=sk.id).first()
            if not perm:
                allowed = (sk.order_index == 1)
                db.session.add(StudentSkill(student_id=u.id, skill_id=sk.id, allowed=allowed))

    db.session.commit()
    flash(f"Students imported. Created: {created}, Updated: {updated}.", "ok")
    return redirect(url_for("chairman.users"))

@bp.get("/skills")
@login_required
def skills():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    skills = Skill.query.order_by(Skill.order_index.asc()).all()
    return render_template("chairman_skills.html", skills=skills)

@bp.post("/skills/add")
@login_required
def add_skill():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    name = (request.form.get("name") or "").strip()
    order_index = int(request.form.get("order_index") or "0")
    duration_min = int(request.form.get("duration_min") or "0") or None

    pass_pct_raw = request.form.get("pass_pct")
    pass_pct = int(pass_pct_raw) if pass_pct_raw and str(pass_pct_raw).strip() else None

    if not name:
        flash("Skill name required.", "error")
        return redirect(url_for("chairman.skills"))

    sk = Skill(name=name, order_index=order_index, duration_min=duration_min, pass_pct=pass_pct, is_active=True)
    db.session.add(sk)
    db.session.commit()

    students = User.query.filter_by(role="student").all()
    for stu in students:
        db.session.add(StudentSkill(student_id=stu.id, skill_id=sk.id, allowed=False))
    db.session.commit()

    flash("Skill added.", "ok")
    return redirect(url_for("chairman.skills"))

@bp.get("/question_tool")
@login_required
def question_tool():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    skills = Skill.query.filter_by(is_active=True).order_by(Skill.order_index.asc()).all()
    questions = Question.query.order_by(Question.id.desc()).limit(500).all()
    return render_template("question_tool.html", skills=skills, questions=questions, role=current_user.role)

@bp.post("/question_tool/add")
@login_required
def add_question():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    import json
    skill_id = int(request.form.get("skill_id"))
    qtype = request.form.get("qtype")
    prompt = (request.form.get("prompt") or "").strip()
    options = (request.form.get("options") or "").strip()
    answer = (request.form.get("answer") or "").strip()
    meta = (request.form.get("meta") or "").strip()

    if not prompt:
        flash("Prompt required.", "error")
        return redirect(url_for("chairman.question_tool"))

    options_json = None
    if options:
        opts = [x.strip() for x in options.split("\n") if x.strip()]
        options_json = json.dumps(opts, ensure_ascii=False)

    answer_json = None
    try:
        if qtype == "mcq_multi":
            answer_json = json.dumps([int(x.strip()) for x in answer.split(",") if x.strip()], ensure_ascii=False)
        elif qtype == "short_text":
            answer_json = json.dumps(answer, ensure_ascii=False)
        else:
            answer_json = json.dumps(int(answer), ensure_ascii=False) if answer != "" else None
    except Exception:
        answer_json = json.dumps(answer, ensure_ascii=False) if qtype == "short_text" else None

    meta_json = None
    if meta:
        m = meta.strip()
        meta_json = m if (m.startswith("{") or m.startswith("[")) else json.dumps(m, ensure_ascii=False)

    q = Question(
        skill_id=skill_id,
        qtype=qtype,
        prompt=prompt,
        options_json=options_json,
        answer_json=answer_json,
        meta_json=meta_json,
        status="approved",
        created_by_id=current_user.id,
        created_by_role=current_user.role,
        approved_by_id=current_user.id,
        approved_at=datetime.utcnow(),
    )
    db.session.add(q)
    db.session.commit()

    flash("Question added (approved).", "ok")
    return redirect(url_for("chairman.question_tool"))

@bp.post("/question_tool/approve/<int:question_id>")
@login_required
def question_approve(question_id: int):
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    q = Question.query.get(question_id)
    if not q:
        flash("Question not found.", "error")
        return redirect(url_for("chairman.question_tool"))

    from ..qutils import is_approvable
    ok, msg = is_approvable(q.qtype, q.options_json, q.answer_json)
    if not ok:
        flash(f"Cannot approve: {msg}", "error")
        return redirect(url_for("chairman.question_tool"))

    q.status = "approved"
    q.approved_by_id = current_user.id
    q.approved_at = datetime.utcnow()
    db.session.commit()

    flash("Question approved.", "ok")
    return redirect(url_for("chairman.question_tool"))

@bp.get("/export/attempts.csv")
@login_required
def export_attempts_csv():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    import csv, io
    from flask import Response

    attempts = Attempt.query.filter(Attempt.finished_at.isnot(None)).order_by(Attempt.finished_at.desc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["attempt_id","student_id","student_name","teacher_id","teacher_name","skill","started_at","finished_at","duration_sec","score_pct","passed"])
    for a in attempts:
        w.writerow([
            a.id, a.student_id, a.student.name if a.student else "",
            a.teacher_id, a.teacher.name if a.teacher else "",
            a.skill.name if a.skill else "",
            a.started_at, a.finished_at, a.duration_sec,
            int(round((a.score or 0)*100)),
            a.passed
        ])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=attempts.csv"})

@bp.get("/export/students.csv")
@login_required
def export_students_csv():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    import csv, io
    from flask import Response

    students = User.query.filter_by(role="student").order_by(User.id.asc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["student_id","name","teacher_id"])
    for s in students:
        w.writerow([s.id, s.name, s.teacher_id or ""])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=students.csv"})

@bp.get("/export/teachers.csv")
@login_required
def export_teachers_csv():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    import csv, io
    from flask import Response

    teachers = User.query.filter_by(role="teacher").order_by(User.id.asc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["teacher_id","name","email"])
    for t in teachers:
        w.writerow([t.id, t.name, t.email or ""])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=teachers.csv"})


@bp.get("/question_tool/edit/<int:question_id>")
@login_required
def question_edit(question_id: int):
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    q = Question.query.get(question_id)
    if not q:
        flash("Question not found.", "error")
        return redirect(url_for("chairman.question_tool"))

    skills = Skill.query.filter_by(is_active=True).order_by(Skill.order_index.asc()).all()
    return render_template("chairman_question_edit.html", q=q, skills=skills)

@bp.post("/question_tool/edit/<int:question_id>")
@login_required
def question_edit_post(question_id: int):
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    import json
    q = Question.query.get(question_id)
    if not q:
        flash("Question not found.", "error")
        return redirect(url_for("chairman.question_tool"))

    q.skill_id = int(request.form.get("skill_id"))
    q.qtype = request.form.get("qtype")
    q.prompt = (request.form.get("prompt") or "").strip()

    options = (request.form.get("options") or "").strip()
    answer = (request.form.get("answer") or "").strip()
    meta = (request.form.get("meta") or "").strip()

    if options:
        opts = [x.strip() for x in options.split("\n") if x.strip()]
        q.options_json = json.dumps(opts, ensure_ascii=False)
    else:
        q.options_json = None

    try:
        if q.qtype == "mcq_multi":
            q.answer_json = json.dumps([int(x.strip()) for x in answer.split(",") if x.strip()], ensure_ascii=False)
        elif q.qtype == "short_text":
            q.answer_json = json.dumps(answer, ensure_ascii=False)
        else:
            q.answer_json = json.dumps(int(answer), ensure_ascii=False) if answer != "" else None
    except Exception:
        q.answer_json = json.dumps(answer, ensure_ascii=False) if q.qtype == "short_text" else None

    if meta:
        m = meta.strip()
        q.meta_json = m if (m.startswith("{") or m.startswith("[")) else json.dumps(m, ensure_ascii=False)
    else:
        q.meta_json = None

    db.session.commit()
    flash("Question updated.", "ok")
    return redirect(url_for("chairman.question_tool"))

@bp.get("/doc_import")
@login_required
def doc_import():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))
    skills = Skill.query.filter_by(is_active=True).order_by(Skill.order_index.asc()).all()
    return render_template("chairman_doc_import.html", skills=skills)

@bp.post("/doc_import")
@login_required
def doc_import_post():
    if not _ensure_admin():
        return redirect(url_for('auth.home'))

    import os, json
    import re
    from flask import current_app
    from ..doc_import import render_pdf_pages_to_images, split_docx_text_to_questions
    from docx import Document

    f = request.files.get("file")
    default_skill_id = int(request.form.get("default_skill_id") or "0") or None

    if not f or not f.filename:
        flash("Upload a PDF or DOCX.", "error")
        return redirect(url_for("chairman.doc_import"))

    name = f.filename
    ext = name.rsplit(".",1)[-1].lower() if "." in name else ""
    if ext not in {"pdf","docx"}:
        flash("Only PDF or DOCX supported.", "error")
        return redirect(url_for("chairman.doc_import"))

    if not default_skill_id:
        flash("Choose a default skill.", "error")
        return redirect(url_for("chairman.doc_import"))

    base_dir = os.path.join(current_app.config["MEDIA_DIR"], "imports", "chairman", current_user.id)
    os.makedirs(base_dir, exist_ok=True)
    safe = "".join([c if c.isalnum() or c in "._-" else "_" for c in name]).strip("_") or f"upload.{ext}"
    src_path = os.path.join(base_dir, safe)
    f.save(src_path)

    created = 0
    if ext == "pdf":
        out_dir = os.path.join(current_app.config["MEDIA_DIR"], "pdf_imports")
        os.makedirs(out_dir, exist_ok=True)
        prefix = re.sub(r"[^A-Za-z0-9_-]+", "_", safe.rsplit(".",1)[0])[:40] or "pdf"
        imgs = render_pdf_pages_to_images(src_path, out_dir, prefix=prefix)
        for img in imgs:
            rel = f"pdf_imports/{img}"
            q = Question(
                skill_id=default_skill_id,
                qtype="image_mcq_single",
                prompt=f"Imported from PDF: {safe} — page {img.split('_p')[-1].split('.')[0]}",
                options_json=None,
                answer_json=None,
                meta_json=json.dumps({"image_media": rel}, ensure_ascii=False),
                status="draft",
                created_by_id=current_user.id,
                created_by_role="chairman",
            )
            db.session.add(q)
            created += 1
        db.session.commit()
        flash(f"Imported {created} draft questions (one per page). Edit each to add options & answer, then approve.", "ok")
        return redirect(url_for("chairman.question_tool"))

    doc = Document(src_path)
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text])
    qs = split_docx_text_to_questions(full_text)
    if not qs:
        qs = [full_text] if full_text.strip() else []
    for i, qtext in enumerate(qs, start=1):
        q = Question(
            skill_id=default_skill_id,
            qtype="short_text",
            prompt=f"Imported from DOCX: {safe}\n\n{qtext}",
            options_json=None,
            answer_json=None,
            meta_json=None,
            status="draft",
            created_by_id=current_user.id,
            created_by_role="chairman",
        )
        db.session.add(q)
        created += 1
    db.session.commit()
    flash(f"Imported {created} draft questions from DOCX. Review and set type/options/answer, then approve.", "ok")
    return redirect(url_for("chairman.question_tool"))
