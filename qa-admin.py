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
import time

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
TOGGLE_BTN = "form:has(input[name='bsa_embed_action'][value='toggle']) button"


def harness(*args):
    return subprocess.run(
        ["docker", "exec", "wp-app", "php", "/tmp/bsa_state.php", *map(str, args)],
        capture_output=True, text=True,
    ).stdout.strip()


def api_code():
    key = harness("key", ORIGIN)
    return subprocess.run(
        ["curl", "-sS", "-m", "30", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Origin: {ORIGIN}", "-H", f"X-BSA-Site-Key: {key}",
         f"{ENDPOINT}/?bsa_embed=config"],
        capture_output=True, text=True,
    ).stdout.strip()


def safe_content(page, attempts=10):
    """The admin form posts and redirects; wait until the document settles."""
    for _ in range(attempts):
        try:
            return page.content()
        except Exception:
            page.wait_for_timeout(700)
    page.wait_for_load_state("load")
    return page.content()


def submit(page, selector):
    """Click a control that submits a real form and wait for the redirect."""
    with page.expect_navigation(wait_until="load"):
        page.eval_on_selector(selector, "el => el.click()")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(400)


def run_viewport(pw, width, height, label):
    # Start from a known state so the button labels and the API agree.
    harness("set-paused", 0)
    harness("set-enabled", ORIGIN, 1)
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
    r = {"viewport": f"{width}x{height}", "errors": []}
    p.on("pageerror", lambda e: r["errors"].append(str(e)))

    p.goto(f"{SITE}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")

    # --- the new screen --------------------------------------------------
    p.goto(EMBED, wait_until="networkidle")
    body = safe_content(p)
    r["has_list"] = "Your websites" in body
    r["site_listed"] = ORIGIN in body
    r["connected_pill"] = "Connected" in body
    r["advanced_present"] = "Pause every embed" in body
    r["snippet_present"] = "data-bsa-key" in body
    r["secret_printed_plaintext"] = harness("secret") in body
    r["secret_masked"] = "••••••••" in body
    p.screenshot(path=f"{OUT}/admin-embed-{label}.png", full_page=True)

    # --- settings page must no longer carry the duplicate controls -------
    p.goto(SETTINGS, wait_until="networkidle")
    p.wait_for_timeout(1500)
    s = safe_content(p)
    r["settings_legacy_card_gone"] = "External Embed (Next.js" not in s
    r["settings_no_legacy_toggle"] = "Require signed server requests" not in s
    p.screenshot(path=f"{OUT}/admin-settings-{label}.png", full_page=True)

    # --- the buttons must actually do something --------------------------
    p.goto(EMBED, wait_until="networkidle")
    r["before_pause_api"] = api_code()

    submit(p, TOGGLE_BTN)
    after_pause = safe_content(p)
    r["paused_pill"] = "Paused" in after_pause
    r["pause_button_label"] = "Connect" in after_pause
    r["after_pause_api"] = api_code()

    submit(p, TOGGLE_BTN)
    after_on = safe_content(p)
    r["reconnect_pill"] = "Connected" in after_on
    r["reconnect_button_label"] = "Pause connection" in after_on
    r["after_reconnect_api"] = api_code()

    # the secret must be obtainable by Copy, but absent from the page source
    r["secret_not_in_page"] = harness("secret") not in after_on
    r["secret_ajax_ok"] = p.evaluate(
        """async () => {
            const b = document.querySelector('.bsa-reveal-secret');
            if (!b) return 'missing';
            const res = await fetch(b.getAttribute('data-endpoint') + '?action=bsa_embed_secret&_wpnonce=' + encodeURIComponent(b.getAttribute('data-nonce')), { credentials: 'same-origin' });
            const j = await res.json();
            return (j && j.success && j.data && j.data.secret) ? 'ok' : 'denied';
        }"""
    )
    r["secret_ajax_denied_without_nonce"] = p.evaluate(
        """async () => {
            const b = document.querySelector('.bsa-reveal-secret');
            const res = await fetch(b.getAttribute('data-endpoint') + '?action=bsa_embed_secret', { credentials: 'same-origin' });
            const j = await res.json();
            return (j && j.success) ? 'leaked' : 'denied';
        }"""
    )

    r["overflow_x"] = p.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"
    )
    b.close()
    return r


