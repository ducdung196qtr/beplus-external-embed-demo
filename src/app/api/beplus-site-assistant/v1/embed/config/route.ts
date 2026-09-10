import { NextResponse } from "next/server";

const WORDPRESS = "http://160.250.135.47:8080";
const ORIGIN = "https://beplus-external-embed-demo.vercel.app";

export async function GET() {
  try {
    const response = await fetch(`${WORDPRESS}/?bsa_embed=config`, {
      headers: { Origin: ORIGIN },
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok || !payload?.ok) throw new Error("WordPress config unavailable");
    // Keep the browser same-origin; Vercel safely proxies to the test WP HTTP endpoint.
    payload.config.apiUrl = "/api/beplus-site-assistant/v1/embed/chat";
    return NextResponse.json(payload, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ ok: false, error: "Live WordPress assistant is unavailable." }, { status: 502 });
  }
}
