import { NextRequest, NextResponse } from "next/server";
import { clientIp, jsonBodyLimit, noStore, rejectUntrustedBrowser, signedHeaders, WORDPRESS } from "@/lib/embed-security";

export async function POST(request: NextRequest) {
  const denied = rejectUntrustedBrowser(request) || jsonBodyLimit(request);
  if (denied) return denied;

  const incoming = await request.json().catch(() => null);
  if (!incoming || typeof incoming !== "object" || Array.isArray(incoming)) {
    return NextResponse.json({ ok: false, error: "Invalid request." }, { status: 400, headers: noStore() });
  }
  const message = typeof incoming.message === "string" ? incoming.message.trim() : "";
  if (!message || message.length > 300) {
    return NextResponse.json({ ok: false, error: "Please enter a message up to 300 characters." }, { status: 400, headers: noStore() });
  }

  // Explicit allowlist: no arbitrary nested objects or attacker-controlled headers
  // are forwarded to WordPress.
  const allowed = ["message", "website", "elapsed", "url", "client_id", "session_id", "visitor_name", "visitor_email", "lang"];
  const form = new URLSearchParams();
  for (const key of allowed) {
    const value = incoming[key];
    if (typeof value === "string") form.set(key, value.slice(0, key === "message" ? 300 : 512));
    if (key === "elapsed" && typeof value === "number" && Number.isFinite(value)) {
      const elapsed = Math.max(0, Math.min(86400, Math.floor(value)));
      form.set(key, String(elapsed));
    }
  }
  const body = form.toString();
  try {
    const headers = new Headers(signedHeaders("chat", body, clientIp(request)));
    headers.set("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
    const response = await fetch(`${WORDPRESS}/?bsa_embed=chat`, { method: "POST", headers, body, cache: "no-store" });
    const payload = await response.json().catch(() => ({ ok: false, error: "Invalid upstream response." }));
    return NextResponse.json(payload, { status: response.ok ? 200 : response.status, headers: noStore() });
  } catch {
    return NextResponse.json({ ok: false, error: "Live WordPress assistant is unavailable." }, { status: 502, headers: noStore() });
  }
}
