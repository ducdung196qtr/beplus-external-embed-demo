"""QA the reworked external-embed admin screen end to end.

Checks, per viewport:
  * Site Assistant -> Embed Script renders with the new website list
  * the bridge secret is NOT printed in full
  * the legacy External Embed card is gone from Settings
  * pressing "Pause connection" really stops the embed, and "Connect" restores it

Writes screenshots to qa-artifacts/.
"""
import json
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

SITE = "http://160.250.135.47:8080"
USER = "admin"
PWD = "Beplus!Test2026"
CHROME = os.environ.get("QA_CHROME", "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome")
OUT = "/root/beplus-external-embed-demo/qa-artifacts"
EMBED = f"{SITE}/wp-admin/admin.php?page=beplus-site-assistant-embed"
SETTINGS = f"{SITE}/wp-admin/admin.php?page=beplus-site-assistant"

ENDPOINT = open("/tmp/bsa_tunnel_url").read().strip()
ORIGIN = "https://beplus-external-embed-demo.vercel.app"


def api_code():
    key = subprocess.run(
        ["docker", "exec", "wp-app", "php", "/tmp/bsa_state.php", "key", ORIGIN],
        capture_output=True, text=True,
    ).stdout.strip()
    out = subprocess.run(
        ["curl", "-sS", "-m", "30", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Origin: {ORIGIN}", "-H", f"X-BSA-Site-Key: {key}",
         f"{ENDPOINT}/?bsa_embed=config"],
        capture_output=True, text=True,
    ).stdout.strip()
    return out


def run_viewport(pw, width, height, label):
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
    result = {"viewport": f"{width}x{height}", "errors": []}
    p.on("pageerror", lambda e: result["errors"].append(str(e)))

    p.goto(f"{SITE}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")

    # --- the new screen -------------------------------------------------
    p.goto(EMBED, wait_until="networkidle")
    body = p.content()
    result["has_list"] = "Your websites" in body
    result["site_listed"] = ORIGIN in body
    result["connected_pill"] = "Connected" in body
    result["advanced_present"] = "Pause every embed" in body
    result["snippet_present"] = "data-bsa-key" in body

    secret = subprocess.run(
        ["docker", "exec", "wp-app", "php", "/tmp/bsa_state.php", "secret"],
        capture_output=True, text=True,
    ).stdout.strip()
    result["secret_printed_plaintext"] = secret in body
    result["secret_masked"] = "••••••••" in body

    p.screenshot(path=f"{OUT}/admin-embed-{label}.png", full_page=True)

    # --- settings page must no longer carry the duplicate controls -------
    p.goto(SETTINGS, wait_until="networkidle")
    p.wait_for_timeout(1500)
    sbody = p.content()
    result["settings_legacy_card_gone"] = "External Embed (Next.js" not in sbody
    result["settings_no_legacy_toggle"] = "Require signed server requests" not in sbody
    p.screenshot(path=f"{OUT}/admin-settings-{label}.png", full_page=True)

    # --- the buttons must actually do something --------------------------
    p.goto(EMBED, wait_until="networkidle")
    result["before_pause_api"] = api_code()
    p.eval_on_selector(
        "form:has(input[name='bsa_embed_action'][value='toggle']) button",
        "el => el.click()",
    )
    p.wait_for_load_state("networkidle")
    p.wait_for_timeout(600)
    after_body = p.content()
    result["paused_pill"] = "Paused" in after_body
    result["after_pause_api"] = api_code()

    p.eval_on_selector(
        "form:has(input[name='bsa_embed_action'][value='toggle']) button",
        "el => el.click()",
    )
    p.wait_for_load_state("networkidle")
    p.wait_for_timeout(600)
    result["after_reconnect_api"] = api_code()
    result["reconnect_pill"] = "Connected" in p.content()

    result["overflow_x"] = p.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"
    )
    b.close()
    return result


def main():
    os.makedirs(OUT, exist_ok=True)
    out = []
    with sync_playwright() as pw:
        for w, h, lbl in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            out.append(run_viewport(pw, w, h, lbl))
    print(json.dumps(out, indent=2))

    ok = True
    for r in out:
        for k, want in [
            ("has_list", True), ("site_listed", True), ("advanced_present", True),
            ("snippet_present", True), ("secret_printed_plaintext", False),
            ("secret_masked", True), ("settings_legacy_card_gone", True),
            ("settings_no_legacy_toggle", True), ("before_pause_api", "200"),
            ("paused_pill", True), ("after_pause_api", "403"),
            ("after_reconnect_api", "200"), ("reconnect_pill", True),
            ("overflow_x", False),
        ]:
            if r.get(k) != want:
                ok = False
                print(f"FAIL {r['viewport']} {k}={r.get(k)!r} want {want!r}")
        if r["errors"]:
            ok = False
            print(f"FAIL {r['viewport']} console errors: {r['errors']}")
    print("QA:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
