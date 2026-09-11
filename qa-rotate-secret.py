"""Rotate the exposed bridge secret through the real admin UI, then prove it.

The secret was visible in screenshots, so it must be replaced. This drives the
Advanced -> "Generate new secret" button in a browser and asserts the outcome at
the API level: the old value stops verifying, the new one starts.
"""
import hashlib
import hmac
import json
import secrets
import subprocess
import time

from playwright.sync_api import sync_playwright

SITE = "http://160.250.135.47:8080"
EMBED = f"{SITE}/wp-admin/admin.php?page=beplus-site-assistant-embed"
CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
USER, PWD = "admin", "Beplus!Test2026"
ORIGIN = "https://beplus-external-embed-demo.vercel.app"
ENDPOINT = open("/tmp/bsa_tunnel_url").read().strip()


def harness(*args):
    r = subprocess.run(
        ["docker", "exec", "wp-app", "php", "/tmp/bsa_state.php"] + [str(a) for a in args],
        capture_output=True, text=True,
    )
    return (r.stdout or r.stderr).strip()


def signed_status(secret):
    """Attempt a signed bridge request and report the HTTP status."""
    ts, nonce, ip = str(int(time.time())), secrets.token_urlsafe(32), "203.0.113.9"
    canon = "\n".join(
        ["bsa-embed-v1", "config", ts, nonce, ORIGIN, ip, hashlib.sha256(b"").hexdigest()]
    )
    sig = hmac.new(secret.encode(), canon.encode(), hashlib.sha256).hexdigest()
    return subprocess.run(
        ["curl", "-sS", "-m", "30", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Origin: {ORIGIN}", "-H", f"X-BSA-Timestamp: {ts}",
         "-H", f"X-BSA-Nonce: {nonce}", "-H", f"X-BSA-Signature: {sig}",
         "-H", f"X-BSA-Client-IP: {ip}", f"{ENDPOINT}/?bsa_embed=config"],
        capture_output=True, text=True,
    ).stdout.strip()


old = harness("secret")
assert old, "no secret to rotate"
print(f"old secret: [REDACTED] ({len(old)} chars)")
print("old secret signs a request :", signed_status(old), "(expect 200)")

results, ok = {}, True
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    p.on("pageerror", lambda e: errors.append(str(e)))

    p.goto(f"{SITE}/wp-login.php", wait_until="domcontentloaded")
    p.fill("#user_login", USER)
    p.fill("#user_pass", PWD)
    p.click("#wp-submit")
    p.wait_for_load_state("domcontentloaded")

    p.goto(EMBED, wait_until="networkidle")
    # the Advanced block is collapsed, exactly as an administrator finds it
    p.click("details.bsa-embed-advanced > summary")
    results["advanced_opened"] = p.is_visible(".bsa-reveal-secret")
    results["masked_before"] = p.eval_on_selector(
        "input[readonly].code", "el => el.value"
    )
    results["secret_absent_from_page"] = old not in p.content()

    with p.expect_navigation(wait_until="load"):
        p.click("form.bsa-embed-inline-form button[type=submit]")
    p.wait_for_load_state("networkidle")
    after = p.content()
    results["rotate_notice"] = "New bridge secret generated" in after
    results["rotated_page_has_no_secret"] = old not in after

    # Copy must still work afterwards, and hand back the NEW value
    p.click("details.bsa-embed-advanced > summary")
    new_secret = p.evaluate(
        """async () => {
            const b = document.querySelector('.bsa-reveal-secret');
            const res = await fetch(b.getAttribute('data-endpoint') +
                '?action=bsa_embed_secret&_wpnonce=' + encodeURIComponent(b.getAttribute('data-nonce')),
                { credentials: 'same-origin' });
            const j = await res.json();
            return (j && j.success && j.data && j.data.secret) || '';
        }"""
    )
    b.close()

results["secret_changed"] = bool(new_secret) and new_secret != old
results["old_secret_now_rejected"] = signed_status(old)
results["new_secret_accepted"] = signed_status(new_secret) if new_secret else "n/a"
results["console_errors"] = errors

print(json.dumps(results, indent=2))
for k, want in [("advanced_opened", True), ("secret_absent_from_page", True),
                ("rotate_notice", True), ("rotated_page_has_no_secret", True),
                ("secret_changed", True), ("old_secret_now_rejected", "403"),
                ("new_secret_accepted", "200")]:
    if results.get(k) != want:
        ok = False
        print(f"FAIL {k}={results.get(k)!r} want {want!r}")
if errors:
    ok = False
    print("FAIL console errors:", errors)
print("ROTATE:", "PASS" if ok else "FAIL")
