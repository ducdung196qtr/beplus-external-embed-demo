"""Screenshot the WordPress admin 'Embed Script' screen for review."""
import os
import sys

from playwright.sync_api import sync_playwright

SITE = "http://160.250.135.47:8080"
USER = "admin"
PWD = "Beplus!Test2026"
CHROME = os.environ.get(
    "QA_CHROME",
    "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome",
)
OUT = "/root/beplus-external-embed-demo/qa-artifacts"


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        p = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
        p.goto(f"{SITE}/wp-login.php", wait_until="domcontentloaded")
        p.fill("#user_login", USER)
        p.fill("#user_pass", PWD)
        p.click("#wp-submit")
        p.wait_for_load_state("domcontentloaded")
        p.goto(f"{SITE}/wp-admin/admin.php?page=beplus-site-assistant-embed",
               wait_until="networkidle")
        p.wait_for_selector(".bsa-embed-card", timeout=30_000)
        p.wait_for_timeout(1200)
        shot = f"{OUT}/admin-embed-script.png"
        p.screenshot(path=shot, full_page=True)

        snippet = p.eval_on_selector_all(
            "textarea[readonly]", "els => els.map(e => e.value).filter(v => v.includes('data-bsa-key'))"
        )
        print("screenshot:", shot)
        print("snippet:", snippet[0] if snippet else "(none)")
        html = p.content()
        print("submenu present:", "Embed Script" in html)
        b.close()


if __name__ == "__main__":
    sys.exit(main())
