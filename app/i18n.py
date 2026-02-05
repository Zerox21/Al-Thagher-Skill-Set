from flask import session

STRINGS = {
  "app_name": {"ar":"منصة قياس المهارات - مدرسة الثغر", "en":"Al Thaghr Skill Set"},
  "login": {"ar":"تسجيل الدخول", "en":"Login"},
  "logout": {"ar":"تسجيل الخروج", "en":"Logout"},
  "home": {"ar":"الرئيسية", "en":"Home"},
  "dashboard": {"ar":"لوحة التحكم", "en":"Dashboard"},
  "users": {"ar":"المستخدمون", "en":"Users"},
  "skills": {"ar":"المهارات", "en":"Skills"},
  "questions": {"ar":"الأسئلة", "en":"Questions"},
  "media": {"ar":"الوسائط", "en":"Media"},
  "import_questions": {"ar":"استيراد أسئلة", "en":"Import Questions"},
  "reports": {"ar":"التقارير", "en":"Reports"},
  "save": {"ar":"حفظ", "en":"Save"},
  "upload": {"ar":"رفع", "en":"Upload"},
  "download": {"ar":"تحميل", "en":"Download"},
  "start_test": {"ar":"بدء الاختبار", "en":"Start Test"},
  "submit_test": {"ar":"إرسال الاختبار", "en":"Submit"},
  "time_left": {"ar":"الوقت المتبقي", "en":"Time left"},
  "select_teacher": {"ar":"اختر المعلم", "en":"Select Teacher"},
  "first_time_teacher": {"ar":"هذه أول مرة لك، الرجاء اختيار معلمك.", "en":"First login: please select your teacher."},
  "remediation": {"ar":"خطة علاجية", "en":"Remediation"},
  "language": {"ar":"اللغة", "en":"Language"},
}

def get_lang():
    return session.get("lang", "ar")

def set_lang(code: str):
    session["lang"] = "en" if code == "en" else "ar"

def t(key: str) -> str:
    lang = get_lang()
    if key in STRINGS:
        return STRINGS[key].get(lang) or STRINGS[key].get("ar") or key
    return key
