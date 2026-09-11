"""Prove what happens when the HTTP snippet is pasted into an HTTPS page.

Two pages of the same deployed app:
  /                loads the snippet with an https:// src  -> widget must mount
  /http-snippet/   loads the snippet with the http:// src  -> must be blocked

Run after deploying. Any browser that allows the second case would mean the
widget silently works for nobody and we would not notice.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
BASE = "https://beplus-external-embed-demo.vercel.app"
OUT = "/root/beplus-external-embed-demo/qa-artifacts"


def probe(pw, path, label):
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1280, "height": 900})
    console, requests, errors = [], [], []
    p.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
    p.on("requestfailed", lambda r: errors.append(f"{r.url} :: {r.failure}"))
    p.on("request", lambda r: requests.append(r.url))

    r = {"page": label, "url": f"{BASE}{path}"}
    p.goto(f"{BASE}{path}", wait_until="networkidle")
    p.wait_for_timeout(3500)

    r["embed_js_requested"] = any("assets/embed.js" in u for u in requests)
    r["widget_present"] = p.evaluate(
        """() => !!(document.querySelector('[class*="bsa-"]') ||
                  document.querySelector('#bsa-chat-root, .bsa-chat-root, .bsa-fab'))"""
    )
    r["mixed_content"] = [c for c in console if "mixed content" in c.lower()]
    r["blocked_requests"] = [e for e in errors if "embed.js" in e]
    r["console_errors"] = [c for c in console if c.startswith("error")]
    p.screenshot(path=f"{OUT}/mixed-content-{label}.png", full_page=True)
    b.close()
    return r


with sync_playwright() as pw:
    served_over_https = probe(pw, "/", "https-snippet")
    served_over_http = probe(pw, "/http-snippet/", "http-snippet")

print(json.dumps({"https_page": served_over_https, "http_page": served_over_http}, indent=2))

ok = True
checks = [
    ("https page: embed.js requested", served_over_https["embed_js_requested"], True),
    ("https page: widget mounted", served_over_https["widget_present"], True),
    ("https page: no mixed content", served_over_https["mixed_content"], []),
    # the request is attempted, then the browser refuses it: the failure shows
    # up as a blocked request, not as an absent request
    ("http page: embed.js attempted", served_over_http["embed_js_requested"], True),
    ("http page: embed.js blocked", bool(served_over_http["blocked_requests"]), True),
    ("http page: browser explained why", bool(served_over_http["mixed_content"]), True),
    ("http page: widget absent", served_over_http["widget_present"], False),
]
for name, got, want in checks:
    if got != want:
        ok = False
        print(f"FAIL {name}: got={got!r} want={want!r}")
print("MIXED CONTENT:", "CONFIRMED BLOCKED" if ok else "UNEXPECTED")
