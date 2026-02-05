# منصة قياس المهارات – مدرسة الثغر (Al Thaghr Skill Set)

مشروع Flask جاهز للنشر على Render/Heroku/Fly بواجهة عربية (RTL) مع خيار الإنجليزية.

## ✅ المميزات
- تسجيل دخول حسب الدور: **رئيس المدرسة / معلم / طالب**
- Allowlist: لا دخول للطلاب إلا إذا كان Student ID موجوداً بقاعدة البيانات
- محاولة واحدة لكل مهارة أسبوعياً (ISO Week)
- اختبارات مؤقّتة + استمرار المؤقت مع التحديث (Refresh)
- أنواع أسئلة متعددة + فيديو تفاعلي (Video Checkpoint)
- استيراد أسئلة من PDF/DOCX مع شاشة مراجعة قبل الاعتماد
- ملفات علاجية للطلاب الراسبين
- تقرير PDF تلقائي لكل محاولة + صندوق تقارير داخل حساب المعلم + بريد اختياري
- شريط تنقل علوي (Top Toolbar) حسب الدور + لغة AR/EN + APP_VERSION بالذيل

## تشغيل محلياً (اختياري)
```bash
cp .env.example .env
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app:create_app db upgrade
python seed.py
flask --app app:create_app run
```

## نشر على Render
**Build Command**
```bash
pip install -r requirements.txt && flask --app app:create_app db upgrade && python seed.py
```

**Start Command**
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

### أهم المتغيرات
- SECRET_KEY (مطلوب)
- APP_VERSION (للتأكد من النشر)
- DATABASE_URL (Postgres على Render)
- Optional: SMTP_* لإرسال البريد
- Optional: STORAGE_BACKEND=s3 مع S3_* لتخزين دائم

> ملاحظة: التخزين المحلي على Render قد يكون مؤقتاً. الأفضل استخدام S3 أو Render Persistent Disk.

## بيانات دخول تجريبية (بعد seed.py)
- chairman / Chairman@123
- teacher1 / Teacher@123
- Student: S1001 / Student@123

## Next Improvements
- بنك أسئلة + Tags + صعوبة
- Item analysis
- Proctoring-lite
- محرر رياضيات أفضل
- تخزين S3 كامل
- Audit logs وصلاحيات دقيقة


## كيف تعمل حدود المحاولات الأسبوعية؟
- النظام يستخدم **ISO Week** (مثال: 2026-W06).
- لا يمكن للطالب إجراء اختبار نفس المهارة أكثر من مرة في نفس الأسبوع.
- المعلم يمكنه السماح بمحاولة إضافية (سماح) لنفس الأسبوع عبر زر **سماح** في لوحة المعلم.

## الاستيراد من PDF/DOCX
1) اذهب إلى **استيراد أسئلة**
2) اختر مهارة ثم ارفع ملف PDF أو DOCX
3) ستظهر شاشة مراجعة: لكل بند اختر نوع السؤال، عدّل النص، أدخل الخيارات والإجابة الصحيحة
4) اضغط **اعتماد وإنشاء الأسئلة**

## إضافة/تعديل المهارات والأسئلة
- رئيس المدرسة: من **المهارات** و **الأسئلة**
- المعلم: من **المهارات** و **الأسئلة**
