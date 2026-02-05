from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import User, Skill, Question, Attempt

bp = Blueprint("chairman", __name__)

def _require_chairman():
    if current_user.role != "chairman":
        abort(403)

@bp.get("/dashboard")
@login_required
def dashboard():
    _require_chairman()
    teachers = User.query.filter_by(role="teacher").all()
    students = User.query.filter_by(role="student").all()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    sperf = (db.session.query(User.id, User.name_ar, User.student_id, func.avg(Attempt.score))
             .outerjoin(Attempt, Attempt.student_id==User.id)
             .filter(User.role=="student")
             .group_by(User.id).all())
    return render_template("chairman_dashboard.html", teachers=teachers, students=students, skills=skills, sperf=sperf)

@bp.get("/users")
@login_required
def users():
    _require_chairman()
    teachers = User.query.filter_by(role="teacher").order_by(User.id.desc()).all()
    students = User.query.filter_by(role="student").order_by(User.id.desc()).all()
    return render_template("chairman_users.html", teachers=teachers, students=students)

@bp.post("/users/teacher")
@login_required
def create_teacher():
    _require_chairman()
    username = (request.form.get("username") or "").strip()
    name_ar = request.form.get("name_ar") or ""
    pw = request.form.get("password") or ""
    if not username or not pw:
        flash("الرجاء تعبئة البيانات.", "danger")
        return redirect(url_for("chairman.users"))
    if User.query.filter_by(username=username).first():
        flash("اسم المستخدم موجود.", "danger")
        return redirect(url_for("chairman.users"))
    t = User(username=username, name_ar=name_ar or username, role="teacher")
    t.set_password(pw)
    db.session.add(t)
    db.session.commit()
    flash("تم إنشاء المعلم.", "success")
    return redirect(url_for("chairman.users"))

@bp.post("/users/student")
@login_required
def create_student():
    _require_chairman()
    student_id = (request.form.get("student_id") or "").strip()
    name_ar = request.form.get("name_ar") or ""
    teacher_id = int(request.form.get("teacher_id") or 0) or None
    pw = request.form.get("password") or ""
    if not student_id or not pw:
        flash("الرجاء تعبئة البيانات.", "danger")
        return redirect(url_for("chairman.users"))
    if User.query.filter_by(student_id=student_id).first():
        flash("رقم الطالب موجود.", "danger")
        return redirect(url_for("chairman.users"))
    u = User(username=f"student_{student_id}", name_ar=name_ar or f"طالب {student_id}", role="student", student_id=student_id, teacher_id=teacher_id)
    u.set_password(pw)
    db.session.add(u)
    db.session.commit()
    flash("تم إنشاء الطالب وإضافته للقائمة.", "success")
    return redirect(url_for("chairman.users"))

@bp.get("/skills")
@login_required
def skills():
    _require_chairman()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    return render_template("chairman_skills.html", skills=skills)

@bp.post("/skills")
@login_required
def skill_create():
    _require_chairman()
    name_ar = request.form.get("name_ar") or ""
    desc = request.form.get("description_ar") or ""
    order = int(request.form.get("order") or 0)
    pass_th = int(request.form.get("pass_threshold") or 60)
    tl = int(request.form.get("time_limit_min") or 10)
    s = Skill(name_ar=name_ar, description_ar=desc, order=order, pass_threshold=pass_th, time_limit_min=tl)
    db.session.add(s)
    db.session.commit()
    flash("تم إضافة المهارة.", "success")
    return redirect(url_for("chairman.skills"))

@bp.route("/skills/<int:skill_id>/edit", methods=["GET","POST"])
@login_required
def skill_edit(skill_id: int):
    _require_chairman()
    s = Skill.query.get_or_404(skill_id)
    if request.method == "GET":
        return render_template("skill_form.html", skill=s, action=url_for("chairman.skill_edit", skill_id=s.id))
    s.name_ar = request.form.get("name_ar") or s.name_ar
    s.description_ar = request.form.get("description_ar") or s.description_ar
    s.order = int(request.form.get("order") or s.order or 0)
    s.pass_threshold = int(request.form.get("pass_threshold") or s.pass_threshold or 60)
    s.time_limit_min = int(request.form.get("time_limit_min") or s.time_limit_min or 10)
    db.session.commit()
    flash("تم تحديث المهارة.", "success")
    return redirect(url_for("chairman.skills"))

