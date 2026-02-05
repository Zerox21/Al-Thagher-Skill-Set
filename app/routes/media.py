from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user
from app import db
from app.models import Media, Report, Attempt
from app.storage import save_upload
from app.utils import ensure_allowed_ext
import os

bp = Blueprint("media", __name__)

ALLOWED_MEDIA_EXT = {".png",".jpg",".jpeg",".gif",".webp",".mp4",".webm",".pdf",".docx",".ppt",".pptx"}

def _can_manage():
    return current_user.is_authenticated and current_user.role in ("chairman","teacher")

@bp.get("/")
@login_required
def library():
    if not _can_manage():
        abort(403)
    items = Media.query.order_by(Media.id.desc()).all()
    return render_template("media_library.html", items=items)

@bp.post("/upload")
@login_required
def upload():
    if not _can_manage():
        abort(403)
    f = request.files.get("file")
    if not f:
        flash("اختر ملفاً.", "danger")
        return redirect(url_for("media.library"))
    if not ensure_allowed_ext(f.filename or "", ALLOWED_MEDIA_EXT):
        flash("امتداد الملف غير مسموح.", "danger")
        return redirect(url_for("media.library"))
    saved = save_upload(f, "media")
    m = Media(filename=saved["filename"], mime=saved["mime"], url="", storage_key=saved["storage_key"], uploaded_by=current_user.id)
    db.session.add(m)
    db.session.commit()
    m.url = f"/media/file/{m.id}"
    db.session.commit()
    flash("تم رفع الوسائط.", "success")
    return redirect(url_for("media.library"))

@bp.get("/file/<int:media_id>")
@login_required
def file(media_id: int):
    m = Media.query.get_or_404(media_id)
    path = m.storage_key
    if path and os.path.exists(path):
        return send_file(path, as_attachment=False, download_name=m.filename)
    if m.url and m.url.startswith("http"):
        from flask import redirect
        return redirect(m.url)
    abort(404)

@bp.get("/report/<int:attempt_id>")
@login_required
def report(attempt_id: int):
    rep = Report.query.filter_by(attempt_id=attempt_id).first_or_404()
    attempt = Attempt.query.get(rep.attempt_id)
    if current_user.role == "teacher" and rep.teacher_id != current_user.id:
        abort(403)
    if current_user.role == "student" and attempt and attempt.student_id != current_user.id:
        abort(403)
    if current_user.role not in ("teacher","student","chairman"):
        abort(403)
    path = rep.storage_key
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=f"report_{attempt_id}.pdf")
    abort(404)
