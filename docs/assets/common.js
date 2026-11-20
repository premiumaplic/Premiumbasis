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
      demo: "Демо: все имена выдуманы"
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
      demo: "Demo: barcha ismlar oʻylab topilgan"
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
      tg.MainButton.setParams({ text: text, color: "#ff9a3c", text_color: "#ffffff", is_visible: !!visible });
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

  var AVATAR_COLORS = ["#ff9a3c", "#4dba6a", "#5ab4f0", "#b37cf0", "#ff7a6b", "#f2b630", "#3cc6b6", "#f07cb4"];
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

  var ui = {
    tgo: tgo, inTg: inTg, t: t, setLang: setLang, lang: function () { return lang; },
    haptic: haptic, setSave: setSave, send: send, confirm: confirmBox, toast: toast,
    draftGet: draftGet, draftSet: draftSet, draftClear: draftClear,
    avatar: avatar, el: el, load: load, fail: fail,
    parseISO: parseISO, iso: iso, addDays: addDays, weekday: weekday, weekRange: weekRange
  };
  for (var k in ui) window.SB[k] = ui[k];
})();
