/*
 * Общие функции для всех форм.
 * Никаких сетевых запросов: данные приходят в ссылке, уходят через sendData.
 */
(function () {
  "use strict";

  var SEND_LIMIT = 4096; // байт, ограничение Telegram

  // Ссылку запоминаем как можно раньше (этот файл грузится до telegram-web-app.js).
  var INITIAL_HREF = String(window.location.href);

  // ---------- чтение параметра d из ссылки ----------

  function paramFrom(part, name) {
    // part: строка вида "a=1&b=2" (без # или ?)
    var pieces = part.split("&");
    for (var i = 0; i < pieces.length; i++) {
      var eq = pieces[i].indexOf("=");
      if (eq > 0 && pieces[i].slice(0, eq) === name) {
        return pieces[i].slice(eq + 1);
      }
    }
    return null;
  }

  function readParam(name) {
    var href = INITIAL_HREF;
    var hashPos = href.indexOf("#");
    var hash = hashPos >= 0 ? href.slice(hashPos + 1) : "";
    var beforeHash = hashPos >= 0 ? href.slice(0, hashPos) : href;
    var qPos = beforeHash.indexOf("?");
    var query = qPos >= 0 ? beforeHash.slice(qPos + 1) : "";
    // Telegram иногда кладёт свои параметры после "?" внутри фрагмента
    var hashValue = paramFrom(hash.replace("?", "&"), name);
    var queryValue = paramFrom(query, name);
    return { hash: hashValue, query: queryValue, href: href };
  }

  // ---------- base64url и распаковка ----------

  function b64urlToBytes(text) {
    var b64 = text.replace(/-/g, "+").replace(/_/g, "/");
    while (b64.length % 4) b64 += "=";
    var bin = atob(b64);
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function hasNativeInflate() {
    try {
      if (typeof DecompressionStream === "undefined") return false;
      new DecompressionStream("deflate-raw");
      return true;
    } catch (e) {
      return false;
    }
  }

  function nativeInflate(bytes) {
    var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Response(stream).arrayBuffer().then(function (buf) {
      return new Uint8Array(buf);
    });
  }

  // Небольшой распаковщик формата DEFLATE (RFC 1951) на случай старого телефона,
  // где нет встроенного DecompressionStream.
  var LBASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258];
  var LEXT = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
  var DBASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
  var DEXT = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];
  var CL_ORDER = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15];

  function jsInflate(src) {
    var pos = 0, bitBuf = 0, bitCnt = 0, out = [];

    function bits(n) {
      while (bitCnt < n) {
        if (pos >= src.length) throw new Error("данные обрезаны");
        bitBuf |= src[pos++] << bitCnt;
        bitCnt += 8;
      }
      var v = bitBuf & ((1 << n) - 1);
      bitBuf >>>= n;
      bitCnt -= n;
      return v;
    }

    function build(lengths) {
      var counts = new Array(16).fill(0), offs = new Array(16).fill(0);
      var syms = new Array(lengths.length);
      for (var i = 0; i < lengths.length; i++) counts[lengths[i]]++;
      counts[0] = 0;
      for (i = 1; i < 16; i++) offs[i] = offs[i - 1] + counts[i - 1];
      for (i = 0; i < lengths.length; i++) if (lengths[i]) syms[offs[lengths[i]]++] = i;
      return { counts: counts, syms: syms };
    }

    function decodeSym(h) {
      var code = 0, first = 0, index = 0;
      for (var len = 1; len < 16; len++) {
        code |= bits(1);
        var count = h.counts[len];
        if (code - count < first) return h.syms[index + (code - first)];
        index += count;
        first = (first + count) << 1;
        code <<= 1;
      }
      throw new Error("ошибка в сжатых данных");
    }

    var fixedLit = null, fixedDist = null;
    function fixedTables() {
      if (!fixedLit) {
        var l = [];
        for (var i = 0; i < 288; i++) l.push(i < 144 ? 8 : i < 256 ? 9 : i < 280 ? 7 : 8);
        var d = [];
        for (i = 0; i < 30; i++) d.push(5);
        fixedLit = build(l);
        fixedDist = build(d);
      }
      return [fixedLit, fixedDist];
    }

    function dynamicTables() {
      var hlit = bits(5) + 257, hdist = bits(5) + 1, hclen = bits(4) + 4;
      var clLens = new Array(19).fill(0);
      for (var i = 0; i < hclen; i++) clLens[CL_ORDER[i]] = bits(3);
      var clTable = build(clLens);
      var lens = [];
      while (lens.length < hlit + hdist) {
        var sym = decodeSym(clTable);
        if (sym < 16) {
          lens.push(sym);
        } else {
          var repeat, value = 0;
          if (sym === 16) {
            if (!lens.length) throw new Error("ошибка в сжатых данных");
            value = lens[lens.length - 1];
            repeat = 3 + bits(2);
          } else if (sym === 17) {
            repeat = 3 + bits(3);
          } else {
            repeat = 11 + bits(7);
          }
          while (repeat--) lens.push(value);
        }
      }
      return [build(lens.slice(0, hlit)), build(lens.slice(hlit))];
    }

    var last = 0;
    while (!last) {
      last = bits(1);
      var type = bits(2);
      if (type === 0) {
        bitBuf = 0; bitCnt = 0; // остаток текущего байта не нужен
        if (pos + 4 > src.length) throw new Error("данные обрезаны");
        var len = src[pos] | (src[pos + 1] << 8);
        pos += 4;
        if (pos + len > src.length) throw new Error("данные обрезаны");
        for (var k = 0; k < len; k++) out.push(src[pos++]);
        continue;
      }
      if (type === 3) throw new Error("ошибка в сжатых данных");
      var t = type === 1 ? fixedTables() : dynamicTables();
      for (;;) {
        var s = decodeSym(t[0]);
        if (s < 256) {
          out.push(s);
        } else if (s === 256) {
          break;
        } else {
          s -= 257;
          if (s >= 29) throw new Error("ошибка в сжатых данных");
          var length = LBASE[s] + bits(LEXT[s]);
          var ds = decodeSym(t[1]);
          if (ds >= 30) throw new Error("ошибка в сжатых данных");
          var dist = DBASE[ds] + bits(DEXT[ds]);
          if (dist > out.length) throw new Error("ошибка в сжатых данных");
          var from = out.length - dist;
          for (var j = 0; j < length; j++) out.push(out[from + j]);
        }
      }
    }
    return new Uint8Array(out);
  }

  // Строка параметра -> объект. Возвращает Promise с {data, method}.
  function decodeParam(text) {
    return new Promise(function (resolve, reject) {
      try {
        var kind = text.charAt(0);
        var bytes = b64urlToBytes(text.slice(1));
        var finish = function (raw, method) {
          var json = new TextDecoder("utf-8").decode(raw);
          resolve({ data: JSON.parse(json), method: method });
        };
        if (kind === "0") return finish(bytes, "без сжатия");
        if (kind !== "1") throw new Error("неизвестный формат");
        if (hasNativeInflate()) {
          nativeInflate(bytes).then(function (raw) { finish(raw, "встроенная"); })
            .catch(function () { finish(jsInflate(bytes), "запасная"); });
        } else {
          finish(jsInflate(bytes), "запасная");
        }
      } catch (e) {
        reject(e);
      }
    });
  }

  // ---------- отправка ----------

  function byteSize(text) {
    return new TextEncoder().encode(text).length;
  }

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    var b = new Uint8Array(16);
    crypto.getRandomValues(b);
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    var h = Array.prototype.map.call(b, function (x) { return (x + 256).toString(16).slice(1); }).join("");
    return h.slice(0, 8) + "-" + h.slice(8, 12) + "-" + h.slice(12, 16) + "-" + h.slice(16, 20) + "-" + h.slice(20);
  }

  // Сегодняшняя дата по часам телефона, в виде 2026-11-20
  function localDate(d) {
    d = d || new Date();
    var m = d.getMonth() + 1, day = d.getDate();
    return d.getFullYear() + "-" + (m < 10 ? "0" : "") + m + "-" + (day < 10 ? "0" : "") + day;
  }

  window.SB = {
    SEND_LIMIT: SEND_LIMIT,
    readParam: readParam,
    decodeParam: decodeParam,
    jsInflate: jsInflate,
    b64urlToBytes: b64urlToBytes,
    hasNativeInflate: hasNativeInflate,
    byteSize: byteSize,
    uuid: uuid,
    localDate: localDate
  };
})();

