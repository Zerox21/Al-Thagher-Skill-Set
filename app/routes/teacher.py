from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Skill, StudentSkillStatus, Remediation, Media, Report, Question
from app.storage import save_upload
from app.utils import iso_week_key, ensure_allowed_ext

bp = Blueprint("teacher", __name__)

ALLOWED_MEDIA_EXT = {".png",".jpg",".jpeg",".gif",".webp",".mp4",".webm",".pdf",".docx",".ppt",".pptx"}
ALLOWED_REMEDIATION_EXT = {".png",".jpg",".jpeg",".gif",".webp",".mp4",".webm",".pdf",".docx",".ppt",".pptx",".xls",".xlsx",".zip"}

def _require_teacher():
    if current_user.role != "teacher":
        abort(403)

@bp.get("/dashboard")
@login_required
def dashboard():
    _require_teacher()
    students = User.query.filter_by(role="student", teacher_id=current_user.id).all()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    reports = Report.query.filter_by(teacher_id=current_user.id).order_by(Report.created_at.desc()).all()
    return render_template("teacher_dashboard.html", students=students, skills=skills, reports=reports)

@bp.get("/skills")
@login_required
def skills():
    _require_teacher()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    return render_template("teacher_skills.html", skills=skills)

@bp.post("/skills")
@login_required
def skill_create():
    _require_teacher()
    name_ar = request.form.get("name_ar") or ""
    desc = request.form.get("description_ar") or ""
    order = int(request.form.get("order") or 0)
    pass_th = int(request.form.get("pass_threshold") or 60)
    tl = int(request.form.get("time_limit_min") or 10)
    s = Skill(name_ar=name_ar, description_ar=desc, order=order, pass_threshold=pass_th, time_limit_min=tl)
    db.session.add(s)
    db.session.commit()
    flash("تم إضافة المهارة.", "success")
    return redirect(url_for("teacher.skills"))

@bp.route("/skills/<int:skill_id>/edit", methods=["GET","POST"])
@login_required
def skill_edit(skill_id: int):
    _require_teacher()
    s = Skill.query.get_or_404(skill_id)
    if request.method == "GET":
        return render_template("skill_form.html", skill=s, action=url_for("teacher.skill_edit", skill_id=s.id))
    s.name_ar = request.form.get("name_ar") or s.name_ar
    s.description_ar = request.form.get("description_ar") or s.description_ar
    s.order = int(request.form.get("order") or s.order or 0)
    s.pass_threshold = int(request.form.get("pass_threshold") or s.pass_threshold or 60)
    s.time_limit_min = int(request.form.get("time_limit_min") or s.time_limit_min or 10)
    db.session.commit()
    flash("تم تحديث المهارة.", "success")
    return redirect(url_for("teacher.skills"))

@bp.post("/skills/<int:skill_id>/delete")
@login_required
def skill_delete(skill_id: int):
    _require_teacher()
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
    return redirect(url_for("teacher.skills"))

@bp.post("/student/<int:student_id>/unlock")
@login_required
def unlock_skill(student_id: int):
    _require_teacher()
    student = User.query.filter_by(id=student_id, role="student", teacher_id=current_user.id).first_or_404()
    skill_id = int(request.form.get("skill_id") or 0)
    status = StudentSkillStatus.query.filter_by(student_id=student.id, skill_id=skill_id).first()
    if not status:
        status = StudentSkillStatus(student_id=student.id, skill_id=skill_id, unlocked=True)
        db.session.add(status)
    else:
        status.unlocked = True
    db.session.commit()
    flash("تم فتح المهارة للطالب.", "success")
    return redirect(url_for("teacher.dashboard"))

@bp.post("/student/<int:student_id>/lock")
@login_required
def lock_skill(student_id: int):
    _require_teacher()
    student = User.query.filter_by(id=student_id, role="student", teacher_id=current_user.id).first_or_404()
    skill_id = int(request.form.get("skill_id") or 0)
    status = StudentSkillStatus.query.filter_by(student_id=student.id, skill_id=skill_id).first()
    if status:
        status.unlocked = False
        db.session.commit()
    flash("تم قفل المهارة.", "success")
    return redirect(url_for("teacher.dashboard"))

@bp.post("/student/<int:student_id>/allow-extra-attempt")
@login_required
def allow_extra_attempt(student_id: int):
    _require_teacher()
    student = User.query.filter_by(id=student_id, role="student", teacher_id=current_user.id).first_or_404()
    skill_id = int(request.form.get("skill_id") or 0)
    wk = iso_week_key()
    status = StudentSkillStatus.query.filter_by(student_id=student.id, skill_id=skill_id).first()
    if not status:
        status = StudentSkillStatus(student_id=student.id, skill_id=skill_id, unlocked=True, extra_attempt_week=wk)
        db.session.add(status)
    else:
        status.extra_attempt_week = wk
    db.session.commit()
    flash("تم السماح بمحاولة إضافية لهذا الأسبوع.", "success")
    return redirect(url_for("teacher.dashboard"))

