import { NextRequest, NextResponse } from "next/server";
export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const message = typeof body.message === "string" ? body.message.trim() : "";
  if (!message || message.length > 300) return NextResponse.json({ ok: false, error: "Please enter a short message." }, { status: 400 });
  return NextResponse.json({ ok: true, answer: "Demo response: the widget sent your message through the external embed contract. In production this exact request is answered by Beplus Site Assistant on your HTTPS WordPress domain, using its existing FAQ, Knowledge Base, Guard, and AI provider.", sources: [] });
}