@bp.post("/skills/<int:skill_id>/delete")
@login_required
def skill_delete(skill_id: int):
    _require_chairman()
    # delete dependents to avoid FK issues in Postgres
    from app.models import Attempt, Report, Remediation, ImportBatch, ImportItem, StudentSkillStatus
    Question.query.filter_by(skill_id=skill_id).delete(synchronize_session=False)

    attempt_ids = [a.id for a in Attempt.query.filter_by(skill_id=skill_id).all()]
    if attempt_ids:
        Report.query.filter(Report.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)
    Attempt.query.filter_by(skill_id=skill_id).delete(synchronize_session=False)
    Remediation.query.filter_by(skill_id=skill_id).delete(synchronize_session=False)
    StudentSkillStatus.query.filter_by(skill_id=skill_id).delete(synchronize_session=False)

    batch_ids = [b.id for b in ImportBatch.query.filter_by(skill_id=skill_id).all()]
    if batch_ids:
        ImportItem.query.filter(ImportItem.batch_id.in_(batch_ids)).delete(synchronize_session=False)
    ImportBatch.query.filter_by(skill_id=skill_id).delete(synchronize_session=False)

    s = Skill.query.get_or_404(skill_id)
    db.session.delete(s)
    db.session.commit()
    flash("تم حذف المهارة.", "success")
    return redirect(url_for("chairman.skills"))

@bp.get("/questions")
@login_required
def question_tool():
    _require_chairman()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    skill_id = request.args.get("skill_id", type=int)
    qs = Question.query.filter_by(skill_id=skill_id).order_by(Question.id.desc()).all() if skill_id else []
    return render_template("chairman_questions.html", skills=skills, skill_id=skill_id, questions=qs)

@bp.route("/questions/new", methods=["GET","POST"])
@login_required
def question_new():
    _require_chairman()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    if request.method == "GET":
        return render_template("question_form.html", skills=skills, q=None, action=url_for("chairman.question_new"))
    # create
    skill_id = int(request.form.get("skill_id") or 0)
    qtype = request.form.get("qtype") or "mcq_single"
    prompt_ar = request.form.get("prompt_ar") or ""
    choices_raw = request.form.get("choices_ar") or ""
    correct_raw = request.form.get("correct") or ""

    options = None
    if qtype in ("mcq_single","mcq_multi","tf","video_checkpoint"):
        ch=[]
        for line in choices_raw.splitlines():
            line=line.strip()
            if not line: continue
            if "|" in line:
                cid, txt = line.split("|",1)
            else:
                cid=str(len(ch)+1)
                txt=line
            ch.append({"id":cid.strip(), "text_ar":txt.strip()})
        options={"choices":ch} if ch else None

    correct_json={"answers":[c.strip() for c in correct_raw.split(",") if c.strip()]} if correct_raw else {"answers":[]}
    media=None; meta=None
    if qtype=="video_checkpoint":
        media={"video_url": request.form.get("video_url") or ""}
        meta={"checkpoint_seconds": int(request.form.get("checkpoint_seconds") or 0)}
    q = Question(skill_id=skill_id, qtype=qtype, prompt_ar=prompt_ar, options_json=options, correct_json=correct_json, media_json=media, meta_json=meta)
    db.session.add(q)
    db.session.commit()
    flash("تم إضافة السؤال.", "success")
    return redirect(url_for("chairman.question_tool", skill_id=skill_id))

@bp.route("/questions/<int:question_id>/edit", methods=["GET","POST"])
@login_required
def question_edit(question_id: int):
    _require_chairman()
    q = Question.query.get_or_404(question_id)
    skills = Skill.query.order_by(Skill.order.asc()).all()
    if request.method == "GET":
        return render_template("question_form.html", skills=skills, q=q, action=url_for("chairman.question_edit", question_id=q.id))
    # update
    q.skill_id = int(request.form.get("skill_id") or q.skill_id)
    q.qtype = request.form.get("qtype") or q.qtype
    q.prompt_ar = request.form.get("prompt_ar") or q.prompt_ar
    # keep simple: parse choices/correct same as teacher
    choices_raw = request.form.get("choices_ar") or ""
    correct_raw = request.form.get("correct") or ""
    options = None
    if q.qtype in ("mcq_single","mcq_multi","tf","video_checkpoint"):
        ch=[]
        for line in choices_raw.splitlines():
            line=line.strip()
            if not line: continue
            if "|" in line:
                cid, txt = line.split("|",1)
            else:
                cid=str(len(ch)+1)
                txt=line
            ch.append({"id":cid.strip(), "text_ar":txt.strip()})
        options={"choices":ch} if ch else None
    q.options_json = options
    q.correct_json = {"answers":[c.strip() for c in correct_raw.split(",") if c.strip()]} if correct_raw else {"answers":[]}
    if q.qtype=="video_checkpoint":
        q.media_json={"video_url": request.form.get("video_url") or ""}
        q.meta_json={"checkpoint_seconds": int(request.form.get("checkpoint_seconds") or 0)}
    else:
        q.media_json=None; q.meta_json=None
    db.session.commit()
    flash("تم حفظ السؤال.", "success")
    return redirect(url_for("chairman.question_tool", skill_id=q.skill_id))

@bp.post("/questions/<int:question_id>/delete")
@login_required
def question_delete(question_id: int):
    _require_chairman()
    q = Question.query.get_or_404(question_id)
    sid = q.skill_id
    db.session.delete(q)
    db.session.commit()
    flash("تم حذف السؤال.", "success")
    return redirect(url_for("chairman.question_tool", skill_id=sid))
