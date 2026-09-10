import { NextRequest, NextResponse } from "next/server";

const WORDPRESS = "http://160.250.135.47:8080";
const ORIGIN = "https://beplus-external-embed-demo.vercel.app";

export async function POST(request: NextRequest) {
  const incoming = await request.json().catch(() => ({}));
  const message = typeof incoming.message === "string" ? incoming.message.trim() : "";
  if (!message || message.length > 1000) {
    return NextResponse.json({ ok: false, error: "Please enter a message up to 1,000 characters." }, { status: 400 });
  }
  const form = new URLSearchParams();
  for (const [key, value] of Object.entries(incoming)) {
    if (typeof value === "string" || typeof value === "number") form.set(key, String(value));
  }
  try {
    const response = await fetch(`${WORDPRESS}/?bsa_embed=chat`, {
      method: "POST",
      headers: { Origin: ORIGIN, "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
      cache: "no-store",
    });
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.ok ? 200 : response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ ok: false, error: "Live WordPress assistant is unavailable." }, { status: 502 });
  }
}
