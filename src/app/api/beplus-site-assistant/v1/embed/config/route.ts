import { NextRequest, NextResponse } from "next/server";
import { clientIp, noStore, rejectUntrustedBrowser, signedHeaders, WORDPRESS } from "@/lib/embed-security";

export async function GET(request: NextRequest) {
  const denied = rejectUntrustedBrowser(request);
  if (denied) return denied;
  try {
    const response = await fetch(`${WORDPRESS}/?bsa_embed=config`, {
      headers: signedHeaders("config", "", clientIp(request)),
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok || !payload?.ok) throw new Error("WordPress config unavailable");
    // Browser stays same-origin/HTTPS while the test WP host is HTTP.
    payload.config.apiUrl = "/api/beplus-site-assistant/v1/embed/chat";
    payload.config.widgetCssUrl = "/api/beplus-site-assistant/v1/embed/asset/chat-widget.css";
    payload.config.widgetJsUrl = "/api/beplus-site-assistant/v1/embed/asset/chat-widget.js";
    return NextResponse.json(payload, { headers: noStore() });
  } catch {
    return NextResponse.json({ ok: false, error: "Live WordPress assistant is unavailable." }, { status: 502, headers: noStore() });
  }
}
