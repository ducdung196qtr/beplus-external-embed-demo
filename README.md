# Beplus Site Assistant — external embed demo

A plain Next.js landing page that shows the real WordPress Site Assistant chat,
without WordPress installed on the site and without any custom chat code.

Live: https://beplus-external-embed-demo.vercel.app/

## How it works

The entire integration is one script tag, generated inside WordPress under
**Site Assistant → Embed Script** and pasted into the page:

```html
<script
  src="https://your-wordpress/wp-content/plugins/beplus-site-assistant/assets/embed.js"
  data-bsa-site="https://beplus-external-embed-demo.vercel.app"
  data-bsa-key="pk_…"
  defer></script>
```

In this repo that tag lives at the bottom of `src/app/page.tsx` (rendered with
`next/script` so it behaves the same as a footer script).

`embed.js` then:

1. asks WordPress for that origin's public widget config,
2. loads the **same** `chat-widget.css` and `chat-widget.js` that WordPress
   serves, so the UI, mascot, FAQ and animations are identical, and
3. points the widget's chat transport at WordPress.

WordPress stays the single source of truth for styling, copy, FAQs and
knowledge. There is no second implementation of the chat UI here.

## Security

- The snippet contains a public per-site key only — no AI key, no server secret.
- WordPress accepts requests only from the exact origins approved in
  **Site Assistant → Embed Script**; removing a site kills its key immediately.
- Rate limits, spam guard, guardrails and the daily budget all still apply.
- Config responses are stripped of anything internal (checked by QA).

## Note on the `WORDPRESS` constant

`WORDPRESS` in `src/app/page.tsx` points at the **test** WordPress used for this
demo: `https://160-250-135-47.sslip.io`, served over HTTPS by Caddy on the VPS.

This used to matter a great deal. The test stack speaks plain HTTP on port 8080,
and an HTTPS page may not load a script from an HTTP origin — the browser
refuses it as mixed content, and refuses it *silently*: no widget, no page
error, nothing in the logs. A temporary Cloudflare quick tunnel papered over it,
but its hostname changed on every restart, so the address had to be edited here
and redeployed.

`sslip.io` resolves to the server's IP, so Caddy can hold a real Let's Encrypt
certificate without owning a domain, and the address is now stable — nothing to
edit when anything restarts. See `/root/caddy/README.md` for the setup, and to
switch to a real domain.

For a real site none of this applies: a production WordPress is already HTTPS, so
the snippet points straight at it and no tunnel or proxy is involved.

## QA

All of these read the WordPress address from `bsa_endpoints.py`, which resolves
it from `/root/bsa-wp-url.txt` — one place, so no script can quietly test a
stale server.

```bash
python qa.py                 # landing: widget mounts, live answer, no overflow/errors
python qa-admin.py           # Embed Script screen, desktop 1440 + mobile 390
python qa-mixed-content.py   # the HTTP snippet really is blocked (failing case kept)
python qa-insecure-warning.py# the HTTP warning appears over HTTP and only there
python qa-snippet-loop.py    # the copied script matches the one the page runs
python qa-rotate-secret.py   # rotating the bridge secret kills the old one
python qa-www-hint.py        # the www/apex hint renders as markup
```

Artifacts land in `qa-artifacts/`.
