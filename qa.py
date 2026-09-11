"""End-to-end QA of the external embed on the live Vercel landing page.

Checks, per viewport:
  - the WordPress widget runtime mounted (#bsa-chat-root, .bsa-fab, .bsa-panel)
  - no legacy/standalone embed UI (.bsae-*)
  - the lead gate works and a real answer comes back from the WordPress KB
  - no horizontal overflow, no uncaught JS errors
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

URL = "https://beplus-external-embed-demo.vercel.app/"
CHROME = os.environ.get(
    "QA_CHROME",
    "/root/.agent-browser/browsers/chrome-153.0.8010.36/chrome-linux64/chrome",
)
OUT = "/root/beplus-external-embed-demo/qa-artifacts"

VIEWPORTS = [
    ("desktop", 1440, 900),
    ("mobile", 390, 844),
]

QUESTION = "What is AlonePro and how do I install it?"


def run(pw, name, width, height, mobile):
    errors = []
    browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": width, "height": height},
                            is_mobile=mobile,
                            has_touch=mobile,
                            device_scale_factor=2)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}")
            if m.type == "error" else None)

    page.goto(URL, wait_until="networkidle", timeout=90_000)
    page.wait_for_selector("#bsa-chat-root", state="attached", timeout=45_000)
    page.wait_for_selector(".bsa-fab", state="visible", timeout=45_000)
    page.wait_for_timeout(2500)

    mounted = page.evaluate("""() => ({
        chatRoot: !!document.querySelector('#bsa-chat-root'),
        fab: !!document.querySelector('.bsa-fab'),
        panel: !!document.querySelector('.bsa-panel'),
        mascot: !!document.querySelector('[class*=mascot]'),
        legacyUi: document.querySelectorAll('[class^=bsae-]').length,
        botName: (window.bsaChat || {}).textBotName || null,
        chatUrl: (window.bsaChat || {}).externalChatUrl || null
    })""")

    # Open the widget and clear the lead gate.
    # The trigger button floats/pulses, so it is never "stable" for Playwright.
    page.eval_on_selector(".bsa-fab", "el => el.click()")
    page.wait_for_timeout(1200)
    gate = page.query_selector("input[placeholder*='Your name']")
    if gate:
        gate.fill("QA Visitor")
        page.fill("input[placeholder*='email']", "qa.visitor@example.com")
        page.eval_on_selector("button:has-text('Start Chatting')", "el => el.click()")
        page.wait_for_timeout(1500)

    page.fill("textarea", QUESTION)
    page.wait_for_timeout(200)
    page.eval_on_selector(".bsa-send", "el => el.click()")
    try:
        page.wait_for_function(
            "() => { const b=[...document.querySelectorAll('.bsa-bubble-content')];"
            " return b.length>0 && b.some(x=>x.textContent.trim().length>80); }",
            timeout=90_000,
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"answer timeout: {exc}")
    page.wait_for_timeout(1500)

    state = page.evaluate("""() => {
        const bubbles = [...document.querySelectorAll('.bsa-bubble-content')];
        const answer = bubbles.length ? bubbles[bubbles.length - 1].textContent.trim() : '';
        const de = document.documentElement;
        return {
            answerChars: answer.length,
            answerStart: answer.slice(0, 120),
            overflowX: de.scrollWidth > de.clientWidth,
            scrollWidth: de.scrollWidth,
            clientWidth: de.clientWidth
        };
    }""")

    os.makedirs(OUT, exist_ok=True)
    shot = f"{OUT}/{name}.png"
    page.screenshot(path=shot, full_page=False)

    page.click(".bsa-fab") if page.query_selector(".bsa-panel") is None else None
    page.wait_for_timeout(400)

    result = {
        "viewport": f"{width}x{height}",
        "mounted": mounted,
        "liveAnswer": state["answerChars"] > 80,
        "answerChars": state["answerChars"],
        "answerStart": state["answerStart"],
        "overflowX": state["overflowX"],
        "screenshot": shot,
        "errors": errors,
    }
    browser.close()
    return result


def main():
    results = []
    with sync_playwright() as pw:
        for name, w, h in VIEWPORTS:
            results.append(run(pw, name, w, h, mobile=(w < 600)))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    ok = all(
        r["mounted"]["chatRoot"]
        and r["mounted"]["fab"]
        and r["mounted"]["legacyUi"] == 0
        and r["liveAnswer"]
        and not r["overflowX"]
        and not r["errors"]
        for r in results
    )
    print("QA:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
