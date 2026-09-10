/* Beplus Site Assistant external loader. It mounts the exact WordPress widget runtime. */
(function (window, document) {
  'use strict';
  var tag = document.currentScript || document.querySelector('script[data-bsa-api]');
  if (!tag || window.__bsaExternalBooted) return;
  window.__bsaExternalBooted = true;
  var base = (tag.dataset.bsaApi || '').replace(/\/$/, '');
  if (!base) return;

  function loadScript(src) {
    var node = document.createElement('script');
    node.src = src; node.async = true;
    document.body.appendChild(node);
  }
  function loadStyle(href) {
    var node = document.createElement('link');
    node.rel = 'stylesheet'; node.href = href;
    document.head.appendChild(node);
  }

  fetch(base + '/embed/config', { credentials: 'omit', cache: 'no-store' })
    .then(function (response) { if (!response.ok) throw new Error('config unavailable'); return response.json(); })
    .then(function (payload) {
      if (!payload || !payload.ok || !payload.config) throw new Error('invalid config');
      var cfg = payload.config;
      // bsaChat is the same contract WordPress injects before chat-widget.js.
      // Only the chat transport differs; all UI/animation/FAQ behavior stays shared.
      window.bsaChat = Object.assign({}, cfg, {
        restUrl: '', nonce: '', frontend: true,
        externalEmbed: true,
        externalChatUrl: base + '/embed/chat',
        deferLoad: false
      });
      loadStyle(cfg.widgetCssUrl);
      loadScript(cfg.widgetJsUrl);
    })
    .catch(function () { /* Keep a denied/unavailable embed silent for visitors. */ });
}(window, document));
