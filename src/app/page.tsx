import Script from "next/script";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.main}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>Beplus Site Assistant</p>
        <h1>One assistant.<br />Any website.</h1>
        <p className={styles.lede}>
          This Next.js landing page has no WordPress runtime. The floating assistant is loaded by one external script and uses the same configured knowledge source.
        </p>
        <div className={styles.actions}><a href="#demo">View embed demo</a><a className={styles.secondary} href="#how">How it works</a></div>
      </section>
      <section id="demo" className={styles.grid}>
        <article><span>01</span><h2>Standalone script</h2><p>A small browser-only widget mounts after your landing becomes interactive.</p></article>
        <article><span>02</span><h2>No secret in browser</h2><p>The snippet only contains a public API URL and site identifier. Keys remain in WordPress.</p></article>
        <article><span>03</span><h2>Shared assistant data</h2><p>FAQ, knowledge, guardrails, and answer pipeline stay in the Beplus Site Assistant plugin.</p></article>
      </section>
      <section id="how" className={styles.note}><strong>Live WordPress knowledge</strong><p>The widget is live-connected to Beplus Site Assistant on WordPress. This Vercel page uses a server-side bridge only because the VPS test WordPress instance is HTTP; browser code never receives an AI key.</p></section>
      <Script src="/embed.js" data-bsa-api="/api/beplus-site-assistant/v1" data-bsa-site="beplus-nextjs-demo" strategy="afterInteractive" />
    </main>
  );
}
