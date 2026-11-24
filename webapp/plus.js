/* ══════════════════════════════════════════════════════════════
   Bloom Plus — покупка Stars в один тап прямо внутри WebApp
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var CATALOG = [
    { id: 'analytics', emoji: '📊', title: 'Глубокая аналитика', desc: 'ПМС-окно, фазы и разброс цикла', stars: 50 },
    { id: 'care',      emoji: '💞', title: 'Забота+',            desc: 'Продвинутые советы партнёру',   stars: 75 },
    { id: 'pdf',       emoji: '📥', title: 'PDF-отчёт',          desc: 'Отчёт для врача в один тап',    stars: 30 },
    { id: 'all',       emoji: '👑', title: 'Всё навсегда',       desc: 'Все функции Plus сразу',        stars: 149, best: true }
  ];
  var NAMES = {}; CATALOG.forEach(function (p) { NAMES[p.id] = p.emoji + ' ' + p.title; });

  if (!DB.plus) DB.plus = { packs: [] };
  function has(f) { return DB.plus.packs.indexOf('all') >= 0 || DB.plus.packs.indexOf(f) >= 0; }
  function grant(f) { if (DB.plus.packs.indexOf(f) < 0) { DB.plus.packs.push(f); save(); } }

  var API = (location.protocol === 'http:' || location.protocol === 'https:') ? location.origin : '';
  var INIT = (TG && TG.initData) ? TG.initData : '';
  var busy = null;

  /* ── стили модуля ── */
  var css = document.createElement('style');
  css.textContent =
    '.bp-sub{font-size:13.5px;color:var(--muted);font-weight:600;line-height:1.5;margin:-4px 0 16px}' +
    '.bp-item{display:flex;align-items:center;gap:13px;width:100%;text-align:left;cursor:pointer;' +
      'background:var(--bg);border:1.5px solid var(--line);border-radius:18px;padding:13px 14px;margin-bottom:9px;' +
      'font-family:inherit;color:var(--ink);transition:transform .15s,border-color .2s,box-shadow .2s;position:relative;overflow:hidden}' +
    '.bp-item:active{transform:scale(.975)}' +
    '.bp-item:not(.owned):hover{border-color:var(--accent);box-shadow:0 6px 18px rgba(0,0,0,.07)}' +
    '.bp-item.best{border-color:var(--accent);background:linear-gradient(135deg,var(--accent-soft),var(--bg))}' +
    '.bp-item.owned{opacity:.72;cursor:default}' +
    '.bp-item.busy{border-color:var(--accent)}' +
    '.bp-ico{width:44px;height:44px;flex-shrink:0;border-radius:14px;display:flex;align-items:center;justify-content:center;' +
      'font-size:21px;background:linear-gradient(135deg,var(--g1),var(--g2));box-shadow:0 5px 14px rgba(0,0,0,.13)}' +
    '.bp-txt{flex:1;min-width:0}' +
    '.bp-txt b{display:block;font-size:14.5px;font-weight:800;letter-spacing:-.2px}' +
    '.bp-txt i{display:block;font-style:normal;font-size:12px;color:var(--muted);font-weight:600;margin-top:2px}' +
    '.bp-price{flex-shrink:0;font-size:13.5px;font-weight:800;color:var(--accent-ink);background:var(--card);' +
      'border:1.5px solid var(--line);border-radius:99px;padding:7px 12px;white-space:nowrap}' +
    '.bp-item.owned .bp-price{background:var(--accent);border-color:var(--accent);color:#fff}' +
    '.bp-badge{position:absolute;top:0;right:0;font-size:9.5px;font-weight:800;letter-spacing:.6px;' +
      'background:var(--accent);color:#fff;padding:3px 9px;border-radius:0 16px 0 12px}' +
    '.bp-spin{width:15px;height:15px;border-radius:50%;border:2.5px solid var(--accent-soft);' +
      'border-top-color:var(--accent);display:inline-block;animation:bpspin .7s linear infinite;vertical-align:-3px}' +
    '@keyframes bpspin{to{transform:rotate(360deg)}}' +
    '.bp-note{font-size:11.5px;color:var(--muted);font-weight:600;text-align:center;line-height:1.5;margin-top:12px}' +
    '.bp-restore{background:none;border:none;color:var(--accent-ink);font-family:inherit;font-weight:700;' +
      'font-size:13px;cursor:pointer;padding:10px;width:100%}' +
    '#bp-confetti{position:fixed;inset:0;z-index:400;pointer-events:none}' +
    '.bp-status{display:flex;align-items:center;gap:9px;background:var(--accent-soft);border-radius:15px;' +
      'padding:11px 14px;margin-bottom:12px;font-size:13px;font-weight:700;color:var(--accent-ink)}';
  document.head.appendChild(css);

  /* ── витрина Plus ── */
  function sheetHTML() {
    var owned = DB.plus.packs.length;
    var h = head('👑 Bloom Plus');
    if (owned) {
      h += '<div class="bp-status">✨ Активно: ' +
        DB.plus.packs.map(function (p) { return NAMES[p] || p; }).join(' · ') + '</div>';
    }
    h += '<p class="bp-sub">Нажми на нужный товар — счёт Telegram Stars откроется прямо здесь. ' +
         'Оплата в два касания, функция включится сразу. Базовое приложение всегда бесплатно 💗</p>';
    CATALOG.forEach(function (p) {
      var own = has(p.id);
      var isBusy = busy === p.id;
      h += '<button class="bp-item' + (own ? ' owned' : '') + (isBusy ? ' busy' : '') + (p.best ? ' best' : '') + '"' +
        (own ? '' : ' data-a="plus-buy" data-pack="' + p.id + '"') + '>' +
        (p.best && !own ? '<span class="bp-badge">ВЫГОДНО</span>' : '') +
        '<span class="bp-ico">' + p.emoji + '</span>' +
        '<span class="bp-txt"><b>' + p.title + '</b><i>' + p.desc + '</i></span>' +
        '<span class="bp-price">' + (own ? '✓ Куплено' : (isBusy ? '<span class="bp-spin"></span>' : p.stars + ' ⭐')) + '</span>' +
        '</button>';
    });
    h += '<button class="bp-restore" data-a="plus-restore">↻ Восстановить покупки</button>';
    h += '<p class="bp-note">Оплата звёздами Telegram ⭐ · возврат по команде /refund в боте<br>' +
         'Покупки привязаны к твоему Telegram-аккаунту</p>';
    h += '<div style="height:6px"></div><button class="btn btn-g" data-a="sheet-close">Закрыть</button>';
    return h;
  }

  function refreshSheet() {
    if (document.getElementById('ov').classList.contains('on') &&
        document.querySelector('.bp-item')) {
      openSheet(sheetHTML());
    }
  }

  openPlus = function () { busy = null; openSheet(sheetHTML()); };

  /* ── покупка ── */
  function buy(pack) {
    if (busy) return;
    if (!TG || !INIT) { toast('Открой Bloom внутри Telegram 🌸'); return; }
    if (!API) { toast('Покупки доступны в онлайн-версии'); return; }
    if (!TG.openInvoice) { toast('Обнови Telegram до последней версии 📲'); return; }

    busy = pack; refreshSheet(); haptic('light');

    fetch(API + '/api/invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pack: pack, initData: INIT })
    })
      .then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); })
      .then(function (res) {
        if (!res.j || !res.j.ok || !res.j.link) {
          busy = null; refreshSheet();
          toast(res.s === 401 ? 'Сессия устарела — перезапусти Bloom 🔄' : 'Не удалось создать счёт 😔');
          return;
        }
        var done = false;
        var finish = function (status) {
          if (done) return; done = true;
          busy = null;
          if (status === 'paid') {
            grant(pack);
            haptic('ok'); celebrate();
            toast('Готово! ' + (NAMES[pack] || 'Plus') + ' открыт 👑');
            refreshSheet(); renderCurrent();
            setTimeout(sync, 1600);
          } else if (status === 'cancelled') {
            toast('Покупка отменена'); refreshSheet();
          } else if (status === 'pending') {
            toast('Платёж обрабатывается ⏳'); refreshSheet(); setTimeout(sync, 2500);
          } else {
            toast('Платёж не прошёл 😔'); refreshSheet();
          }
        };
        try { TG.openInvoice(res.j.link, finish); }
        catch (e) { busy = null; refreshSheet(); toast('Не удалось открыть счёт 😔'); }
        try { TG.onEvent('invoiceClosed', function (ev) { finish(ev && ev.status); }); } catch (e) {}
      })
      .catch(function () {
        busy = null; refreshSheet();
        toast('Нет связи с сервером 📡');
      });
  }

  /* ── синхронизация покупок с сервером ── */
  function sync(quiet) {
    if (!API || !INIT) return;
    fetch(API + '/api/me?initData=' + encodeURIComponent(INIT))
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok || !Array.isArray(j.packs)) return;
        var changed = false;
        j.packs.forEach(function (p) {
          if (NAMES[p] && DB.plus.packs.indexOf(p) < 0) { DB.plus.packs.push(p); changed = true; }
        });
        if (changed) { save(); renderCurrent(); refreshSheet(); }
        if (!quiet) toast(changed ? 'Покупки восстановлены 👑' : 'Все покупки уже активны ✨');
      })
      .catch(function () { if (!quiet) toast('Сервер недоступен 📡'); });
  }

  /* ── салют при покупке ── */
  function celebrate() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var c = document.createElement('canvas');
    c.id = 'bp-confetti';
    document.body.appendChild(c);
    var ctx = c.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    c.width = innerWidth * dpr; c.height = innerHeight * dpr;
    ctx.scale(dpr, dpr);
    var cs = getComputedStyle(document.documentElement);
    var cols = ['--g1', '--g2', '--accent', '--fer', '--ovu'].map(function (v) {
      return cs.getPropertyValue(v).trim() || '#F5567B';
    });
    var ps = [];
    for (var i = 0; i < 90; i++) {
      ps.push({
        x: innerWidth / 2 + (Math.random() - .5) * 120,
        y: innerHeight * .42,
        vx: (Math.random() - .5) * 9,
        vy: -Math.random() * 13 - 4,
        s: Math.random() * 7 + 4,
        r: Math.random() * Math.PI,
        vr: (Math.random() - .5) * .3,
        c: cols[i % cols.length]
      });
    }
    var t0 = performance.now();
    (function loop(t) {
      var el = t - t0;
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      ps.forEach(function (p) {
        p.vy += .42; p.x += p.vx; p.y += p.vy; p.r += p.vr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r);
        ctx.globalAlpha = Math.max(0, 1 - el / 1500);
        ctx.fillStyle = p.c;
        ctx.fillRect(-p.s / 2, -p.s / 2, p.s, p.s * .62);
        ctx.restore();
      });
      if (el < 1500) requestAnimationFrame(loop); else c.remove();
    })(t0);
  }

  /* ── настройки: статус Plus ── */
  var _os = openSettings;
  openSettings = function () {
    _os();
    var box = document.createElement('div');
    box.className = 'f-group';
    box.innerHTML = '<div class="f-label">👑 Bloom Plus</div>' +
      (DB.plus.packs.length
        ? '<p class="muted" style="margin-bottom:9px">Активно: ' +
          DB.plus.packs.map(function (p) { return NAMES[p] || p; }).join(', ') + '</p>'
        : '<p class="muted" style="margin-bottom:9px">Дополнения за звёзды Telegram — покупка в один тап ⭐</p>') +
      '<div class="btn-row"><button class="btn btn-s" data-a="plus">Открыть магазин</button>' +
      '<button class="btn btn-g" data-a="plus-restore">↻ Восстановить</button></div>';
    document.getElementById('sheet').appendChild(box);
  };

  /* ── платная аналитика + PDF ── */
  var _rs = renderStats;
  renderStats = function () {
    _rs();
    var st = myStats(); if (!st.starts.length) return;
    var m = model(st), tab = document.getElementById('tab-stats');
    var card = document.createElement('div');
    if (has('analytics') && m && !m.future) {
      card.className = 'card';
      card.innerHTML = '<div class="sec-title">🔬 Глубокая аналитика</div>' +
        '<div class="pred-row"><b>🍂 ПМС-окно</b><span>' + fNice(addD(m.next, -5)) + ' — ' + fNice(addD(m.next, -1)) + '</span></div>' +
        '<div class="pred-row"><b>✨ Овуляция ~</b><span>' + fNice(m.ovu) + '</span></div>' +
        '<div class="pred-row"><b>💫 Фертильно</b><span>' + fNice(addD(m.ovu, -4)) + ' — ' + fNice(addD(m.ovu, 1)) + '</span></div>' +
        (st.gaps.length > 1
          ? '<div class="pred-row"><b>📏 Разброс цикла</b><span>' +
            Math.min.apply(null, st.gaps) + '–' + Math.max.apply(null, st.gaps) + ' дн</span></div>' : '');
    } else {
      card.className = 'card tip-card'; card.setAttribute('data-a', 'plus');
      card.innerHTML = '<div class="sec-title">🔬 Глубокая аналитика 🔒</div>' +
        '<p class="muted">ПМС-окно, точные фазы и разброс цикла — 50 ⭐. Нажми, чтобы купить в один тап.</p>';
    }
    tab.appendChild(card);
    var pb = document.createElement('button');
    pb.className = 'btn ' + (has('pdf') ? 'btn-s' : 'btn-g');
    pb.style.marginTop = '10px';
    pb.setAttribute('data-a', 'pdf-report');
    pb.textContent = has('pdf') ? '🖨 PDF-отчёт для врача' : '🖨 PDF-отчёт · 30 ⭐';
    tab.appendChild(pb);
  };

  /* ── Забота+ ── */
  var CARE_PLUS = {
    menstrual:  ['Свари имбирный чай — он снимает спазмы 🍵', 'Включи её любимый сериал и просто побудь рядом 🛋️'],
    follicular: ['Спланируйте мини-приключение на выходные 🗺️', 'Спроси про её цели — сейчас она готова свернуть горы 🏔️'],
    fertile:    ['Устрой вечер без телефонов — только вы двое 🕯️', 'Скажи, что гордишься ей. Конкретно, за что 💌'],
    ovulation:  ['Идеальный день для важного совместного решения 💍', 'Прогулка в новом месте — она сегодня сияет 📸'],
    luteal:     ['Возьми ужин на себя — готовка или доставка 🍜', 'Спроси «чем помочь?» вместо «что случилось?» 🫶'],
    late:       ['Купи тест, если она переживает — без давления 🤍', 'Напомни, что ты рядом при любом результате 🫂']
  };
  var _rp = renderPartner;
  renderPartner = function () {
    _rp();
    var tab = document.getElementById('tab-partner');
    if (!DB.partners.length) return;
    if (has('care')) {
      tab.querySelectorAll('.p-card').forEach(function (c, i) {
        var x = DB.partners[i]; if (!x) return;
        var st = statsOf(x.p.s, [], x.p.c || 28, x.p.p || 5);
        var m = model(st), ph = (m && m.phase) || 'follicular';
        var ul = c.querySelector('.care ul'); if (!ul) return;
        (CARE_PLUS[ph] || CARE_PLUS.follicular).forEach(function (t) {
          var li = document.createElement('li'); li.textContent = '👑 ' + t; ul.appendChild(li);
        });
      });
    } else {
      var b = document.createElement('button');
      b.className = 'btn btn-g'; b.setAttribute('data-a', 'plus');
      b.textContent = '💞 Забота+ · больше советов · 75 ⭐';
      tab.appendChild(b);
    }
  };

  /* ── PDF-отчёт ── */
  function pdfReport() {
    var st = myStats();
    var rows = DB.periods.slice().sort(function (a, b) { return a.start < b.start ? -1 : 1; })
      .map(function (p) {
        var d = parse(p.start);
        return '<tr><td>' + fNice(d) + ' ' + d.getFullYear() + '</td><td>' + p.len + ' дн</td></tr>';
      }).join('');
    var logs = Object.keys(DB.logs).sort().slice(-30).map(function (d) {
      var l = DB.logs[d];
      var s = (l.syms || []).map(function (k) {
        var f = SYM.find(function (x) { return x[0] === k; }); return f ? f[1] : k;
      }).join(', ');
      return '<tr><td>' + fNice(parse(d)) + '</td><td>' +
        ['—', 'слабые', 'средние', 'сильные'][l.flow || 0] + '</td><td>' + s + '</td><td>' + esc(l.note || '') + '</td></tr>';
    }).join('');
    var html = '<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Bloom — отчёт</title>' +
      '<style>body{font-family:Arial,sans-serif;padding:32px;color:#333}h1{color:#F5567B;margin:0 0 6px}' +
      'table{width:100%;border-collapse:collapse;margin:10px 0 26px}' +
      'td,th{border:1px solid #e6d7de;padding:8px;font-size:13px;text-align:left}th{background:#FFE4EC}' +
      'h3{margin:18px 0 4px}</style></head><body>' +
      '<h1>🌸 Bloom — отчёт о цикле</h1>' +
      '<p>Дата: ' + fFull(today()) + ' · Средний цикл: ' + st.avgC + ' дн · Менструация: ' + st.avgP + ' дн</p>' +
      '<h3>Циклы</h3><table><tr><th>Начало</th><th>Длительность</th></tr>' + rows + '</table>' +
      '<h3>Дневник (последние 30 записей)</h3><table><tr><th>Дата</th><th>Выделения</th><th>Симптомы</th><th>Заметка</th></tr>' + logs + '</table>' +
      '<p style="color:#999;font-size:11px">Сформировано приложением Bloom. Не является медицинским заключением.</p>' +
      '<script>window.print()<\/script></body></html>';
    var w = window.open('', '_blank');
    if (w) { w.document.write(html); w.document.close(); toast('Выбери «Сохранить как PDF» 🖨'); }
    else {
      var txt = 'Bloom — отчёт ' + fFull(today()) + '\nСредний цикл: ' + st.avgC + ' дн\n\nЦиклы:\n' +
        DB.periods.map(function (p) { return p.start + ' (' + p.len + ' дн)'; }).join('\n');
      copyTxt(txt, 'Отчёт скопирован текстом 📋');
    }
  }

  /* ── обработчики ── */
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-a]'); if (!el) return;
    var a = el.dataset.a;
    if (a === 'plus-buy') buy(el.dataset.pack);
    else if (a === 'plus-restore') { haptic('light'); sync(false); }
    else if (a === 'pdf-report') { if (has('pdf')) pdfReport(); else openPlus(); }
  });

  sync(true);
  renderCurrent();
})();
