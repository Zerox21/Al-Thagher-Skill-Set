from app import create_app, db
from app.models import User, Skill, Question, StudentSkillStatus

def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username="chairman").first():
            u = User(username="chairman", name_ar="رئيس المدرسة", role="chairman")
            u.set_password("Chairman@123")
            db.session.add(u)

        if not User.query.filter_by(username="teacher1").first():
            t = User(username="teacher1", name_ar="المعلم الأول", role="teacher", email="teacher1@example.com")
            t.set_password("Teacher@123")
            db.session.add(t)

        db.session.commit()
        teacher = User.query.filter_by(username="teacher1").first()

        if not User.query.filter_by(student_id="S1001").first():
            s = User(username="student_s1001", name_ar="طالب تجريبي", role="student", student_id="S1001", teacher_id=teacher.id)
            s.set_password("Student@123")
            db.session.add(s)
            db.session.commit()

        if not Skill.query.first():
            skill = Skill(name_ar="مهارة القراءة", description_ar="اختبار تجريبي لمهارة القراءة", order=1, pass_threshold=60, time_limit_min=10)
            db.session.add(skill)
            db.session.commit()

            q1 = Question(
                skill_id=skill.id,
                qtype="mcq_single",
                prompt_ar="اختر الإجابة الصحيحة: ٢ + ٢ = ؟ (يدعم LaTeX: \\(...\\))",
                options_json={"choices":[{"id":"a","text_ar":"3"},{"id":"b","text_ar":"4"},{"id":"c","text_ar":"5"}]},
                correct_json={"answers":["b"]},
            )
            q2 = Question(
                skill_id=skill.id,
                qtype="video_checkpoint",
                prompt_ar="شاهد الفيديو حتى الثانية 5 ثم أجب: ما لون الكلمة الظاهرة؟",
                media_json={"video_url":"https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"},
                meta_json={"checkpoint_seconds":5},
                options_json={"choices":[{"id":"a","text_ar":"أحمر"},{"id":"b","text_ar":"أزرق"}]},
                correct_json={"answers":["a"]},
            )
            db.session.add_all([q1,q2])
            db.session.commit()

        student = User.query.filter_by(student_id="S1001").first()
        skill = Skill.query.first()
        if student and skill and not StudentSkillStatus.query.filter_by(student_id=student.id, skill_id=skill.id).first():
            st = StudentSkillStatus(student_id=student.id, skill_id=skill.id, unlocked=True)
            db.session.add(st)
            db.session.commit()

        print("Seed completed.")
        print("Chairman: chairman / Chairman@123")
        print("Teacher: teacher1 / Teacher@123")
        print("Student: S1001 / Student@123")

if __name__ == "__main__":
    main()
