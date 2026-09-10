import { NextResponse } from "next/server";

const WORDPRESS = "http://160.250.135.47:8080";
const paths: Record<string, { path: string; type: string }> = {
  "chat-widget.css": { path: "/wp-content/plugins/beplus-site-assistant/admin/css/chat-widget.css", type: "text/css; charset=utf-8" },
  "chat-widget.js": { path: "/wp-content/plugins/beplus-site-assistant/admin/js/chat-widget.js", type: "application/javascript; charset=utf-8" },
};

export async function GET(_: Request, { params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  const asset = paths[name];
  if (!asset) return new NextResponse("Not found", { status: 404 });
  try {
    const upstream = await fetch(`${WORDPRESS}${asset.path}`, { cache: "no-store" });
    if (!upstream.ok) return new NextResponse("WordPress asset unavailable", { status: 502 });
    return new NextResponse(await upstream.text(), {
      headers: { "Content-Type": asset.type, "Cache-Control": "no-store" },
    });
  } catch {
    return new NextResponse("WordPress asset unavailable", { status: 502 });
  }
}
