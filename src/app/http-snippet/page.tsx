/**
 * Deliberate failure case, kept as evidence.
 *
 * This page pastes the snippet exactly as the WordPress admin screen produced
 * it while the admin was browsing over plain HTTP — note the http:// src. The
 * page itself is served over HTTPS, so the browser must refuse to load that
 * script as mixed content. Nothing here is fixed up or proxied on purpose:
 * this is what a visitor would get.
 */
const HTTP_SNIPPET = `<script src="http://160.250.135.47:8080/wp-content/plugins/beplus-site-assistant/assets/embed.js" data-bsa-site="https://beplus-external-embed-demo.vercel.app" data-bsa-key="pk_WrQkewYFVUq5gMFyYbDiPUrktSMk1n4h" defer></script>`;

export default function HttpSnippet() {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "48px 24px", maxWidth: 720, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28 }}>Snippet copied over HTTP</h1>
      <p style={{ color: "#555", lineHeight: 1.6 }}>
        This page was served over HTTPS and contains the script tag exactly as the plugin
        generated it while the administrator was on the plain HTTP address.
      </p>
      <pre
        style={{
          background: "#0f172a", color: "#a5f3fc", padding: 16, borderRadius: 8,
          overflowX: "auto", fontSize: 12, lineHeight: 1.6,
        }}
      >
        {HTTP_SNIPPET}
      </pre>
      <p id="outcome" style={{ color: "#555", lineHeight: 1.6 }}>
        Look for the chat bubble in the bottom-right corner. There should be none.
      </p>
      <div dangerouslySetInnerHTML={{ __html: HTTP_SNIPPET }} />
    </main>
  );
}
