"""Generate all AMSDP M3 frontend pages."""
import os, sys

ROOT = "/home/shomonrobie/amsdp/frontend"


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  {path}")


# === global.css
write("styles/global.css", """/* AMSDP Frontend — Global Styles */
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:Helvetica,Arial,sans-serif; background:#f0f2f5; color:#333; line-height:1.5; }
a { color:#1a5c7a; text-decoration:none; }
button { cursor:pointer; }
input,select,textarea { width:100%; padding:0.5rem; border:1px solid #ccc; border-radius:4px; font-size:0.9rem; }
label { display:block; margin-bottom:0.25rem; font-weight:600; font-size:0.85rem; }
table { width:100%; border-collapse:collapse; background:#fff; border-radius:6px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
th { background:#1a5c7a; color:#fff; padding:0.6rem; text-align:left; font-size:0.85rem; }
td { padding:0.5rem 0.6rem; border-bottom:1px solid #eee; font-size:0.85rem; }
tr:hover { background:#f8faff; }
.btn { display:inline-block; background:#1a5c7a; color:#fff; border:none; padding:0.45rem 1rem; border-radius:4px; font-size:0.85rem; }
.btn:hover { background:#134b63; }
.btn-sm { padding:0.3rem 0.6rem; font-size:0.8rem; }
.btn-danger { background:#c62828; }
.btn-outline { background:transparent; color:#1a5c7a; border:1px solid #1a5c7a; }
.card { background:#fff; border-radius:6px; padding:1rem; box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:1rem; }
.error { color:#c62828; font-size:0.85rem; padding:0.5rem; background:#fbe9e7; border-radius:4px; margin:0.5rem 0; }
.success { color:#2e7d32; font-size:0.85rem; padding:0.5rem; background:#e8f5e9; border-radius:4px; margin:0.5rem 0; }
.loading { text-align:center; padding:2rem; color:#888; }
.empty { text-align:center; padding:2rem; color:#999; font-style:italic; }
.modal-overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:center; z-index:100; }
.modal { background:#fff; border-radius:8px; padding:1.5rem; min-width:400px; max-width:600px; max-height:80vh; overflow-y:auto; }
.modal h3 { margin-bottom:1rem; color:#1a5c7a; }
.form-group { margin-bottom:0.75rem; }
.form-actions { display:flex; gap:0.5rem; justify-content:flex-end; margin-top:1rem; }
.page-title { color:#1a5c7a; margin-bottom:1rem; font-size:1.2rem; }
.flex { display:flex; gap:0.5rem; align-items:center; }
.flex-wrap { flex-wrap:wrap; }
.justify-between { justify-content:space-between; }
.mb-1 { margin-bottom:0.5rem; }
.mb-2 { margin-bottom:1rem; }
""")
print("Styles written")