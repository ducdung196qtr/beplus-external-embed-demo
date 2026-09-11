"""Close the loop: the snippet you copy from wp-admin must be the one that runs.

1. Log in to wp-admin over HTTPS and read the snippet the screen produces.
2. Read the snippet the deployed landing page actually loads.
3. They must agree on src, data-bsa-site and data-bsa-key — otherwise "copy
   this script" is a promise the demo does not keep.
"""
import json
import re
import subprocess

from playwright.sync_api import sync_playwright

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
USER, PWD = "admin", "Beplus!Test2026"
from bsa_endpoints import wp_url

TUNNEL = wp_url()
DEMO = "https://beplus-external-embed-demo.vercel.app/"


def attrs(tag):
    out = {}
    for k in ("src", "data-bsa-site", "data-bsa-key", "data-bsa-api"):
        m = re.search(k + r'="([^"]*)"', tag)
        if m:
            out[k] = m.group(1)
    return out


with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    p = b.new_page()
    p.goto(f"{TUNNEL}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")
    p.goto(f"{TUNNEL}/wp-admin/admin.php?page=beplus-site-assistant-embed", wait_until="networkidle")
    admin_snippet = p.evaluate(
        """() => {
            const d = document.querySelector('details.bsa-embed-share');
            const t = d && d.querySelector('textarea, code, pre');
            return t ? (t.value || t.textContent || '') : '';
        }"""
    )

    # The landing page uses next/script with strategy="afterInteractive", which
    # appends the tag after hydration — so wait for it rather than reading the
    # initial HTML, and confirm the browser actually fetched it.
    p2 = b.new_page()
    fetched = []
    p2.on("request", lambda r: fetched.append(r.url))
    p2.goto(DEMO, wait_until="load")
    # a <script> element is never "visible", so wait for attachment
    p2.wait_for_selector('script[src*="embed.js"]', state="attached", timeout=30000)
    p2.wait_for_timeout(2500)
    demo_tags = p2.evaluate(
        """() => [...document.querySelectorAll('script[src*="embed.js"]')].map(s => s.outerHTML)"""
    )
    print("demo requested embed.js:", any("embed.js" in u for u in fetched))
    b.close()

admin = attrs(admin_snippet)
demo = attrs(demo_tags[0]) if demo_tags else {}

print(json.dumps({"admin_snippet": admin, "demo_script": demo}, indent=2))

ok = True
for k in ("src", "data-bsa-site", "data-bsa-key"):
    if not admin.get(k):
        ok = False
        print(f"FAIL admin snippet has no {k}")
    elif admin.get(k) != demo.get(k):
        ok = False
        print(f"FAIL {k} differs:\n  admin={admin.get(k)}\n  demo ={demo.get(k)}")
    else:
        print(f"OK   {k} matches")
if not admin.get("src", "").startswith("https://"):
    ok = False
    print("FAIL admin snippet is not https")
print("LOOP:", "PASS" if ok else "FAIL")
