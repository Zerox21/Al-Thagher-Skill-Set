import datetime as dt
from sqlalchemy import UniqueConstraint
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name_ar = db.Column(db.String(200), nullable=False, default="")
    name_en = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # chairman|teacher|student
    email = db.Column(db.String(200), nullable=True)

    student_id = db.Column(db.String(50), unique=True, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    def set_password(self, pw: str):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash or "", pw)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0)
    pass_threshold = db.Column(db.Integer, default=60)
    time_limit_min = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class StudentSkillStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    unlocked = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    extra_attempt_week = db.Column(db.String(12), nullable=True)
    __table_args__ = (UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime = db.Column(db.String(100), nullable=True)
    url = db.Column(db.Text, nullable=False)
    storage_key = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    qtype = db.Column(db.String(50), nullable=False)
    prompt_ar = db.Column(db.Text, nullable=False)
    prompt_en = db.Column(db.Text, nullable=True)

    options_json = db.Column(db.JSON, nullable=True)
    correct_json = db.Column(db.JSON, nullable=True)
    media_json = db.Column(db.JSON, nullable=True)
    meta_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    week_key = db.Column(db.String(12), nullable=False)

    started_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    time_seconds = db.Column(db.Integer, default=0)

    score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="in_progress")
    answers_json = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    __table_args__ = (UniqueConstraint("student_id", "skill_id", "week_key", name="uq_attempt_week"),)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempt.id"), nullable=False, unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    url = db.Column(db.Text, nullable=False)
    storage_key = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class Remediation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    notes_ar = db.Column(db.Text, nullable=True)
    notes_en = db.Column(db.Text, nullable=True)
    file_media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class ImportBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)  # pdf|docx
    status = db.Column(db.String(20), default="draft")
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class ImportItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("import_batch.id"), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    suggested_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
