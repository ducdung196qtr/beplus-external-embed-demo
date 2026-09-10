import crypto from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

export const EMBED_ORIGIN = "https://beplus-external-embed-demo.vercel.app";
const MAX_BODY_BYTES = 8_192;

function configuredSecret(): string | null {
  const secret = process.env.BSA_EMBED_PROXY_SECRET;
  return secret && /^[\x20-\x7E]{32,256}$/.test(secret) ? secret : null;
}

export function rejectUntrustedBrowser(request: NextRequest): NextResponse | null {
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");
  // Fetch Metadata is set by real browsers and blocks cross-site navigation,
  // form and script abuse before the request can consume upstream AI capacity.
  // A same-origin GET may omit Origin, but unsafe requests must supply ours.
  const sameSite = fetchSite === "same-origin" || fetchSite === "same-site";
  const unsafe = request.method !== "GET" && request.method !== "HEAD";
  if (!sameSite || (origin && origin !== EMBED_ORIGIN) || (unsafe && origin !== EMBED_ORIGIN)) {
    return NextResponse.json({ ok: false, error: "Request denied." }, { status: 403, headers: noStore() });
  }
  return null;
}

export function jsonBodyLimit(request: NextRequest): NextResponse | null {
  const length = Number(request.headers.get("content-length") || "0");
  if (length > MAX_BODY_BYTES) return NextResponse.json({ ok: false, error: "Request too large." }, { status: 413, headers: noStore() });
  return null;
}

export function clientIp(request: NextRequest): string {
  const candidate = (request.headers.get("x-vercel-forwarded-for") || request.headers.get("x-forwarded-for") || "").split(",")[0].trim();
  // WordPress independently validates the value; use a benign explicit placeholder
  // when unavailable so the signed request is denied rather than collapsing limits.
  return candidate || "0.0.0.0";
}

export function signedHeaders(mode: "config" | "chat", body: string, ip: string): HeadersInit {
  const secret = configuredSecret();
  if (!secret) throw new Error("BSA_EMBED_PROXY_SECRET is not configured");
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = crypto.randomUUID();
  const bodyHash = crypto.createHash("sha256").update(body).digest("hex");
  const canonical = ["bsa-embed-v1", mode, timestamp, nonce, EMBED_ORIGIN, ip, bodyHash].join("\n");
  const signature = crypto.createHmac("sha256", secret).update(canonical).digest("hex");
  return {
    Origin: EMBED_ORIGIN,
    "X-BSA-Timestamp": timestamp,
    "X-BSA-Nonce": nonce,
    "X-BSA-Signature": signature,
    "X-BSA-Client-IP": ip,
  };
}

export function noStore(): HeadersInit {
  return {
    "Cache-Control": "no-store, max-age=0",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
  };
}
export const WORDPRESS = "http://160.250.135.47:8080";
export { MAX_BODY_BYTES };
