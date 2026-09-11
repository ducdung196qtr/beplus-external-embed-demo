"""The www hint must render as real markup, not as escaped tags or a PHP notice."""
import json
import re

from playwright.sync_api import sync_playwright

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
USER, PWD = "admin", "Beplus!Test2026"
from bsa_endpoints import wp_url

TUNNEL = wp_url()

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    p.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    p.goto(f"{TUNNEL}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")
    p.goto(f"{TUNNEL}/wp-admin/admin.php?page=beplus-site-assistant-embed", wait_until="networkidle")

    form = p.locator("#bsa-site-url")
    card = form.locator("xpath=ancestor::div[contains(@class,'bsa-embed-card')]")
    text = card.inner_text()

    res = {
        "mentions_www": "www.example.com" in text,
        "mentions_apex": "example.com" in text,
        # <code> survived, so we printed markup rather than escaping it twice
        "code_tag_count": card.locator("code").count(),
        # a raw %1$s or a wp_error string means the printf went wrong
        "raw_placeholder": bool(re.search(r"%1\$s|WP_Error", text)),
        "php_notice": bool(re.search(r"Warning:|Notice:|Deprecated:", text)),
        "console_errors": errors,
    }
    card.screenshot(path="/root/beplus-external-embed-demo/qa-artifacts/embed-www-hint.png")
    b.close()

print(json.dumps(res, indent=2))
ok = (
    res["mentions_www"]
    and res["mentions_apex"]
    and res["code_tag_count"] >= 2
    and not res["raw_placeholder"]
    and not res["php_notice"]
    and not res["console_errors"]
)
print("WWW HINT:", "PASS" if ok else "FAIL")
