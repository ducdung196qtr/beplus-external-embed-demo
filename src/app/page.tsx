import Script from "next/script";
import styles from "./page.module.css";

/**
 * This page is a plain Next.js landing with no WordPress runtime.
 *
 * The only integration is the snippet generated in WordPress under
 * Site Assistant → Embed Script, pasted below. It loads the same widget CSS
 * and JS that WordPress serves, so the chat looks and behaves identically.
 */
const WORDPRESS = "https://production-toddler-sample-securities.trycloudflare.com";

export default function Home() {
  return (
    <main className={styles.main}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>Beplus Site Assistant</p>
        <h1>One assistant.<br />Any website.</h1>
        <p className={styles.lede}>
          This Next.js landing page has no WordPress runtime and no chat code of its own. The
          assistant you can open in the corner comes entirely from one script tag copied out of
          the WordPress plugin.
        </p>
        <div className={styles.actions}>
          <a href="#demo">View embed demo</a>
          <a className={styles.secondary} href="#how">How it works</a>
        </div>
      </section>

      <section id="demo" className={styles.grid}>
        <article><span>01</span><h2>One script tag</h2><p>Copied from Site Assistant → Embed Script and pasted into this page. Nothing is built or rewritten here.</p></article>
        <article><span>02</span><h2>The real WordPress widget</h2><p>The same chat-widget.css and chat-widget.js files that WordPress serves. Same mascot, same FAQ, same animations.</p></article>
        <article><span>03</span><h2>WordPress stays the source of truth</h2><p>Colours, bot name, welcome text, FAQs and knowledge all live in WordPress. Change them there and this page follows on reload.</p></article>
      </section>

      <section id="how" className={styles.note}>
        <strong>Live WordPress knowledge, no secrets in the browser</strong>
        <p>
          The script contains a public site key only — no AI key and no server secret. WordPress
          accepts requests from this exact address, refuses any other origin, and still applies its
          own rate limits, spam guard and guardrails to every message.
        </p>
      </section>

      {/* Copied verbatim from WordPress → Site Assistant → Embed Script */}
      <Script
        src={`${WORDPRESS}/wp-content/plugins/beplus-site-assistant/assets/embed.js`}
        data-bsa-site="https://beplus-external-embed-demo.vercel.app"
        data-bsa-key="pk_WrQkewYFVUq5gMFyYbDiPUrktSMk1n4h"
        strategy="afterInteractive"
      />
    </main>
  );
}
