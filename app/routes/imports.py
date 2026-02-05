from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Skill, ImportBatch, ImportItem, Question
from app.storage import save_upload
from app.utils import ensure_allowed_ext
import os
import fitz
from docx import Document

bp = Blueprint("imports", __name__)

ALLOWED_IMPORT_EXT = {".pdf", ".docx"}

def _can_manage():
    return current_user.is_authenticated and current_user.role in ("chairman","teacher")

@bp.get("/")
@login_required
def index():
    if not _can_manage():
        abort(403)
    skills = Skill.query.order_by(Skill.order.asc()).all()
    batches = ImportBatch.query.order_by(ImportBatch.id.desc()).all()
    return render_template("import_index.html", skills=skills, batches=batches)

@bp.post("/upload")
@login_required
def upload():
    if not _can_manage():
        abort(403)
    f = request.files.get("file")
    skill_id = int(request.form.get("skill_id") or 0)
    if not f or not skill_id:
        flash("الرجاء اختيار ملف ومهارة.", "danger")
        return redirect(url_for("imports.index"))

    if not ensure_allowed_ext(f.filename or "", ALLOWED_IMPORT_EXT):
        flash("الملف يجب أن يكون PDF أو DOCX.", "danger")
        return redirect(url_for("imports.index"))

    lower = (f.filename or "").lower()
    source_type = "pdf" if lower.endswith(".pdf") else "docx"
    saved = save_upload(f, "imports")

    batch = ImportBatch(created_by=current_user.id, skill_id=skill_id, filename=os.path.basename(f.filename), source_type=source_type)
    db.session.add(batch)
    db.session.commit()

    blocks = []
    if source_type == "docx":
        doc = Document(saved["storage_key"])
        for p in doc.paragraphs:
            txt = (p.text or "").strip()
            if txt:
                blocks.append(txt)
    else:
        doc = fitz.open(saved["storage_key"])
        for page in doc:
            txt = (page.get_text() or "").strip()
            for part in [x.strip() for x in txt.split("\n\n") if x.strip()]:
                blocks.append(part)

    if not blocks:
        blocks = ["(لم يتم استخراج نص. الرجاء إدخال الأسئلة يدوياً)"]

    for b in blocks[:200]:
        db.session.add(ImportItem(batch_id=batch.id, raw_text=b))
    db.session.commit()

    flash("تم إنشاء مسودة استيراد. الرجاء مراجعة البنود.", "success")
    return redirect(url_for("imports.review", batch_id=batch.id))

@bp.get("/<int:batch_id>/review")
@login_required
def review(batch_id: int):
    if not _can_manage():
        abort(403)
    batch = ImportBatch.query.get_or_404(batch_id)
    items = ImportItem.query.filter_by(batch_id=batch.id).order_by(ImportItem.id.asc()).all()
    skill = Skill.query.get(batch.skill_id)
    return render_template("import_review.html", batch=batch, items=items, skill=skill)

@bp.post("/<int:batch_id>/apply")
@login_required
def apply(batch_id: int):
    if not _can_manage():
        abort(403)
    batch = ImportBatch.query.get_or_404(batch_id)
    items = ImportItem.query.filter_by(batch_id=batch.id).order_by(ImportItem.id.asc()).all()
    created = 0
    for it in items:
        qtype = request.form.get(f"type_{it.id}") or "short"
        prompt = request.form.get(f"prompt_{it.id}") or it.raw_text
        choices_raw = request.form.get(f"choices_{it.id}") or ""
        correct_raw = request.form.get(f"correct_{it.id}") or ""
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
            options = {"choices":ch} if ch else None
        correct = {"answers":[c.strip() for c in correct_raw.split(",") if c.strip()]} if correct_raw else {"answers":[]}
        db.session.add(Question(skill_id=batch.skill_id, qtype=qtype, prompt_ar=prompt, options_json=options, correct_json=correct))
        created += 1
    batch.status = "completed"
    db.session.commit()
    flash(f"تم اعتماد الاستيراد وإنشاء {created} سؤالاً.", "success")
    return redirect(url_for("imports.index"))