@bp.get("/remediation")
@login_required
def remediation_page():
    _require_teacher()
    students = User.query.filter_by(role="student", teacher_id=current_user.id).all()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    rems = Remediation.query.filter_by(teacher_id=current_user.id).order_by(Remediation.created_at.desc()).all()
    return render_template("teacher_remediation.html", students=students, skills=skills, remediations=rems)

@bp.post("/remediation")
@login_required
def remediation_post():
    _require_teacher()
    student_id = int(request.form.get("student_id") or 0)
    skill_id = int(request.form.get("skill_id") or 0)
    notes = request.form.get("notes_ar") or ""
    file = request.files.get("file")
    if not file:
        flash("الرجاء اختيار ملف.", "danger")
        return redirect(url_for("teacher.remediation_page"))
    if not ensure_allowed_ext(file.filename or "", ALLOWED_REMEDIATION_EXT):
        flash("امتداد الملف غير مسموح.", "danger")
        return redirect(url_for("teacher.remediation_page"))

    student = User.query.filter_by(id=student_id, role="student", teacher_id=current_user.id).first()
    if not student:
        flash("طالب غير صحيح.", "danger")
        return redirect(url_for("teacher.remediation_page"))

    saved = save_upload(file, "remediation")
    m = Media(filename=saved["filename"], mime=saved["mime"], url="", storage_key=saved["storage_key"], uploaded_by=current_user.id)
    db.session.add(m)
    db.session.commit()
    m.url = f"/media/file/{m.id}"
    db.session.commit()

    rem = Remediation(teacher_id=current_user.id, student_id=student.id, skill_id=skill_id, notes_ar=notes, file_media_id=m.id)
    db.session.add(rem)
    db.session.commit()
    flash("تم رفع الخطة العلاجية.", "success")
    return redirect(url_for("teacher.remediation_page"))

@bp.get("/reports")
@login_required
def reports():
    _require_teacher()
    reports = Report.query.filter_by(teacher_id=current_user.id).order_by(Report.created_at.desc()).all()
    return render_template("teacher_reports.html", reports=reports)

@bp.get("/questions")
@login_required
def question_tool():
    _require_teacher()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    skill_id = request.args.get("skill_id", type=int)
    qs = Question.query.filter_by(skill_id=skill_id).order_by(Question.id.desc()).all() if skill_id else []
    return render_template("teacher_questions.html", skills=skills, skill_id=skill_id, questions=qs)

@bp.route("/questions/new", methods=["GET","POST"])
@login_required
def question_new():
    _require_teacher()
    skills = Skill.query.order_by(Skill.order.asc()).all()
    if request.method == "GET":
        return render_template("question_form.html", skills=skills, q=None, action=url_for("teacher.question_new"))

    return _upsert_question()

@bp.route("/questions/<int:question_id>/edit", methods=["GET","POST"])
@login_required
def question_edit(question_id: int):
    _require_teacher()
    q = Question.query.get_or_404(question_id)
    skills = Skill.query.order_by(Skill.order.asc()).all()
    if request.method == "GET":
        return render_template("question_form.html", skills=skills, q=q, action=url_for("teacher.question_edit", question_id=q.id))
    return _upsert_question(q)

@bp.post("/questions/<int:question_id>/delete")
@login_required
def question_delete(question_id: int):
    _require_teacher()
    q = Question.query.get_or_404(question_id)
    skill_id = q.skill_id
    db.session.delete(q)
    db.session.commit()
    flash("تم حذف السؤال.", "success")
    return redirect(url_for("teacher.question_tool", skill_id=skill_id))

def _upsert_question(q: Question | None = None):
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
            if not line: 
                continue
            if "|" in line:
                cid, txt = line.split("|",1)
            else:
                cid=str(len(ch)+1)
                txt=line
            ch.append({"id":cid.strip(), "text_ar":txt.strip()})
        options={"choices":ch} if ch else None

    correct_json={"answers":[c.strip() for c in correct_raw.split(",") if c.strip()]} if correct_raw else {"answers":[]}
    meta=None
    media=None
    if qtype=="video_checkpoint":
        media={"video_url": request.form.get("video_url") or ""}
        meta={"checkpoint_seconds": int(request.form.get("checkpoint_seconds") or 0)}

    if q is None:
        q = Question(skill_id=skill_id, qtype=qtype, prompt_ar=prompt_ar)
        db.session.add(q)
    q.skill_id = skill_id
    q.qtype = qtype
    q.prompt_ar = prompt_ar
    q.options_json = options
    q.correct_json = correct_json
    q.media_json = media
    q.meta_json = meta

    db.session.commit()
    flash("تم حفظ السؤال.", "success")
    return redirect(url_for("teacher.question_tool", skill_id=skill_id))
