"""The HTTP warning must appear where it is true, and nowhere else.

Same plugin, same page, two addresses:
  http://160.250.135.47:8080     -> warning shown, script src is http://
  https://<tunnel>               -> no warning, script src is https://
"""
import json
import re
import subprocess

from playwright.sync_api import sync_playwright

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
USER, PWD = "admin", "Beplus!Test2026"
OUT = "/root/beplus-external-embed-demo/qa-artifacts"
from bsa_endpoints import wp_url

TUNNEL = wp_url()


def check(pw, origin, label):
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    errors = []
    p.on("pageerror", lambda e: errors.append(str(e)))
    r = {"label": label, "origin": origin}

    p.goto(f"{origin}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")
    p.goto(f"{origin}/wp-admin/admin.php?page=beplus-site-assistant-embed", wait_until="networkidle")

    body = p.inner_text(".bsa-embed-wrap")
    r["warning_shown"] = "will not load on an HTTPS website" in body
    r["warning_names_address"] = "plain HTTP" in body

    # the script that a copy would yield, read from the page itself
    snippet = p.evaluate(
        """() => {
            const d = document.querySelector('details.bsa-embed-share');
            const t = d && d.querySelector('textarea, code, pre');
            return t ? (t.value || t.textContent || '') : '';
        }"""
    )
    m = re.search(r'src="([^"]+)"', snippet)
    r["snippet_src"] = m.group(1) if m else ""
    r["snippet_is_https"] = r["snippet_src"].startswith("https://")
    r["errors"] = errors
    p.screenshot(path=f"{OUT}/insecure-warning-{label}.png", full_page=True)
    b.close()
    return r


with sync_playwright() as pw:
    over_http = check(pw, "http://160.250.135.47:8080", "http")
    over_https = check(pw, TUNNEL, "https")

print(json.dumps({"over_http": over_http, "over_https": over_https}, indent=2))

ok = True
for name, got, want in [
    ("http  : warning shown", over_http["warning_shown"], True),
    ("http  : snippet src is http", over_http["snippet_is_https"], False),
    ("https : no warning", over_https["warning_shown"], False),
    ("https : snippet src is https", over_https["snippet_is_https"], True),
]:
    if got != want:
        ok = False
        print(f"FAIL {name}: got={got!r} want={want!r}")
for r in (over_http, over_https):
    if r["errors"]:
        ok = False
        print(f"FAIL {r['label']} console errors:", r["errors"])
print("WARNING:", "PASS" if ok else "FAIL")
