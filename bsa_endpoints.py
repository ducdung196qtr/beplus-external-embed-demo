"""Where the WordPress test stack lives.

One place, because several QA scripts need this address, and a stale copy of it
silently tests the wrong server — or nothing at all. That is not hypothetical:
these scripts previously read a Cloudflare quick-tunnel URL that rotated every
time the tunnel restarted.

Resolution order: $BSA_WP_URL, then the persistent file, then the /tmp copy.
There is deliberately no fallback to the old tunnel: a dead address should fail
loudly rather than quietly pass a stale check.
"""
import os
import pathlib
import sys

FILES = ("/root/bsa-wp-url.txt", "/tmp/bsa_wp_url")


def wp_url() -> str:
    candidates = [os.environ.get("BSA_WP_URL", "")]
    candidates += [pathlib.Path(p).read_text().strip() if pathlib.Path(p).exists() else ""
                   for p in FILES]
    for value in candidates:
        if value.startswith("https://"):
            return value.rstrip("/")
    sys.exit("No WordPress address. Run: echo https://<host> > /root/bsa-wp-url.txt")


if __name__ == "__main__":
    print(wp_url())
