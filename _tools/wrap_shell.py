"""Wrap AMSDP pages into the shared AppShell + RequireLogin."""
import os, re

PAGES_DIR = "/home/shomonrobie/amsdp/frontend/pages"

FILES = {
    "patients.js": "/patients",
    "doctors.js": "/doctors",
    "staff.js": "/staff",
    "orgs.js": "/orgs",
    "branches.js": "/branches",
    "schedules.js": "/schedules",
    "appointments.js": "/appointments",
}

for fname, route in FILES.items():
    path = os.path.join(PAGES_DIR, fname)
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()

    if "AppShell" in src:
        print(f"{fname}: already wrapped")
        continue

    # 1. Add shell imports after the first `import ... from ...;`/`import React`
    src = src.replace(
        "import React from 'react';",
        "import React from 'react';\nimport AppShell from '../components/AppShell';\nimport { RequireLogin } from '../components/ui/Alert';",
        1,
    )

    # 2. Replace the inline login-required guard with a null guard (RequireLogin handles UI)
    src = re.sub(
        r"if\(!u\.id\)return<div[^;]*?>[^;]*?<\/a><\/div>;",
        "if(!u.id)return null;",
        src,
        count=1,
    )

    open_wrapper = "<div style={{marginLeft:'200px',padding:'1rem 1.5rem'}}>"
    close_wrapper = "  </div>);"  # page-level closing inside return(...)

    if open_wrapper not in src:
        # try alternate spacing variants
        for alt in ["<div style={{ marginLeft:'200px',padding:'1rem 1.5rem' }}>",
                    "<div style={{marginLeft: '200px', padding: '1rem 1.5rem'}}>"]:
            if alt in src:
                src = src.replace(alt, open_wrapper, 1)
                break
        else:
            print(f"{fname}: outer wrapper not found, skip")
            continue

    bc = f"[{{ label: T('t') }}]"
    src = src.replace(
        open_wrapper,
        f"<RequireLogin><AppShell active=\"{route}\" breadcrumbs={bc}><div>",
        1,
    )
    # Replace final page-level close. The last non-indented '  </div>);' is ours.
    # Find last occurrence of close pattern followed by end.
    idx = src.rfind(close_wrapper)
    if idx != -1:
        src = src[:idx] + "  </div></AppShell></RequireLogin>);" + src[idx + len(close_wrapper):]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src)
    print(f"{fname}: wrapped -> {route}")

print("done")