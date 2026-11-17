"""Fix breadcrumbs JSX attribute braces in wrapped pages."""
import os, re

for f in ["patients.js", "doctors.js", "staff.js", "orgs.js", "branches.js", "schedules.js", "appointments.js"]:
    p = os.path.join("/home/shomonrobie/amsdp/frontend/pages", f)
    c = open(p, encoding="utf-8").read()
    new = re.sub(r"breadcrumbs=\[\{ label: T\(\s*'t'\s*\) \}\]>",
                 "breadcrumbs={[{ label: T('t') }]}>", c)
    if new != c:
        open(p, "w", encoding="utf-8").write(new)
        print(f, "fixed breadcrumbs braces")
    else:
        print(f, "no change")