/*
 * Общие части интерфейса форм: тема, тексты ru/uz, кнопка «Сохранить», черновик, всплывашки.
 */
(function () {
  "use strict";

  // telegram-web-app.js грузится ПОСЛЕ этого файла, поэтому Telegram ищем при каждом обращении
  function tgo() { return window.Telegram && window.Telegram.WebApp; }
  function inTg() { var w = tgo(); return !!(w && w.platform && w.platform !== "unknown"); }

  // Тексты интерфейса. Узбекский — ЧЕРНОВИК, на проверку владельцу.
  var I18N = {
    ru: {
      save: "Сохранить", saveN: "Сохранить · {n}", next: "Следующий", toList: "К списку",
      attendance: "Посещаемость", weekly: "Недельный отчёт", topic: "Тема урока",
      present: "Пришёл", late: "Опоздал", absent: "Не пришёл", excused: "Уважит.",
      presentShort: "Пришли", lateShort: "Опоздали", absentShort: "Нет", excusedShort: "Уважит.",
      allPresent: "Все пришли", tapHint: "Нажмите на ученика, чтобы сменить отметку",
      today: "сегодня", savedForDate: "За этот день уже сохранено — можно исправить",
      part: "Часть {i} из {n}", students: "учеников",
      thisWeek: "Эта неделя", lastWeek: "Прошлая неделя",
      filled: "Заполнено {k} из {n}", done: "готово", saved: "сохранено", empty: "не заполнен",
      comment: "Комментарий для родителя", commentHint: "до 80 букв, можно пусто",
      commentExists: "Комментарий уже сохранён — оставьте пустым, чтобы не менять",
      phrases: "Готовые фразы", card: "карточка",
      fromLastWeek: "Подставлено с прошлой недели — поменяйте, что изменилось",
      answerAll: "Ответьте на все вопросы", great: "Отлично! {k} из {n}", allDone: "Все заполнены! Нажмите «Сохранить»",
      nothingToSave: "Сначала заполните хотя бы одного ученика",
      tooBig: "Помещается {k} из {n}. Отправить их сейчас? Остальные останутся в черновике — откройте отчёт ещё раз.",
      current: "Сейчас", noTopic: "тема не указана", chooseUnit: "Юнит из книги", ownTopic: "Своя тема",
      topicPlaceholder: "Например: Present Simple, неправильные глаголы",
      notInTelegram: "Это просмотр формы. Сохранять можно только из Telegram.",
      broken: "Данные в ссылке повреждены. Откройте форму кнопкой в чате бота.",
      noData: "Откройте форму кнопкой в чате бота.",
      demo: "Демо: все имена выдуманы",
      exam: "Экзамен", decision: "Решение по станции", passScore: "Проходной балл: {p} из {m}",
      scoresUnset: "Владелец ещё не задал проходной и максимальный балл для этой станции. Попросите его: меню → 🎯 Баллы экзаменов.",
      moves: "Переходит", repeat: "Повтор", stays: "Остаётся", changeDecision: "Изменить решение",
      reason: "Причина (обязательно)", reasonPh: "Почему решение отличается от балла",
      otherStage: "на другой станции", path: "Путь после B2", later: "Позже",
      teacherHint: "Переход на этой станции решает учитель. Отметьте, кто переходит дальше.",
      scoreHint: "Введите баллы — решение подставится само", needReason: "Укажите причину, где решение изменено",
      endOfRoute: "конец пути", enterScores: "Введите хотя бы один балл",
      journal: "Журнал группы", reportsWeek: "Недельные отчёты", attToday: "сегодня отмечено",
      attMark: "отметить урок", stations: "Станции", hints: "Подсказки", cards: "Карточки родителям",
      noHints: "подсказок нет", hintsN: "{n} шт.", cardsSub: "готово {k} из {n}", stationsSub: "перевести",
      footer: "Данные уходят боту, когда вы нажимаете «Сохранить» внизу. Ответ бот пришлёт в чат.",
      closeMarked: "Закрыть отмеченные · {n}", markToClose: "Отметьте подсказки, которые уже решены",
      hintsEmpty: "По группе подсказок нет 👍", why: "Почему",
      wholeGroup: "Вся группа", groupNow: "сейчас: {s}", pickStation: "На какую станцию?",
      moveConfirm: "{who}: {from} ➜ {to}", move: "Перевести", skippedNote: "Пропущенные станции не появятся на карте ученика.",
      examRestart: "Экзамены новой станции — каждые 2 месяца с сегодняшнего дня.",
      cardsText: "Бот пришлёт в чат по картинке на каждого ученика, у которого есть отчёт за эту неделю и отметка о согласии родителя. Перешлите каждую карточку родителю.",
      cardsReady: "Готово к отправке", cardsNoReport: "Нет отчёта за неделю", cardsNoConsent: "Нет согласия родителя",
      sendCards: "Прислать карточки · {n}", noExam: "у этого предмета нет экзаменов",
      lv0: "слабо", lv1: "так себе", lv2: "хорошо", lv3: "отлично", optional: "можно пропустить",
      notRated: "не оценивалось на этой неделе", pickLevel: "Выберите уровень",
      starWeek: "Звезда недели", starHint: "На карточке родителю появится значок ★"
    },
    uz: {
      save: "Saqlash", saveN: "Saqlash · {n}", next: "Keyingisi", toList: "Roʻyxatga",
      attendance: "Davomat", weekly: "Haftalik hisobot", topic: "Dars mavzusi",
      present: "Keldi", late: "Kechikdi", absent: "Kelmadi", excused: "Sababli",
      presentShort: "Keldi", lateShort: "Kechikdi", absentShort: "Yoʻq", excusedShort: "Sababli",
      allPresent: "Hammasi keldi", tapHint: "Belgini oʻzgartirish uchun oʻquvchini bosing",
      today: "bugun", savedForDate: "Bu kun uchun saqlangan — tuzatish mumkin",
      part: "{n} tadan {i}-qism", students: "oʻquvchi",
      thisWeek: "Shu hafta", lastWeek: "Oʻtgan hafta",
      filled: "{n} tadan {k} tasi toʻldirildi", done: "tayyor", saved: "saqlangan", empty: "toʻldirilmagan",
      comment: "Ota-ona uchun izoh", commentHint: "80 harfgacha, boʻsh qolishi mumkin",
      commentExists: "Izoh allaqachon saqlangan — oʻzgartirmaslik uchun boʻsh qoldiring",
      phrases: "Tayyor iboralar", card: "karta",
      fromLastWeek: "Oʻtgan haftadan olindi — oʻzgarganini tuzating",
      answerAll: "Barcha savollarga javob bering", great: "Ajoyib! {n} tadan {k}", allDone: "Hammasi toʻldirildi! «Saqlash»ni bosing",
      nothingToSave: "Avval kamida bitta oʻquvchini toʻldiring",
      tooBig: "{n} tadan {k} tasi sigʻadi. Hozir yuborilsinmi? Qolganlari qoralamada qoladi — hisobotni qayta oching.",
      current: "Hozir", noTopic: "mavzu koʻrsatilmagan", chooseUnit: "Kitobdan unit", ownTopic: "Oʻz mavzusi",
      topicPlaceholder: "Masalan: Present Simple, notoʻgʻri feʼllar",
      notInTelegram: "Bu shaklni koʻrish. Faqat Telegram orqali saqlash mumkin.",
      broken: "Havoladagi maʼlumotlar buzilgan. Shaklni bot chatidagi tugma orqali oching.",
      noData: "Shaklni bot chatidagi tugma orqali oching.",
      demo: "Demo: barcha ismlar oʻylab topilgan",
      exam: "Imtihon", decision: "Bosqich boʻyicha qaror", passScore: "Oʻtish bali: {m} dan {p}",
      scoresUnset: "Markaz egasi bu bosqich uchun oʻtish va maksimal ballni hali kiritmagan.",
      moves: "Oʻtadi", repeat: "Qayta", stays: "Qoladi", changeDecision: "Qarorni oʻzgartirish",
      reason: "Sabab (majburiy)", reasonPh: "Nega qaror balldan farq qiladi",
      otherStage: "boshqa bosqichda", path: "B2 dan keyingi yoʻl", later: "Keyinroq",
      teacherHint: "Bu bosqichda oʻtishni oʻqituvchi hal qiladi. Kim oʻtishini belgilang.",
      scoreHint: "Ballarni kiriting — qaror oʻzi qoʻyiladi", needReason: "Qaror oʻzgartirilgan joyda sababini yozing",
      endOfRoute: "yoʻl oxiri", enterScores: "Kamida bitta ball kiriting",
      journal: "Guruh jurnali", reportsWeek: "Haftalik hisobotlar", attToday: "bugun belgilangan",
      attMark: "darsni belgilash", stations: "Bosqichlar", hints: "Maslahatlar", cards: "Ota-onalarga kartalar",
      noHints: "maslahat yoʻq", hintsN: "{n} ta", cardsSub: "{n} tadan {k} tayyor", stationsSub: "oʻtkazish",
      footer: "Pastdagi «Saqlash» bosilganda maʼlumotlar botga ketadi. Javobni bot chatga yuboradi.",
      closeMarked: "Belgilanganlarni yopish · {n}", markToClose: "Hal boʻlgan maslahatlarni belgilang",
      hintsEmpty: "Guruh boʻyicha maslahatlar yoʻq 👍", why: "Sababi",
      wholeGroup: "Butun guruh", groupNow: "hozir: {s}", pickStation: "Qaysi bosqichga?",
      moveConfirm: "{who}: {from} ➜ {to}", move: "Oʻtkazish", skippedNote: "Oʻtkazib yuborilgan bosqichlar xaritada koʻrinmaydi.",
      examRestart: "Yangi bosqich imtihonlari — bugundan boshlab har 2 oyda.",
      cardsText: "Bot shu hafta hisoboti va ota-ona roziligi bor har bir oʻquvchi uchun chatga rasm yuboradi. Har bir kartani ota-onaga yuboring.",
      cardsReady: "Yuborishga tayyor", cardsNoReport: "Hafta hisoboti yoʻq", cardsNoConsent: "Ota-ona roziligi yoʻq",
      sendCards: "Kartalarni yuborish · {n}", noExam: "bu fanda imtihon yoʻq",
      lv0: "sust", lv1: "oʻrtacha", lv2: "yaxshi", lv3: "aʼlo", optional: "oʻtkazish mumkin",
      notRated: "bu hafta baholanmagan", pickLevel: "Darajani tanlang",
      starWeek: "Hafta yulduzi", starHint: "Ota-ona kartasida ★ belgisi paydo boʻladi"
    }
  };
  var lang = "ru";

  function t(key, vars) {
    var text = (I18N[lang] && I18N[lang][key]) || I18N.ru[key] || key;
    if (vars) Object.keys(vars).forEach(function (k) { text = text.split("{" + k + "}").join(vars[k]); });
    return text;
  }

  function setLang(value) { lang = value === "uz" ? "uz" : "ru"; document.documentElement.lang = lang; }

  // Тема: светлая/тёмная по Telegram, шапка и фон в цвет формы
  function applyTheme() {
    var tg = tgo();
    var dark = tg && tg.colorScheme === "dark";
    if (!tg && window.matchMedia) dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    if (!tg) return;
    var bg = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
    try {
      if (tg.isVersionAtLeast && tg.isVersionAtLeast("6.1")) {
        tg.setHeaderColor(bg);
        tg.setBackgroundColor(bg);
      }
    } catch (e) { /* старый Telegram — не страшно */ }
  }

  function haptic(kind) {
    var tg = tgo();
    try {
      if (!tg || !tg.HapticFeedback) return;
      if (kind === "select") tg.HapticFeedback.selectionChanged();
      else if (kind === "success" || kind === "error" || kind === "warning") tg.HapticFeedback.notificationOccurred(kind);
      else tg.HapticFeedback.impactOccurred("light");
    } catch (e) { /* без вибрации */ }
  }

  // Кнопка «Сохранить»: в Telegram — родная MainButton, вне Telegram — кнопка внизу страницы
  var saveHandler = null, fallbackBar = null;
  function setSave(text, handler, visible) {
    saveHandler = handler;
    var tg = tgo();
    if (inTg() && tg.MainButton) {
      tg.MainButton.setParams({ text: text, color: "#ef8a2b", text_color: "#ffffff", is_visible: !!visible });
      return;
    }
    if (!fallbackBar) {
      fallbackBar = document.createElement("div");
      fallbackBar.className = "save-bar";
      var b = document.createElement("button");
      b.className = "btn";
      b.type = "button";
      b.addEventListener("click", function () { if (saveHandler) saveHandler(); });
      fallbackBar.appendChild(b);
      document.body.appendChild(fallbackBar);
    }
    fallbackBar.firstChild.textContent = text;
    fallbackBar.classList.toggle("hidden", !visible);
  }

  // Родная кнопка Telegram «← Назад» в шапке формы (null — спрятать)
  var backHandler = null, backBound = false;
  function setBack(handler) {
    // внутри приложения группы «Назад» без своего действия ведёт на главный экран группы
    if (!handler && window.SB && SB.hubHome) handler = SB.hubHome;
    backHandler = handler;
    var tg = tgo();
    if (!inTg() || !tg.BackButton) return;
    if (!backBound) {
      tg.BackButton.onClick(function () { if (backHandler) backHandler(); });
      backBound = true;
    }
    if (handler) tg.BackButton.show(); else tg.BackButton.hide();
  }

  function send(payload) {
    var text = JSON.stringify(payload);
    if (SB.byteSize(text) > SB.SEND_LIMIT) throw new Error("too big");
    if (!inTg()) {
      toast(t("notInTelegram"), true);
      if (window.console) console.log("sendData", text);
      window.__lastSent = text;
      return false;
    }
    tgo().sendData(text); // Telegram сам закроет форму
    return true;
  }

  function confirmBox(text, callback) {
    var tg = tgo();
    if (inTg() && tg.showConfirm && tg.isVersionAtLeast && tg.isVersionAtLeast("6.2")) {
      tg.showConfirm(text, callback);
    } else {
      callback(window.confirm(text));
    }
  }

  var toastTimer = null;
  function toast(text, bad) {
    var old = document.querySelector(".toast");
    if (old) old.remove();
    var el = document.createElement("div");
    el.className = "toast" + (bad ? " bad" : "");
    el.textContent = text;
    document.body.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.remove(); }, 2200);
  }

  // Черновик на телефоне (только номера учеников и ответы; стирается после отправки)
  function draftGet(key) {
    try { return JSON.parse(localStorage.getItem("sb:" + key) || "null"); } catch (e) { return null; }
  }
  function draftSet(key, value) {
    try { localStorage.setItem("sb:" + key, JSON.stringify(value)); } catch (e) { /* нет места — не страшно */ }
  }
  function draftClear(key) {
    try { localStorage.removeItem("sb:" + key); } catch (e) { /* ничего */ }
  }

  var AVATAR_COLORS = ["#e9883a", "#3f9e6a", "#3d86c6", "#8a62c9", "#d4604f", "#c99a2e", "#2f9e93", "#c35f8f"];
  function avatar(name, id) {
    var el = document.createElement("span");
    el.className = "avatar";
    el.style.background = AVATAR_COLORS[(id || 0) % AVATAR_COLORS.length];
    el.textContent = (name || "?").charAt(0).toUpperCase();
    return el;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  // Загрузка данных формы: из ссылки (#d=...) или демо-данные (?demo)
  function load(demoData, onReady) {
    applyTheme();
    var tg = tgo();
    if (tg) {
      tg.ready();
      tg.expand();
      if (inTg() && tg.MainButton) tg.MainButton.onClick(function () { if (saveHandler) saveHandler(); });
    }
    var isDemo = /[?&]demo\b/.test(location.search);
    if (isDemo) {
      setLang(/[?&]lang=uz\b/.test(location.search) ? "uz" : demoData.lang);
      demoData.lang = lang;
      return onReady(demoData, true);
    }
    var p = SB.readParam("d");
    var raw = p.hash || p.query;
    if (!raw) return fail(t("noData"));
    SB.decodeParam(raw).then(function (res) {
      setLang(res.data.lang);
      onReady(res.data, false);
    }).catch(function () { fail(t("broken")); });
  }

  function fail(text) {
    var main = document.querySelector("main");
    main.innerHTML = "";
    main.appendChild(el("div", "error-box", text));
  }

  // Дата: «пт 20» и «16–21 нояб.»
  var WD = { ru: ["вс", "пн", "вт", "ср", "чт", "пт", "сб"], uz: ["ya", "du", "se", "ch", "pa", "ju", "sh"] };
  var MON = { ru: ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
              uz: ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"] };
  function parseISO(s) { var a = s.split("-"); return new Date(+a[0], +a[1] - 1, +a[2]); }
  function iso(d) { return SB.localDate(d); }
  function addDays(d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; }
  function weekday(d) { return WD[lang][d.getDay()]; }
  function weekRange(monday) {
    var sat = addDays(monday, 5);
    return monday.getDate() + "–" + sat.getDate() + " " + MON[lang][sat.getMonth()];
  }

  // Дополнительные тексты (приложение группы, панель центра) — в своих файлах
  function addTexts(more) {
    Object.keys(more).forEach(function (l) {
      I18N[l] = I18N[l] || {};
      Object.keys(more[l]).forEach(function (k) { I18N[l][k] = more[l][k]; });
    });
  }

  var reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var SVGNS = "http://www.w3.org/2000/svg";
  function svg(tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }

  // Кольцо прогресса: pct 0–100; число в центре задаёт вызывающий
  function ring(pct, size, stroke, cls) {
    size = size || 64; stroke = stroke || 8;
    var r = (size - stroke) / 2, c = 2 * Math.PI * r;
    var box = el("span", "ring " + (cls || ""));
    box.style.width = box.style.height = size + "px";
    var s = svg("svg", { width: size, height: size, viewBox: "0 0 " + size + " " + size });
    s.appendChild(svg("circle", { cx: size / 2, cy: size / 2, r: r, "class": "ring-bg", "stroke-width": stroke, fill: "none" }));
    var fg = svg("circle", { cx: size / 2, cy: size / 2, r: r, "class": "ring-fg", "stroke-width": stroke, fill: "none",
                             "stroke-linecap": "round", "stroke-dasharray": c, "stroke-dashoffset": c,
                             transform: "rotate(-90 " + size / 2 + " " + size / 2 + ")" });
    s.appendChild(fg);
    box.appendChild(s);
    var target = c * (1 - Math.max(0, Math.min(100, pct)) / 100);
    if (reduced) fg.setAttribute("stroke-dashoffset", target);
    else requestAnimationFrame(function () { requestAnimationFrame(function () { fg.style.strokeDashoffset = target; }); });
    return box;
  }

  // Мини-график уровня по неделям: строка «--3456-7» (0–9 или «-» — нет отчёта)
  function sparkline(hist, w, h) {
    w = w || 84; h = h || 28;
    var s = svg("svg", { width: w, height: h, viewBox: "0 0 " + w + " " + h, "class": "spark" });
    var n = hist.length, pts = [];
    for (var i = 0; i < n; i++) {
      var ch = hist.charAt(i);
      if (ch >= "0" && ch <= "9") pts.push([n > 1 ? 4 + i * (w - 8) / (n - 1) : w / 2, h - 4 - (+ch / 9) * (h - 8)]);
    }
    if (pts.length > 1) {
      s.appendChild(svg("polyline", { points: pts.map(function (p) { return p.join(","); }).join(" "),
                                      fill: "none", "class": "spark-line", "stroke-width": 3,
                                      "stroke-linecap": "round", "stroke-linejoin": "round" }));
    }
    pts.forEach(function (p, k) {
      s.appendChild(svg("circle", { cx: p[0], cy: p[1], r: k === pts.length - 1 ? 3.6 : 2.2, "class": "spark-dot" }));
    });
    return s;
  }

  // Число, которое «набегает» от 0
  function countUp(node, to, suffix) {
    suffix = suffix || "";
    if (reduced || !to) { node.textContent = to + suffix; return; }
    var start = null, dur = 700;
    var step = function (ts) {
      if (start === null) start = ts;
      var k = Math.min(1, (ts - start) / dur);
      node.textContent = Math.round(to * (1 - Math.pow(1 - k, 3))) + suffix;
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // Конфетти на весь экран (праздник: все отчёты заполнены)
  function confetti() {
    if (reduced) return;
    var cv = document.createElement("canvas");
    cv.className = "confetti";
    var W = cv.width = window.innerWidth, H = cv.height = window.innerHeight;
    document.body.appendChild(cv);
    var ctx = cv.getContext("2d");
    var colors = ["#ff9a3c", "#ffc23d", "#4dba6a", "#5ab4f0", "#ff7a6b", "#b37cf0"];
    var parts = [];
    for (var i = 0; i < 140; i++) {
      parts.push({ x: W / 2 + (Math.random() - 0.5) * 80, y: H * 0.35, vx: (Math.random() - 0.5) * 14,
                   vy: -Math.random() * 14 - 4, s: 5 + Math.random() * 6, r: Math.random() * 6,
                   vr: (Math.random() - 0.5) * 0.4, c: colors[i % colors.length] });
    }
    var t0 = null;
    var frame = function (ts) {
      if (t0 === null) t0 = ts;
      ctx.clearRect(0, 0, W, H);
      parts.forEach(function (p) {
        p.vy += 0.42; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.r += p.vr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c;
        ctx.fillRect(-p.s / 2, -p.s / 3, p.s, p.s * 0.66); ctx.restore();
      });
      if (ts - t0 < 2200) requestAnimationFrame(frame); else cv.remove();
    };
    requestAnimationFrame(frame);
  }

  // Маскот «Апельсинка»: настроение happy / calm / worried / party
  function mascot(mood, size) {
    size = size || 72;
    var box = el("span", "mascot mood-" + (mood || "calm"));
    box.style.width = box.style.height = size + "px";
    var s = svg("svg", { viewBox: "0 0 100 100", width: size, height: size });
    s.appendChild(svg("ellipse", { cx: 50, cy: 94, rx: 26, ry: 4, "class": "m-shadow" }));
    var body = svg("g", { "class": "m-body" });
    body.appendChild(svg("path", { d: "M50 14 C 56 4, 70 4, 72 10 C 64 12, 58 14, 52 20 Z", "class": "m-leaf" }));
    body.appendChild(svg("circle", { cx: 50, cy: 54, r: 36, "class": "m-skin" }));
    body.appendChild(svg("circle", { cx: 50, cy: 54, r: 36, "class": "m-shine" }));
    body.appendChild(svg("ellipse", { cx: 28, cy: 64, rx: 6, ry: 4, "class": "m-cheek" }));
    body.appendChild(svg("ellipse", { cx: 72, cy: 64, rx: 6, ry: 4, "class": "m-cheek" }));
    var eyes = svg("g", { "class": "m-eyes" });
    [36, 64].forEach(function (x) {
      eyes.appendChild(svg("ellipse", { cx: x, cy: 50, rx: 8, ry: 9, "class": "m-eye" }));
      eyes.appendChild(svg("circle", { cx: x + 1.5, cy: 52, r: 4.2, "class": "m-pupil" }));
    });
    body.appendChild(eyes);
    var mouth = { happy: "M38 66 Q50 80 62 66", party: "M36 64 Q50 84 64 64 Z", calm: "M40 68 Q50 75 60 68",
                  worried: "M40 72 Q50 64 60 72" }[mood] || "M40 68 Q50 75 60 68";
    body.appendChild(svg("path", { d: mouth, "class": "m-mouth" + (mood === "party" ? " open" : "") }));
    s.appendChild(body);
    box.appendChild(s);
    return box;
  }

  // Склонение: plural(5, ["ученик", "ученика", "учеников"])
  function plural(n, forms) {
    if (lang === "uz") return forms[0];
    var a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return forms[2];
    if (b === 1) return forms[0];
    if (b >= 2 && b <= 4) return forms[1];
    return forms[2];
  }

  // Линейные иконки 24×24 (свои, без внешних файлов). Только постоянные строки — без данных из ссылки.
  var ICONS = {
    home: '<path d="M3 11l9-8 9 8"/><path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14.5c2.4.2 4 1.8 4.5 4.5"/>',
    map: '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
    chart: '<path d="M3 20h18"/><path d="M6 20v-7M11 20V6M16 20v-10"/>',
    report: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M9 10h6M9 14h6M9 18h3"/>',
    cap: '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v5"/>',
    book: '<path d="M4 19V5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2 2 2 0 0 0 2 2h13"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z"/>',
    checkbox: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 12l3 3 5-6"/>',
    check: '<path d="M5 12l5 5 9-10"/>',
    star: '<path d="M12 3l2.8 5.8 6.2.8-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.8z"/>',
    starFill: '<path fill="currentColor" d="M12 3l2.8 5.8 6.2.8-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.8z"/>',
    flag: '<path d="M5 21V4"/><path d="M5 4h12l-2.5 4L17 12H5"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    bell: '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    file: '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    download: '<path d="M12 4v11M7 10l5 5 5-5M4 20h16"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    layers: '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    sliders: '<path d="M4 7h16M4 12h16M4 17h16"/><circle cx="15" cy="7" r="2" fill="var(--surface)"/><circle cx="9" cy="12" r="2" fill="var(--surface)"/><circle cx="17" cy="17" r="2" fill="var(--surface)"/>',
    list: '<path d="M9 6h12M9 12h12M9 18h12"/><path d="M4 6h.01M4 12h.01M4 18h.01" stroke-width="3"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>',
    trendUp: '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    trendDown: '<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
    alert: '<path d="M12 3l10 18H2z"/><path d="M12 10v4M12 17.5v.5"/>',
    repeat: '<path d="M4 11a8 8 0 0 1 14-4.5L20 9"/><path d="M20 4v5h-5"/><path d="M20 13a8 8 0 0 1-14 4.5L4 15"/><path d="M4 20v-5h5"/>',
    empty: '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
    thumb: '<path d="M7 11v9H4v-9z"/><path d="M7 11l4-8c1.5 0 2.5 1 2.5 2.5V9H19a2 2 0 0 1 2 2.3l-1.3 7A2 2 0 0 1 17.7 20H7"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pen: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13 7l4 4"/>',
    send: '<path d="M21 3L10 14"/><path d="M21 3l-7 18-4-7-7-4z"/>',
    building: '<path d="M3 21h18M5 21V9l7-5 7 5v12"/><path d="M9 21v-6h6v6"/>',
    route: '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h8a3 3 0 0 0 0-6H8a3 3 0 0 1 0-6h8"/>',
    shuffle: '<path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>'
  };
  function icon(name, cls) {
    var box = el("span", "ic" + (cls ? " " + cls : ""));
    box.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || "") + "</svg>";
    return box;
  }

  var ui = {
    icon: icon,
    addTexts: addTexts, ring: ring, sparkline: sparkline, countUp: countUp, confetti: confetti, mascot: mascot,
    plural: plural, reduced: reduced, svg: svg,
    tgo: tgo, inTg: inTg, t: t, setLang: setLang, lang: function () { return lang; },
    haptic: haptic, setSave: setSave, setBack: setBack, send: send, confirm: confirmBox, toast: toast,
    draftGet: draftGet, draftSet: draftSet, draftClear: draftClear,
    avatar: avatar, el: el, load: load, fail: fail,
    parseISO: parseISO, iso: iso, addDays: addDays, weekday: weekday, weekRange: weekRange
  };
  for (var k in ui) window.SB[k] = ui[k];
})();
