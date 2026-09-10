/* Beplus Site Assistant external embed — no API key is ever shipped to the browser. */
(function (window, document) {
  'use strict';
  var script = document.currentScript || document.querySelector('script[data-bsa-api]');
  if (!script || window.__bsaExternalLoaded) return;
  window.__bsaExternalLoaded = true;

  var apiBase = (script.dataset.bsaApi || '').replace(/\/$/, '');
  if (!apiBase) return;
  var configUrl = apiBase + '/embed/config';
  var storagePrefix = 'bsa-external:' + (script.dataset.bsaSite || 'default');
  var clientId = localStorage.getItem(storagePrefix + ':client') || ('bsa_' + crypto.getRandomValues(new Uint32Array(2)).join(''));
  localStorage.setItem(storagePrefix + ':client', clientId);

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) { node.setAttribute(key, attrs[key]); });
    if (text) node.textContent = text;
    return node;
  }
  function addMessage(stream, text, who) {
    var m = el('div', { class: 'bsae-message bsae-' + who }, text);
    stream.appendChild(m); stream.scrollTop = stream.scrollHeight;
  }
  function styles(accent) {
    return '.bsae-root{position:fixed;right:20px;bottom:20px;z-index:2147483000;font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:#0f172a}.bsae-root *{box-sizing:border-box}.bsae-launch{width:56px;height:56px;border:0;border-radius:50%;float:right;background:' + accent + ';color:#fff;font-size:24px;cursor:pointer;box-shadow:0 10px 28px rgba(15,23,42,.25)}.bsae-panel{display:none;clear:both;width:min(372px,calc(100vw - 32px));margin-bottom:12px;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 22px 70px rgba(15,23,42,.22)}.bsae-root.open .bsae-panel{display:block}.bsae-head{padding:16px 18px;background:#0f172a;color:#fff}.bsae-head strong,.bsae-head small{display:block}.bsae-head small{color:#cbd5e1}.bsae-stream{height:300px;overflow:auto;padding:16px;background:#f8fafc}.bsae-message{max-width:88%;margin:0 0 10px;padding:10px 12px;border-radius:14px;white-space:pre-wrap}.bsae-bot{background:#fff;border:1px solid #e2e8f0}.bsae-user{margin-left:auto;background:' + accent + ';color:#fff}.bsae-form{display:flex;gap:8px;padding:12px;border-top:1px solid #e2e8f0}.bsae-form input{min-width:0;flex:1;border:1px solid #cbd5e1;border-radius:10px;padding:10px}.bsae-form button{border:0;border-radius:10px;padding:10px 13px;background:' + accent + ';color:#fff;font-weight:700;cursor:pointer}@media(max-width:480px){.bsae-root{right:12px;bottom:12px}.bsae-stream{height:260px}}';
  }
  fetch(configUrl, { credentials: 'omit' }).then(function (r) { if (!r.ok) throw new Error('not authorized'); return r.json(); }).then(function (payload) {
    var cfg = payload.config || {}; var accent = cfg.accent || '#0d9488';
    document.head.appendChild(el('style', {}, styles(accent)));
    var root = el('section', { class: 'bsae-root', 'aria-label': 'Chat assistant' });
    var panel = el('div', { class: 'bsae-panel', role: 'dialog', 'aria-label': cfg.botName || 'Assistant' });
    var head = el('div', { class: 'bsae-head' }); head.appendChild(el('strong', {}, cfg.botName || 'Beplus Assistant')); head.appendChild(el('small', {}, cfg.botStatus || 'Always active'));
    var stream = el('div', { class: 'bsae-stream', 'aria-live': 'polite' }); addMessage(stream, cfg.welcome || 'How can I help?', 'bot');
    var form = el('form', { class: 'bsae-form' }); var input = el('input', { type: 'text', maxlength: '300', placeholder: cfg.placeholder || 'Ask anything…', 'aria-label': 'Message' }); var send = el('button', { type: 'submit' }, 'Send'); form.appendChild(input); form.appendChild(send);
    panel.appendChild(head); panel.appendChild(stream); panel.appendChild(form);
    var launch = el('button', { class: 'bsae-launch', type: 'button', 'aria-label': 'Open chat', 'aria-expanded': 'false' }, '✦');
    launch.addEventListener('click', function () { var open = root.classList.toggle('open'); launch.setAttribute('aria-expanded', String(open)); if (open) input.focus(); });
    form.addEventListener('submit', function (event) {
      event.preventDefault(); var message = input.value.trim(); if (!message) return; input.value = ''; addMessage(stream, message, 'user'); send.disabled = true;
      fetch(cfg.apiUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'omit', body: JSON.stringify({ message: message, url: location.href, client_id: clientId, session_id: clientId, elapsed: 3, lang: document.documentElement.lang || 'en' }) })
        .then(function (r) { return r.json(); }).then(function (data) { addMessage(stream, data.ok ? data.answer : (data.error || 'Please try again later.'), 'bot'); })
        .catch(function () { addMessage(stream, 'Unable to connect right now. Please try again.', 'bot'); })
        .finally(function () { send.disabled = false; input.focus(); });
    });
    root.appendChild(panel); root.appendChild(launch); document.body.appendChild(root);
  }).catch(function () { /* Config/origin is deliberately silent to visitors. */ });
}(window, document));
