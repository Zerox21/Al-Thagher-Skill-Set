 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/tests/test_smoke.py b/tests/test_smoke.py
new file mode 100644
index 0000000000000000000000000000000000000000..7252c68d0976c8334489a17271d4b09b6c8a678a
--- /dev/null
+++ b/tests/test_smoke.py
@@ -0,0 +1,2 @@
+def test_smoke():
+    assert True
 
EOF
)
