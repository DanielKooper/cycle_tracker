/* ══════════════════════════════════════════════════════════════
   Bloom Care — расширенные советы партнёру + языки RU / EN / UK
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  if (!DB.lang) DB.lang = 'ru';
  if (!DB.plus) DB.plus = { packs: [] };

  var LANGS = [
    { id: 'ru', label: '🇷🇺 Русский' },
    { id: 'en', label: '🇬🇧 English' },
    { id: 'uk', label: '🇺🇦 Українська' }
  ];

  var TITLE = {
    ru: '💞 Как поддержать сейчас',
    en: '💞 How to support now',
    uk: '💞 Як підтримати зараз'
  };

  var PLUS_TITLE = {
    ru: '👑 Забота+',
    en: '👑 Care+',
    uk: '👑 Турбота+'
  };

  var TIPS = {
    ru: {
      menstrual: {
        base: [
          'Принеси тёплый плед и что-то вкусное 🍫',
          'Спроси, нужно ли обезболивающее 💊',
          'Возьми на себя бытовые дела сегодня 🧹',
          'Не обесценивай боль фразами «потерпи» 🫶'
        ],
        plus: [
          'Свари имбирный чай — он может облегчить спазмы 🍵',
          'Включи её любимый сериал и просто побудь рядом 🛋️'
        ]
      },
      follicular: {
        base: [
          'Отличное время для свидания — позови куда-нибудь 🌷',
          'Предложи активность: прогулку, спорт, поездку 🚴',
          'Поддержи её новые идеи и начинания 💡',
          'Сделай комплимент её энергии и инициативе ✨'
        ],
        plus: [
          'Спланируйте мини-приключение на выходные 🗺️',
          'Спроси про её цели — сейчас она готова свернуть горы 🏔️'
        ]
      },
      fertile: {
        base: [
          'Она может чувствовать себя уверенно — поддержи это 🌟',
          'Запланируй что-то приятное вместе 🎉',
          'Комплименты сейчас работают особенно хорошо 💐',
          'Если беременность не в планах — будьте внимательнее 🤍'
        ],
        plus: [
          'Устрой вечер без телефонов — только вы двое 🕯️',
          'Скажи, что гордишься ей. Конкретно, за что 💌'
        ]
      },
      ovulation: {
        base: [
          'Энергия на пике — стройте совместные планы ✨',
          'Время для романтики и близких разговоров 💞',
          'Не откладывай важные разговоры — момент лучший 🗣️',
          'Предложи красивое место или новый опыт 📸'
        ],
        plus: [
          'Идеальный день для важного совместного решения 💍',
          'Прогулка в новом месте — она сегодня сияет 🌟'
        ]
      },
      luteal: {
        base: [
          'Больше терпения: возможен ПМС 🍂',
          'Не спорь по мелочам — обними вместо слов 🤗',
          'Купи её любимые вкусняшки заранее 🛍️',
          'Снизь expectations: ей может быть тяжелее концентрироваться 🫶'
        ],
        plus: [
          'Возьми ужин на себя — готовка или доставка 🍜',
          'Спроси «чем помочь?» вместо «что случилось?» 💬'
        ]
      },
      late: {
        base: [
          'Задержка = стресс. Не нагнетай и не паникуй 🫶',
          'Мягко спроси, как она себя чувствует 💬',
          'Если задержка долгая — предложи сходить к врачу вместе 🩺',
          'Не шути про беременность, если она тревожится 🤍'
        ],
        plus: [
          'Купи тест, если она переживает — без давления 🧪',
          'Напомни, что ты рядом при любом результате 🫂'
        ]
      }
    },

    en: {
      menstrual: {
        base: [
          'Bring a warm blanket and something tasty 🍫',
          'Ask if she needs pain relief 💊',
          'Take over chores today 🧹',
          'Don’t dismiss pain with “just tolerate it” 🫶'
        ],
        plus: [
          'Make ginger tea — it may ease cramps 🍵',
          'Put on her favorite show and just be there 🛋️'
        ]
      },
      follicular: {
        base: [
          'Great time for a date — invite her out 🌷',
          'Suggest activity: walk, sport, trip 🚴',
          'Support her new ideas and plans 💡',
          'Compliment her energy and initiative ✨'
        ],
        plus: [
          'Plan a mini-adventure for the weekend 🗺️',
          'Ask about her goals — she’s ready to move mountains 🏔️'
        ]
      },
      fertile: {
        base: [
          'She may feel confident — support that 🌟',
          'Plan something nice together 🎉',
          'Compliments land especially well now 💐',
          'If pregnancy isn’t planned — be careful 🤍'
        ],
        plus: [
          'Have a phone-free evening — just the two of you 🕯️',
          'Tell her you’re proud of her. Be specific 💌'
        ]
      },
      ovulation: {
        base: [
          'Energy is high — make plans together ✨',
          'Time for romance and close conversations 💞',
          'Don’t postpone important talks — timing is great 🗣️',
          'Suggest a beautiful place or new experience 📸'
        ],
        plus: [
          'A great day for an important shared decision 💍',
          'Walk somewhere new — she’s glowing today 🌟'
        ]
      },
      luteal: {
        base: [
          'More patience: PMS may happen 🍂',
          'Don’t argue over small things — hug instead 🤗',
          'Buy her favorite treats in advance 🛍️',
          'Lower expectations: focus may be harder 🫶'
        ],
        plus: [
          'Handle dinner — cook or order in 🍜',
          'Ask “how can I help?” instead of “what happened?” 💬'
        ]
      },
      late: {
        base: [
          'Late period = stress. Don’t amplify panic 🫶',
          'Gently ask how she feels 💬',
          'If it’s long — offer to see a doctor together 🩺',
          'Don’t joke about pregnancy if she’s anxious 🤍'
        ],
        plus: [
          'Buy a test if she’s worried — no pressure 🧪',
          'Remind her you’re there no matter the result 🫂'
        ]
      }
    },

    uk: {
      menstrual: {
        base: [
          'Принеси теплу ковдру і щось смачне 🍫',
          'Запитай, чи потрібне знеболювальне 💊',
          'Візьми на себе побутові справи сьогодні 🧹',
          'Не знецінюй біль фразами «просто потерпи» 🫶'
        ],
        plus: [
          'Завари імбирний чай — він може полегшити спазми 🍵',
          'Увімкни її улюблений серіал і просто будь поруч 🛋️'
        ]
      },
      follicular: {
        base: [
          'Чудовий час для побачення — запроси кудись 🌷',
          'Запропонуй активність: прогулянку, спорт, поїздку 🚴',
          'Підтримай її нові ідеї та починання 💡',
          'Зроби комплімент її енергії та ініціативі ✨'
        ],
        plus: [
          'Сплануйте міні-пригоду на вихідні 🗺️',
          'Запитай про її цілі — зараз вона готова звернути гори 🏔️'
        ]
      },
      fertile: {
        base: [
          'Вона може почуватися впевнено — підтримай це 🌟',
          'Заплануй щось приємне разом 🎉',
          'Компліменти зараз працюють особливо добре 💐',
          'Якщо вагітність не в планах — будьте уважні 🤍'
        ],
        plus: [
          'Влаштуй вечір без телефонів — лише ви двоє 🕯️',
          'Скажи, що пишаєшся нею. Конкретно, за що 💌'
        ]
      },
      ovulation: {
        base: [
          'Енергія на піку — будуйте спільні плани ✨',
          'Час для романтики й близьких розмов 💞',
          'Не відкладай важливі розмови — момент найкращий 🗣️',
          'Запропонуй гарне місце або новий досвід 📸'
        ],
        plus: [
          'Ідеальний день для важливого спільного рішення 💍',
          'Прогулянка в новому місці — вона сьогодні сяє 🌟'
        ]
      },
      luteal: {
        base: [
          'Більше терпіння: можливий ПМС 🍂',
          'Не сперечайся через дрібниці — обійми замість слів 🤗',
          'Купи її улюблені смаколики заздалегідь 🛍️',
          'Знизь очікування: їй може бути важче концентруватися 🫶'
        ],
        plus: [
          'Візьми вечерю на себе — приготуй або замов 🍜',
          'Запитай «чим допомогти?» замість «що сталося?» 💬'
        ]
      },
      late: {
        base: [
          'Затримка = стрес. Не нагнітай і не панікуй 🫶',
          'М’яко запитай, як вона почувається 💬',
          'Якщо затримка довга — запропонуй сходити до лікаря разом 🩺',
          'Не жартуй про вагітність, якщо вона тривожиться 🤍'
        ],
        plus: [
          'Купи тест, якщо вона переживає — без тиску 🧪',
          'Нагадай, що ти поруч за будь-якого результату 🫂'
        ]
      }
    }
  };

  function hasCarePlus() {
    return DB.plus.packs.indexOf('all') >= 0 || DB.plus.packs.indexOf('care') >= 0;
  }

  function tipsFor(phase) {
    var lang = TIPS[DB.lang] ? DB.lang : 'ru';
    var p = TIPS[lang][phase] || TIPS[lang].follicular;
    var list = p.base.slice();
    if (hasCarePlus()) list = list.concat(p.plus);
    return list;
  }

  /* Настройки: выбор языка */
  var _os = openSettings;
  openSettings = function () {
    _os();
    var box = document.createElement('div');
    box.className = 'f-group';
    box.innerHTML = '<div class="f-label">🌍 Language / Мова</div><div class="chips">' +
      LANGS.map(function (l) {
        return '<button class="chip' + (DB.lang === l.id ? ' on' : '') + '" data-a="care-lang" data-lang="' + l.id + '">' + l.label + '</button>';
      }).join('') + '</div>';
    document.getElementById('sheet').appendChild(box);
  };

  /* Партнёр: заменяем советы на расширенные и локализованные */
  var _rp = renderPartner;
  renderPartner = function () {
    _rp();
    var cards = document.querySelectorAll('#tab-partner .p-card');
    cards.forEach(function (card, i) {
      var x = DB.partners[i];
      if (!x) return;
      var st = statsOf(x.p.s, [], x.p.c || 28, x.p.p || 5);
      var m = model(st);
      var phase = (m && m.phase) || 'follicular';
      var care = card.querySelector('.care');
      if (!care) return;
      var h4 = care.querySelector('h4');
      var ul = care.querySelector('ul');
      if (h4) h4.textContent = hasCarePlus() ? (PLUS_TITLE[DB.lang] || PLUS_TITLE.ru) : (TITLE[DB.lang] || TITLE.ru);
      if (ul) {
        ul.innerHTML = tipsFor(phase).map(function (t) {
          return '<li>' + t + '</li>';
        }).join('');
      }
    });
  };

  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-a="care-lang"]');
    if (!el) return;
    DB.lang = el.dataset.lang;
    save();
    haptic('ok');
    toast(DB.lang === 'ru' ? 'Язык изменён 🌍' : DB.lang === 'uk' ? 'Мову змінено 🌍' : 'Language updated 🌍');
    openSettings();
    renderCurrent();
  });

  renderCurrent();
})();
