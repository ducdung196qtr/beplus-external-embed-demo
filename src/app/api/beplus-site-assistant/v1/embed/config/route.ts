import { NextRequest, NextResponse } from "next/server";
export function GET(request: NextRequest) {
  const origin = request.headers.get("origin");
  const allowed = new Set(["http://localhost:3000", "http://localhost:3001"]);
  if (origin && !allowed.has(origin)) return NextResponse.json({ error: "Origin not allowed" }, { status: 403 });
  // Relative URL deliberately keeps this local/Vercel demo same-origin.
  // Production plugin config returns its own HTTPS WordPress REST URL.
  return NextResponse.json({ ok: true, config: { apiUrl: "/api/beplus-site-assistant/v1/embed/chat", welcome: "Hi! I’m Beplus Assistant. This is the external embed UI contract demo.", faqs: [], botName: "Beplus Assistant", botStatus: "External embed demo", placeholder: "Ask about the integration…", accent: "#ec4899", widgetPosition: "bottom-right" } });
}
