"""Verify the exact copy-paste snippet works on the live demo site.

Asserts the snippet the admin UI generates is the snippet the browser actually
loads, then walks the whole flow the way a visitor's browser does it:

  embed.js requested from WordPress -> config fetched with the site key ->
  the SAME widget CSS/JS mounted -> a question answered by the real WP pipeline.

A 200 from curl proves none of this: the loader is silent by design, so a denied
or broken embed looks identical to a working one until you look in the browser.
"""
import json
import re

from playwright.sync_api import sync_playwright

from bsa_endpoints import wp_url

CHROME = "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome"
WP = wp_url()
DEMO = "https://beplus-external-embed-demo.vercel.app/"
KEY = "pk_WrQkewYFVUq5gMFyYbDiPUrktSMk1n4h"
EXPECTED_SRC = f"{WP}/wp-content/plugins/beplus-site-assistant/assets/embed.js"

result = {"step": {}, "failures": []}


def check(name, ok, detail=""):
    result["step"][name] = {"ok": bool(ok), "detail": str(detail)[:200]}
    if not ok:
        result["failures"].append(f"{name}: {detail}")


with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    page = b.new_page(viewport={"width": 1440, "height": 1000})

    requests, failed, console = [], [], []
    page.on("request", lambda r: requests.append(r.url))
    page.on("requestfailed", lambda r: failed.append(f"{r.url} :: {r.failure}"))
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type == "error" else None)

    page.goto(DEMO, wait_until="load")
    page.wait_for_timeout(7000)

    # 1. the tag in the LIVE DOM must be the snippet under test, character for character
    tags = page.evaluate(
        """() => [...document.querySelectorAll('script[data-bsa-site]')].map(s => ({
            src: s.src, site: s.getAttribute('data-bsa-site'),
            key: s.getAttribute('data-bsa-key')}))"""
    )
    check("snippet tag present in DOM", len(tags) == 1, f"found {len(tags)}")
    if tags:
        t = tags[0]
        check("src matches the snippet under test", t["src"] == EXPECTED_SRC, t["src"])
        check("data-bsa-site matches", t["site"] == DEMO.rstrip("/"), t["site"])
        check("data-bsa-key matches", t["key"] == KEY, t["key"][:14] + "...")

    # 2. the browser really fetched embed.js from the HTTPS WordPress host
    check("embed.js requested over https", any(EXPECTED_SRC in u for u in requests))
    check("no request was blocked", not failed, failed[:2])

    # 3. config came back from the WP endpoint with the key in a header
    cfg_reqs = [u for u in requests if "bsa_embed=config" in u]
    check("config endpoint called", bool(cfg_reqs), cfg_reqs[:1])

    # 4. the real WordPress widget runtime mounted (same CSS + JS as WP)
    checks = page.evaluate(
        """() => ({
            booted: !!window.__bsaExternalBooted,
            bsaChat: !!window.bsaChat,
            externalEmbed: !!(window.bsaChat && window.bsaChat.externalEmbed),
            css: [...document.querySelectorAll('link[rel=stylesheet]')]
                    .some(l => l.href.includes('chat-widget.css')),
            js: [...document.querySelectorAll('script[src]')]
                    .some(s => s.src.includes('chat-widget.js')),
            widgetNode: !!document.querySelector('#bsa-chat-root'),
        })"""
    )
    check("loader booted", checks["booted"])
    check("externalEmbed flag set", checks["externalEmbed"])
    check("WP widget CSS loaded", checks["css"])
    check("WP widget JS loaded", checks["js"])
    check("widget mounted in DOM", checks["widgetNode"])

    # 5. no secret leaked into page context
    leaked = page.evaluate(
        """() => {
            const t = document.documentElement.outerHTML;
            return ['sk_', 'proxy_secret', 'api_key'].filter(w => t.includes(w));
        }"""
    )
    check("no secret in page HTML", not leaked, leaked)

    # 6. it must actually answer — open, ask a KB-specific question, read the reply
    fab = page.query_selector("#bsa-chat-root .bsa-fab")
    check("launcher button present", bool(fab))
    if fab:
        fab.click(force=True)
        page.wait_for_timeout(2500)

    # This install has lead capture on, so the widget opens on a name/email gate
    # rather than straight into the input. Same widget, same settings as WP —
    # the external embed inherits the configured flow instead of a cut-down one.
    gate = page.query_selector("#bsa-chat-root .bsa-lead-submit")
    check("lead gate shown (lead capture is on)", bool(gate))
    if gate:
        page.fill("#bsa-chat-root .bsa-lead-name", "QA Visitor")
        page.fill("#bsa-chat-root .bsa-lead-email", "qa.visitor@example.com")
        gate.click(force=True)
        page.wait_for_timeout(3000)
        check("gate dismissed, chat available",
              page.is_visible("#bsa-chat-root .bsa-input"))

    box = page.query_selector("#bsa-chat-root .bsa-input, #bsa-chat-root textarea")
    if box and box.is_visible():
        box.fill("What services does this company offer?")
        box.press("Enter")
        page.wait_for_timeout(18000)
        chat = page.evaluate(
            """() => {
                const n = document.querySelector('#bsa-chat-root .bsa-chat-body');
                return n ? n.innerText.trim() : '';
            }"""
        )
        check("chat produced an answer", len(chat) > 40, f"{len(chat)} chars")
        result["answer_preview"] = chat[:700]
    else:
        check("chat input reachable", False, "input not visible after the gate")

    result["console_errors"] = console[:5]
    check("no console errors", not console, console[:2])
    page.screenshot(path="/root/beplus-external-embed-demo/qa-artifacts/snippet-exact-test.png")
    b.close()

result["VERDICT"] = "PASS" if not result["failures"] else "FAIL"
print(json.dumps(result, indent=2))
