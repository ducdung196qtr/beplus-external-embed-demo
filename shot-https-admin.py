"""Capture the Embed Script screen as it looks over the new stable HTTPS."""
from playwright.sync_api import sync_playwright

from bsa_endpoints import wp_url

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
USER, PWD = "admin", "Beplus!Test2026"
WP = wp_url()

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1440, "height": 1150})
    p.goto(f"{WP}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")
    p.goto(f"{WP}/wp-admin/admin.php?page=beplus-site-assistant-embed", wait_until="networkidle")

    # open the share panel so the copyable script is on screen
    details = p.locator("details.bsa-embed-share").first
    if details.count():
        details.evaluate("el => el.open = true")
    p.wait_for_timeout(600)
    p.screenshot(path="/root/beplus-external-embed-demo/qa-artifacts/https-embed-script.png", full_page=True)

    text = p.inner_text("body")
    print("warning shown over https :", "plain HTTP" in text)
    print("snippet host in page     :", "https://160-250-135-47.sslip.io" in text)
    b.close()
