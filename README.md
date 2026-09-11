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
demo. That test stack only speaks plain HTTP on a private port, and an HTTPS
page cannot call it directly (mixed content), so it is exposed through a
temporary Cloudflare quick tunnel — hence the random `trycloudflare.com`
hostname. If the tunnel restarts, update that one constant and redeploy.

For a real site this does not apply: a production WordPress is already HTTPS, so
the snippet points straight at it and no tunnel is involved.

## QA

```bash
python qa.py        # desktop 1440 + mobile 390, live answer, no overflow/errors
```

Artifacts land in `qa-artifacts/`.