THROWAWAY = "https://qa-throwaway.example.com"


def api_code_for(origin):
    key = harness("key", origin)
    if not key:
        return "no-key"
    return subprocess.run(
        ["curl", "-sS", "-m", "30", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Origin: {origin}", "-H", f"X-BSA-Site-Key: {key}",
         f"{ENDPOINT}/?bsa_embed=config"],
        capture_output=True, text=True,
    ).stdout.strip()


def run_full_flow(pw):
    """The primary journey: type an address, get a list row and a working script."""
    harness("remove", THROWAWAY)
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    r = {"flow": "add -> snippet -> remove", "errors": []}
    p.on("pageerror", lambda e: r["errors"].append(str(e)))
    p.on("dialog", lambda d: d.accept())

    p.goto(f"{SITE}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")

    p.goto(EMBED, wait_until="networkidle")
    r["count_before"] = len(p.query_selector_all("details.bsa-embed-share"))

    p.fill("#bsa-site-url", THROWAWAY)
    submit(p, "form:has(input[name='bsa_embed_action'][value='add']) button")
    body = safe_content(p)
    p.wait_for_timeout(400)
    r["row_created"] = THROWAWAY in body
    r["panel_auto_opened"] = p.evaluate(
        """(origin) => [...document.querySelectorAll('details.bsa-embed-share[open]')]
             .some(d => d.textContent.includes(origin) && /data-bsa-key="pk_/.test(d.querySelector('textarea')?.value || ''))""",
        THROWAWAY,
    )
    r["remove_is_red"] = p.eval_on_selector(".bsa-embed-remove", "el => getComputedStyle(el).color")
    r["new_key_works_immediately"] = api_code_for(THROWAWAY)
    p.screenshot(path=f"{OUT}/admin-embed-after-add.png", full_page=True)

    submit(p, f"form:has(input[name='bsa_site_origin'][value='{THROWAWAY}']) button.bsa-embed-remove")
    p.wait_for_timeout(500)
    page_after = safe_content(p)
    r["row_gone"] = p.evaluate(
        """(o) => ![...document.querySelectorAll('details.bsa-embed-share')]
             .some(d => d.textContent.includes(o))""",
        THROWAWAY,
    )
    r["remove_notice_shown"] = "removed" in page_after
    r["key_dead_after_remove"] = api_code_for(THROWAWAY)
    b.close()
    return r


EXPECT = [
    ("has_list", True), ("site_listed", True), ("connected_pill", True),
    ("advanced_present", True), ("snippet_present", True),
    ("secret_printed_plaintext", False), ("secret_masked", True),
    ("settings_legacy_card_gone", True), ("settings_no_legacy_toggle", True),
    ("before_pause_api", "200"), ("paused_pill", True), ("after_pause_api", "403"),
    ("after_reconnect_api", "200"), ("reconnect_pill", True),
    ("pause_button_label", True), ("reconnect_button_label", True),
    ("secret_not_in_page", True), ("secret_ajax_ok", "ok"),
    ("secret_ajax_denied_without_nonce", "denied"), ("overflow_x", False),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    results, ok = [], True
    try:
        with sync_playwright() as pw:
            for w, h, lbl in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
                results.append(run_viewport(pw, w, h, lbl))
            flow = run_full_flow(pw)
            results.append(flow)
    finally:
        # never leave the WordPress test site paused, whatever happened above
        harness("set-paused", 0)
        harness("set-enabled", ORIGIN, 1)

    print(json.dumps(results, indent=2))
    for k, want in [("row_created", True), ("panel_auto_opened", True),
                    ("remove_is_red", "rgb(179, 45, 46)"),
                    ("new_key_works_immediately", "200"),
                    ("row_gone", True), ("remove_notice_shown", True),
                    ("key_dead_after_remove", "no-key"),
                    ("count_before", 1)]:
        if flow.get(k) != want:
            ok = False
            print(f"FAIL flow {k}={flow.get(k)!r} want {want!r}")
    if flow["errors"]:
        ok = False
        print("FAIL flow console errors:", flow["errors"])
    for r in results:
        if "viewport" not in r:
            continue  # the flow entry has its own checks above
        for k, want in EXPECT:
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
