"""What a visitor actually experiences, from the browser's point of view.

Checks the two things that matter and that HTTP status codes cannot show:
the demo page's widget, and whether the HTTPS WordPress page is clean or
silently degraded by mixed content.
"""
import json

from playwright.sync_api import sync_playwright

from bsa_endpoints import wp_url

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
WP = wp_url()
DEMO = "https://beplus-external-embed-demo.vercel.app/"

out = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    # --- the demo page: does the chat mount? ---
    p = b.new_page(viewport={"width": 1440, "height": 1000})
    failed, console = [], []
    p.on("requestfailed", lambda r: failed.append(f"{r.url} :: {r.failure}"))
    p.on("console", lambda m: console.append(m.text) if m.type in ("error", "warning") else None)
    p.goto(DEMO, wait_until="load")
    p.wait_for_timeout(6000)
    out["demo"] = {
        "widget_present": p.evaluate("() => !!document.querySelector('[class*=bsa-]')"),
        "bubble_present": p.evaluate("() => !!document.querySelector('[class*=bsa-chat-], [id*=bsa]')"),
        "embed_js_loaded": p.evaluate("() => !!window.__bsaExternalBooted"),
        "failed_requests": [f for f in failed if "embed.js" in f or WP in f],
        "console_errors": console[:5],
    }
    p.screenshot(path="/root/beplus-external-embed-demo/qa-artifacts/demo-current.png")

    # --- the WordPress page over HTTPS: is it clean? ---
    p2 = b.new_page(viewport={"width": 1440, "height": 1000})
    blocked, failed2 = [], []
    p2.on("requestfailed", lambda r: failed2.append(f"{r.url} :: {r.failure}"))
    p2.on("response", lambda r: blocked.append(r.url) if r.status >= 400 else None)
    p2.goto(WP + "/", wait_until="load")
    p2.wait_for_timeout(3000)
    imgs = p2.evaluate(
        """() => [...document.images].map(i => ({
            src: i.currentSrc || i.src,
            ok: i.complete && i.naturalWidth > 0,
        }))"""
    )
    out["wordpress"] = {
        "images_total": len(imgs),
        "images_broken": sum(1 for i in imgs if not i["ok"]),
        "broken_examples": [i["src"] for i in imgs if not i["ok"]][:3],
        "failed_requests": [f for f in failed2 if "160.250.135.47" in f][:5],
        "http_4xx": [u for u in blocked if "160.250.135.47" in u][:5],
    }
    p2.screenshot(path="/root/beplus-external-embed-demo/qa-artifacts/wp-https-page.png", full_page=False)
    b.close()

print(json.dumps(out, indent=2))
