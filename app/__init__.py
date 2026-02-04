 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app/__init__.py b/app/__init__.py
index 19881d0b53eacaf8315405faf7dd1567187675db..77cbae8a598c978b76b60b47cbc0e3d60ec4d73d 100644
--- a/app/__init__.py
+++ b/app/__init__.py
@@ -44,36 +44,39 @@ def create_app():
     # Jinja helpers
     from .filters import bp as filters_bp
     app.register_blueprint(filters_bp)
 
     from .routes.auth import bp as auth_bp
     from .routes.student import bp as student_bp
     from .routes.teacher import bp as teacher_bp
     from .routes.chairman import bp as chairman_bp
     from .routes.files import bp as files_bp
 
     app.register_blueprint(auth_bp)
     app.register_blueprint(student_bp, url_prefix="/student")
     app.register_blueprint(teacher_bp, url_prefix="/teacher")
     app.register_blueprint(chairman_bp, url_prefix="/chairman")
     app.register_blueprint(files_bp, url_prefix="/files")
 
     @app.context_processor
     def inject_brand():
         return {
             'brand': {
                 'name': app.config.get('BRAND_NAME'),
                 'tagline': app.config.get('BRAND_TAGLINE'),
                 'primary_color': app.config.get('BRAND_PRIMARY_COLOR'),
                 'logo_path': app.config.get('BRAND_LOGO_PATH'),
                 'favicon_path': app.config.get('BRAND_FAVICON_PATH'),
-            }
+            },
+            'app_version': app.config.get('APP_VERSION'),
+            'app_locale': app.config.get('APP_LOCALE'),
+            'app_text_dir': app.config.get('APP_TEXT_DIR'),
         }
 
     with app.app_context():
         db.create_all()
         from .migrate import ensure_schema
         ensure_schema()
         from .seed import ensure_seed_data
         ensure_seed_data()
 
     return app
 
EOF
)
