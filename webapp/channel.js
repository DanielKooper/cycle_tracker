/* ══════════════════════════════════════════════════════════════
   Bloom Channel — ссылка на канал: карточка на главной + настройки
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var CHANNEL = '';      // придёт с сервера из /api/config (переменная CHANNEL_URL)
  var FALLBACK = '';     // запасная ссылка, если сервер недоступен — можно вписать сюда

  function url() { return CHANNEL || FALLBACK; }

  var css = document.createElement('style');
  css.textContent =
    '.ch-card{display:flex;align-items:center;gap:12px;position:relative;padding-right:36px;' +
      'background:linear-gradient(135deg,var(--accent-soft),var(--card))}' +
    '.ch-ico{width:44px;height:44px;border-radius:14px;flex-shrink:0;display:flex;align-items:center;justify-content:center;' +
      'font-size:20px;background:linear-gradient(135deg,var(--g1),var(--g2));box-shadow:0 5px 14px rgba(0,0,0,.13)}' +
    '.ch-txt{flex:1;min-width:0}' +
    '.ch-txt b{display:block;font-size:14.5px;font-weight:800;letter-spacing:-.2px}' +
    '.ch-txt i{display:block;font-style:normal;font-size:12px;color:var(--muted);font-weight:600;margin-top:2px;line-height:1.4}' +
    '.ch-btn{width:auto;flex-shrink:0;padding:10px 16px;font-size:13px;border-radius:13px}' +
    '.ch-x{position:absolute;top:8px;right:8px;width:26px;height:26px;border:none;border-radius:9px;' +
      'background:transparent;color:var(--muted);cursor:pointer;font-size:12px}';
  document.head.appendChild(css);

  var TXT = {
    ru: { title: 'Bloom в Telegram', sub: 'Новости, советы и обновления приложения', btn: 'Подписаться', set: 'Наш канал', setSub: 'Новости и советы Bloom', open: 'Открыть' },
    en: { title: 'Bloom on Telegram', sub: 'News, tips and app updates', btn: 'Subscribe', set: 'Our channel', setSub: 'Bloom news and tips', open: 'Open' },
    uk: { title: 'Bloom у Telegram', sub: 'Новини, поради та оновлення застосунку', btn: 'Підписатися', set: 'Наш канал', setSub: 'Новини та поради Bloom', open: 'Відкрити' }
  };
  function t() { return TXT[DB.lang] || TXT.ru; }

  /* забираем ссылку с сервера */
  if (location.protocol === 'http:' || location.protocol === 'https:') {
    fetch(location.origin + '/api/config')
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.channel) { CHANNEL = j.channel; renderCurrent(); }
      })
      .catch(function () {});
  }

  /* карточка на главном экране */
  var _rt = renderToday;
  renderToday = function () {
    _rt();
    if (!url() || DB.channelHidden) return;
    var tab = document.getElementById('tab-today');
    var card = document.createElement('div');
    card.className = 'card ch-card';
    card.innerHTML =
      '<button class="ch-x" data-a="channel-hide">✕</button>' +
      '<div class="ch-ico">📣</div>' +
      '<div class="ch-txt"><b>' + t().title + '</b><i>' + t().sub + '</i></div>' +
      '<button class="btn btn-p ch-btn" data-a="channel-open">' + t().btn + '</button>';
    tab.appendChild(card);
  };

  /* пункт в настройках */
  var _os = openSettings;
  openSettings = function () {
    _os();
    if (!url()) return;
    var row = document.createElement('div');
    row.className = 'set-row';
    row.innerHTML =
      '<div><div class="t">📣 ' + t().set + '</div><div class="s">' + t().setSub + '</div></div>' +
      '<button class="chip" data-a="channel-open">' + t().open + '</button>';
    document.getElementById('sheet').appendChild(row);
  };

  /* клики */
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-a]');
    if (!el) return;
    if (el.dataset.a === 'channel-open') {
      var u = url();
      if (!u) return;
      haptic('light');
      if (TG && TG.openTelegramLink) TG.openTelegramLink(u);
      else window.open(u, '_blank');
    } else if (el.dataset.a === 'channel-hide') {
      DB.channelHidden = true;
      save();
      renderCurrent();
    }
  });

  renderCurrent();
})();
