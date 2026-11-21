/*
 * Журнал группы — главный интерфейс учителя (Telegram Mini App).
 * Открывается кнопкой «📱 Группа» под полем ввода в чате бота. Все данные группы приходят
 * в ссылке; сохранение — одним Telegram.WebApp.sendData (Telegram закрывает приложение,
 * бот отвечает в чат и обновляет кнопку).
 *
 * Нижнее меню: Главная · Ученики · Карта · Итоги.
 *  - Главная: неделя, экзамен, прогресс отчётов, «следующий шаг», быстрые действия, внимание.
 *  - Ученики: уровень, динамика, станция; профиль ученика (отчёт, перевод на станцию).
 *  - Карта: путь по станциям с разделами, ученики на станциях, перевод группы.
 *  - Итоги: уровень группы по неделям, показатели недели, кто растёт, кому помочь.
 * Формы (отчёт, экзамен, тема, посещаемость) — из ../forms/, открываются поверх.
 */
(function () {
  "use strict";

  SB.addTexts({
    ru: {
      tabHome: "Главная", tabStudents: "Ученики", tabMap: "Карта", tabStats: "Итоги",
      weekOf: "Неделя {n} из {t}", weekN: "Неделя {n}", startsOn: "Старт {d}",
      examIn: "Экзамен через {n} дн.", examToday: "Экзамен сегодня!", examTomorrow: "Экзамен завтра",
      streak: "{n} нед. подряд", reportsShort: "отчёты недели",
      nextStep: "Следующий шаг", stepExam: "Сегодня экзамен", stepExamSub: "Внесите баллы — бот сам переведёт сдавших",
      stepReport: "Заполните недельный отчёт", stepReportSub: "Осталось {n} {w}", stepFill: "Заполнить",
      stepCards: "Отправьте карточки родителям", stepCardsSub: "Готово {n} {w} — перешлите родителям", stepSend: "Открыть",
      stepDone: "Неделя закрыта!", stepDoneSub: "Все отчёты заполнены и карточки можно отправлять. Отдохните 🎉",
      stepEmpty: "В группе пока нет учеников", stepEmptySub: "Попросите владельца добавить учеников",
      actions: "Действия", attention: "Нужно внимание", all: "Все",
      st1: "ученик", st2: "ученика", st5: "учеников", cardsW1: "карточка", cardsW2: "карточки", cardsW5: "карточек",
      filterAll: "Все", filterNoReport: "Без отчёта", filterAttention: "Внимание", filterStars: "Звёзды",
      noReport: "нет отчёта", reportDone: "отчёт есть", level: "Уровень", noLevel: "нет данных",
      levelWeeks: "Уровень по неделям", lastReport: "Отчёт недели", lastReportPrev: "Отчёт прошлой недели",
      noAnswers: "Отчёта за эти две недели нет", skipped: "не оценивалось",
      station: "Станция", moveStudent: "Перевести на другую станцию", fillReport: "Заполнить отчёт",
      card: "Карточка", consentYes: "согласие есть", consentNo: "нет согласия родителя",
      star: "Звезда недели", growing: "Растут", needHelp: "Нужна помощь", nobody: "Пока никого",
      groupLevel: "Уровень группы", vsLastWeek: "к прошлой неделе", questionsWeek: "Показатели недели",
      reportsByWeek: "Отчёты по неделям", thisWeekShort: "эта", noData: "Пока мало данных — заполните отчёты пару недель",
      groupHere: "Группа здесь", here: "здесь", stationsDone: "пройдено", onStation: "На станции",
      moveGroupHere: "Перевести всю группу сюда", noStudentsHere: "На этой станции учеников нет",
      mapHint: "Нажмите на станцию — увидите, кто на ней, и сможете перевести группу",
      fork: "Развилка: дальше CEFR или IELTS", monthsN: "{n} мес.", byTeacher: "по решению учителя",
      exam8: "экзамен каждые 2 мес.", selectStudents: "Кому прислать", selectAll: "Выбрать всех готовых",
      tapStudentToFill: "Нажмите на ученика, чтобы заполнить отчёт",
      deltaUp: "+{n}%", deltaDown: "−{n}%", hello: "Привет! Это журнал группы",
      demoNote: "Демо: все имена выдуманы, сохранение не работает",
      hintsAll: "Все подсказки", mapEmpty: "У предмета этой группы нет карты станций",
      stw1: "станция", stw2: "станции", stw5: "станций", before: "пройденный раздел — нажмите, чтобы раскрыть"
    },
    uz: {
      tabHome: "Asosiy", tabStudents: "Oʻquvchilar", tabMap: "Xarita", tabStats: "Natijalar",
      weekOf: "{t} haftadan {n}-hafta", weekN: "{n}-hafta", startsOn: "Boshlanishi {d}",
      examIn: "Imtihongacha {n} kun", examToday: "Imtihon bugun!", examTomorrow: "Imtihon ertaga",
      streak: "{n} hafta ketma-ket", reportsShort: "hafta hisobotlari",
      nextStep: "Keyingi qadam", stepExam: "Bugun imtihon", stepExamSub: "Ballarni kiriting — bot oʻtganlarni oʻzi oʻtkazadi",
      stepReport: "Haftalik hisobotni toʻldiring", stepReportSub: "{n} ta {w} qoldi", stepFill: "Toʻldirish",
      stepCards: "Ota-onalarga kartalarni yuboring", stepCardsSub: "{n} ta {w} tayyor", stepSend: "Ochish",
      stepDone: "Hafta yopildi!", stepDoneSub: "Barcha hisobotlar toʻldirildi, kartalarni yuborish mumkin 🎉",
      stepEmpty: "Guruhda hali oʻquvchi yoʻq", stepEmptySub: "Markaz egasidan oʻquvchilarni qoʻshishni soʻrang",
      actions: "Amallar", attention: "Eʼtibor kerak", all: "Hammasi",
      st1: "oʻquvchi", st2: "oʻquvchi", st5: "oʻquvchi", cardsW1: "karta", cardsW2: "karta", cardsW5: "karta",
      filterAll: "Hammasi", filterNoReport: "Hisobotsiz", filterAttention: "Eʼtibor", filterStars: "Yulduzlar",
      noReport: "hisobot yoʻq", reportDone: "hisobot bor", level: "Daraja", noLevel: "maʼlumot yoʻq",
      levelWeeks: "Haftalar boʻyicha daraja", lastReport: "Hafta hisoboti", lastReportPrev: "Oʻtgan hafta hisoboti",
      noAnswers: "Shu ikki hafta uchun hisobot yoʻq", skipped: "baholanmagan",
      station: "Bosqich", moveStudent: "Boshqa bosqichga oʻtkazish", fillReport: "Hisobotni toʻldirish",
      card: "Karta", consentYes: "rozilik bor", consentNo: "ota-ona roziligi yoʻq",
      star: "Hafta yulduzi", growing: "Oʻsmoqda", needHelp: "Yordam kerak", nobody: "Hozircha hech kim",
      groupLevel: "Guruh darajasi", vsLastWeek: "oʻtgan haftaga nisbatan", questionsWeek: "Hafta koʻrsatkichlari",
      reportsByWeek: "Haftalar boʻyicha hisobotlar", thisWeekShort: "shu", noData: "Maʼlumot kam — bir-ikki hafta hisobot toʻldiring",
      groupHere: "Guruh shu yerda", here: "shu yerda", stationsDone: "oʻtildi", onStation: "Bosqichda",
      moveGroupHere: "Butun guruhni shu yerga oʻtkazish", noStudentsHere: "Bu bosqichda oʻquvchi yoʻq",
      mapHint: "Bosqichni bosing — kim borligini koʻrasiz va guruhni oʻtkazishingiz mumkin",
      fork: "Ayrilish: keyin CEFR yoki IELTS", monthsN: "{n} oy", byTeacher: "oʻqituvchi qarori bilan",
      exam8: "har 2 oyda imtihon", selectStudents: "Kimga yuborish", selectAll: "Barcha tayyorlarni tanlash",
      tapStudentToFill: "Hisobotni toʻldirish uchun oʻquvchini bosing",
      deltaUp: "+{n}%", deltaDown: "−{n}%", hello: "Salom! Bu guruh jurnali",
      demoNote: "Demo: barcha ismlar oʻylab topilgan, saqlash ishlamaydi",
      hintsAll: "Barcha maslahatlar", mapEmpty: "Bu guruh fani uchun bosqichlar xaritasi yoʻq",
      stw1: "bosqich", stw2: "bosqich", stw5: "bosqich", before: "oʻtilgan boʻlim — ochish uchun bosing"
    }
  });

  // ---------------------------------------------------------------- демо-данные (имена выдуманы)

  function demoMonday(back) {
    var d = new Date(), wd = (d.getDay() + 6) % 7;
    return SB.iso(SB.addDays(d, -wd - 7 * (back || 0)));
  }
  var DEMO = {
    v: 2, f: "hub", gid: 1, g: "10-А", sj: "Английский", sc: "en", lang: "ru", today: SB.localDate(),
    hdr: "Курс A1 · неделя 6 из 8 · экзамен через 3 недели", wkn: 6, wkt: 8,
    exd: SB.iso(SB.addDays(new Date(), 17)), sst: SB.iso(SB.addDays(new Date(), -40)),
    st: [[11, "Азиз К.", "uz", 6, 1, "-4456678"], [12, "Мадина Ю.", "ru", 6, 1, "77788899"],
         [13, "Жасур А.", "uz", 6, 0, "6654433-"], [14, "Камила Р.", "ru", 5, 1, "--556667"],
         [15, "Отабек С.", "uz", 6, 1, "5556565-"], [16, "Севара О.", "ru", 7, 1, "88889999"],
         [17, "Тимур Н.", "ru", 6, 1, "4444555-"]],
    att: null,
    wk: {
      wk: demoMonday(0),
      q: [[1, "Домашнее задание", "не сделано", "частично", "сделано с ошибками", "сделано хорошо", 0],
          [2, "Работа на уроке", "пассивен", "отвечает, когда спросят", "активно участвует", "помогает другим", 0],
          [3, "Новые слова", "не выучены", "выучена часть", "выучено большинство", "выучены все", 0],
          [4, "Грамматика темы", "не понял", "понимает с подсказкой", "применяет с ошибками", "применяет уверенно", 0],
          [5, "Говорение", "молчит", "отдельные слова", "простые фразы", "свободно для своего уровня", 0],
          [8, "Аудирование", "не понимает на слух", "понимает отдельные слова", "понимает основное", "понимает почти всё", 1],
          [9, "Чтение", "не читает", "читает с трудом", "читает с ошибками", "читает бегло и понимает", 1],
          [10, "Письмо", "не пишет", "много ошибок", "небольшие ошибки", "пишет грамотно", 1],
          [7, "Дисциплина", "мешал", "отвлекался", "нормально", "образцово", 0]],
      ph: [["Молодец!", "Barakalla!"], ["Старается на уроке.", "Darsda harakat qiladi."],
           ["Нужно повторять слова.", "Soʻzlarni takrorlash kerak."], ["Больше читать дома.", "Uyda koʻproq oʻqish kerak."]],
      a: { "11": { "0": "322123xx3", "1": "21101xxx2" }, "12": { "0": "333232333", "1": "333222322" },
           "14": { "0": "22212x2x2", "1": "2221xxxx2" }, "16": { "0": "333333333" },
           "13": { "1": "21101xxx2" }, "15": { "1": "2222xxxx2" } },
      c: {}, sr: { "0": [12] }
    },
    ex: { s: 6, sn: "Курс A1", nx: "Курс A2", fork: false, mode: "score", pass: 60, max: 100, prev: {} },
    tp: { cur: "Unit 5. Present Simple", u: [[1, 5, "Present Simple"], [2, 6, "My day"], [3, 7, "Food"]] },
    hn: [[101, 13, "Домашка проседает", "недели: 09.11–14.11, 16.11–21.11", "homework"],
         [102, 16, "Похвалите", "средний балл растёт 3 недели подряд", "growth"],
         [103, 13, "Риск не сдать экзамен", "уровень 45% при проходном 60%", "exam_risk"]],
    stg: [[1, "Starter", "Для детей", "Буквы, звуки и первые слова", "k", 0, 0],
          [2, "Roundup 1", "Для детей", "Простые фразы и базовая грамматика", "k", 0, 0],
          [3, "Roundup 2", "Для детей", "Времена Present и Past", "k", 0, 0],
          [4, "Roundup 3", "Для детей", "Future, сравнения, модальные глаголы", "k", 0, 0],
          [5, "Roundup 4", "Для детей", "Сложные времена и пассив", "k", 0, 0],
          [6, "Курс A1", "Общий английский", "Общение на простые темы", "m", 1, 2],
          [7, "Курс A2", "Общий английский", "Рассказ о себе, планы и опыт", "m", 1, 2],
          [8, "Курс B1", "Общий английский", "Свободный разговор на бытовые темы", "m", 1, 2],
          [9, "Курс B2", "Общий английский", "Уверенный английский, сложные тексты", "m", 1, 2],
          [10, "Pre-CEFR", "Экзамен CEFR", "Формат экзамена CEFR", "c", 0, 2],
          [11, "CEFR", "Экзамен CEFR", "Подготовка и сдача CEFR", "c", 0, 3],
          [12, "Pre-IELTS", "Экзамен IELTS", "Формат экзамена IELTS", "i", 0, 2],
          [13, "IELTS", "Экзамен IELTS", "Подготовка и сдача IELTS", "i", 0, 3]],
    gs: 6
  };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var hub, demo = false, tab = "home", nav = null, mapOpen = {};

  // ---------------------------------------------------------------- данные

  function student(id) { return hub.st.filter(function (s) { return s[0] === id; })[0]; }
  function station(id) { return (hub.stg || []).filter(function (s) { return s[0] === id; })[0]; }
  function stName(id) { var s = station(id); return s ? s[1] : "—"; }
  function hist(s) { return s[5] || ""; }
  function levelOf(s) {               // последний известный уровень 0–9 или null
    var h = hist(s);
    for (var i = h.length - 1; i >= 0; i--) if (h.charAt(i) !== "-") return +h.charAt(i);
    return null;
  }
  function pct(level) { return level === null ? null : Math.round(level / 9 * 100); }
  function rec(sid) { return (hub.wk.a || {})[String(sid)] || {}; }
  function reportDone(sid) { return !!rec(sid)["0"]; }
  function starred(sid) { return ((hub.wk.sr || {})["0"] || []).indexOf(sid) >= 0; }
  function hintsOf(sid) { return (hub.hn || []).filter(function (h) { return h[1] === sid; }); }
  function badHints(sid) { return hintsOf(sid).filter(function (h) { return h[4] !== "growth"; }); }
  function doneCount() { return hub.st.filter(function (s) { return reportDone(s[0]); }).length; }
  function cardsReady() {
    return hub.st.filter(function (s) { var r = rec(s[0]); return s[4] && (r["0"] || r["1"]); });
  }
  function daysTo(isoDate) {
    if (!isoDate) return null;
    var a = SB.parseISO(hub.today || SB.localDate()), b = SB.parseISO(isoDate);
    return Math.round((b - a) / 86400000);
  }
  function words(n, a, b, c) { return SB.plural(n, [t(a), t(b), t(c)]); }

  // Недели подряд, когда отчёты заполнены у всех (по истории уровней)
  function streak() {
    if (!hub.st.length) return 0;
    var len = hist(hub.st[0]).length, n = 0;
    for (var i = len - 1; i >= 0; i--) {
      var full = hub.st.every(function (s) { return hist(s).charAt(i) && hist(s).charAt(i) !== "-"; });
      if (full) n++;
      else if (i === len - 1) continue;   // текущая неделя ещё не закрыта — не обрываем серию
      else break;
    }
    return n;
  }

  // ---------------------------------------------------------------- навигация

  function setTabs(visible) {
    document.body.classList.toggle("in-form", !visible);
    var bar = document.getElementById("tabbar");
    if (bar) bar.classList.toggle("hidden", !visible);
  }

  function renderTabbar() {
    var bar = document.getElementById("tabbar");
    bar.innerHTML = "";
    var items = [["home", "🏠", t("tabHome")], ["students", "👥", t("tabStudents")]];
    if (hub.stg && hub.stg.length) items.push(["map", "🗺️", t("tabMap")]);
    items.push(["stats", "📊", t("tabStats")]);
    items.forEach(function (it) {
      var b = el("button", "tab" + (tab === it[0] ? " active" : ""));
      b.type = "button";
      b.appendChild(el("span", "tab-icon", it[1]));
      b.appendChild(el("span", "tab-label", it[2]));
      if (it[0] === "students") {
        var att = hub.st.filter(function (s) { return badHints(s[0]).length; }).length;
        if (att) b.appendChild(el("span", "tab-dot", String(att)));
      }
      b.addEventListener("click", function () { go(it[0]); });
      bar.appendChild(b);
    });
  }

  function screen(cls) {
    app.innerHTML = "";
    window.scrollTo(0, 0);
    var box = el("div", "screen " + (cls || ""));
    app.appendChild(box);
    return box;
  }

  function stagger(container) {
    var kids = container.children;
    for (var i = 0; i < kids.length; i++) {
      kids[i].classList.add("rise");
      kids[i].style.animationDelay = Math.min(i * 45, 400) + "ms";
    }
  }

  function go(name) {
    if (name !== tab) SB.haptic("select");
    tab = name;
    nav = null;
    setTabs(true);
    renderTabbar();
    hubbar(false);
    SB.hubHome = null;
    SB.setSave(t("save"), function () {}, false);
    SB.setBack(name === "home" ? null : function () { go("home"); });
    if (name === "students") return studentsTab();
    if (name === "map") return mapTab();
    if (name === "stats") return statsTab();
    return homeTab();
  }

  // Подэкран (профиль, станция, подсказки, карточки): «Назад» возвращает на вкладку
  function sub(render) {
    nav = render;
    SB.setSave(t("save"), function () {}, false);
    SB.setBack(function () { go(tab); });
    render();
  }

  function backRow(box, title) {
    var top = el("div", "subbar");
    var b = el("button", "icon-btn", "←");
    b.type = "button";
    b.addEventListener("click", function () { go(tab); });
    top.appendChild(b);
    top.appendChild(el("h1", "grow", title));
    box.appendChild(top);
  }

  // Формы (отчёт, экзамен, тема, посещаемость) — данные из общего пакета группы
  function formData(kind) {
    var out = { v: 1, gid: hub.gid, g: hub.g, lang: hub.lang };
    if (kind === "attendance") {
      out.f = "att"; out.today = hub.att.today; out.days = hub.att.days; out.h = hub.att.h;
      out.st = hub.st.map(function (s) { return [s[0], s[1]]; });
    } else if (kind === "weekly") {
      for (var w in hub.wk) out[w] = hub.wk[w];
      out.f = "wk";
      out.st = hub.st.map(function (s) { return [s[0], s[1], s[2]]; });
    } else if (kind === "exam") {
      for (var e in hub.ex) out[e] = hub.ex[e];
      out.f = "ex";
      out.st = hub.st.map(function (s) { return [s[0], s[1], s[3] === hub.ex.s ? 1 : 0]; });
    } else if (kind === "topic") {
      out.f = "tp"; out.cur = hub.tp.cur; out.u = hub.tp.u;
    }
    return out;
  }

  function hubbar(show) {
    var bar = document.getElementById("hubbar");
    document.getElementById("hubname").textContent = t("journal") + " " + hub.g;
    bar.classList.toggle("hidden", !show);
  }

  function openForm(kind, opts) {
    SB.haptic("select");
    setTabs(false);
    hubbar(true);
    window.scrollTo(0, 0);
    SB.hubHome = function () { go(tab); };
    SB.setBack(SB.hubHome);
    SB.forms[kind].start(formData(kind), demo, opts || {});
  }

  // ---------------------------------------------------------------- главная

  function homeTab() {
    var box = screen("home");
    var done = doneCount(), total = hub.st.length;
    var hintsBad = (hub.hn || []).filter(function (h) { return h[4] !== "growth"; });

    // ---- шапка: группа, неделя, экзамен, кольцо отчётов
    var hero = el("div", "hero2");
    var left = el("div", "hero-left");
    left.appendChild(el("small", "", (hub.sj || "") + (hub.hdr ? "" : "")));
    left.appendChild(el("div", "title", hub.g));
    var chips = el("div", "hero-chips");
    if (hub.wkn) {
      var wk = el("span", "hchip");
      wk.appendChild(document.createTextNode(hub.wkt ? t("weekOf", { n: hub.wkn, t: hub.wkt }) : t("weekN", { n: hub.wkn })));
      chips.appendChild(wk);
    } else if (hub.sst) {
      chips.appendChild(el("span", "hchip", t("startsOn", { d: hub.sst.split("-").reverse().slice(0, 2).join(".") })));
    }
    var dx = daysTo(hub.exd);
    if (dx !== null && dx >= 0) {
      chips.appendChild(el("span", "hchip exam" + (dx <= 7 ? " soon" : ""),
                           "🎓 " + (dx === 0 ? t("examToday") : dx === 1 ? t("examTomorrow") : t("examIn", { n: dx }))));
    }
    var sk = streak();
    if (sk >= 2) chips.appendChild(el("span", "hchip fire", "🔥 " + t("streak", { n: sk })));
    left.appendChild(chips);
    if (hub.wkt) {
      var segs = el("div", "week-segs");
      for (var i = 1; i <= hub.wkt; i++) segs.appendChild(el("i", i < hub.wkn ? "on" : i === hub.wkn ? "now" : ""));
      segs.appendChild(el("b", "flag", "🏁"));
      left.appendChild(segs);
    }
    hero.appendChild(left);
    var r = SB.ring(total ? 100 * done / total : 0, 92, 10, "hero-ring");
    var mid = el("span", "ring-mid");
    var num = el("b", "");
    mid.appendChild(num);
    mid.appendChild(el("small", "", "/ " + total));
    r.appendChild(mid);
    r.appendChild(el("span", "ring-cap", t("reportsShort")));
    SB.countUp(num, done);
    hero.appendChild(r);
    box.appendChild(hero);
    if (demo) box.appendChild(el("p", "hint center", t("demoNote")));

    // ---- следующий шаг (как «следующий урок» в Duolingo)
    box.appendChild(nextStep(done, total));

    // ---- быстрые действия
    box.appendChild(el("h2", "", t("actions")));
    var grid = el("div", "quick");
    grid.appendChild(quick("📝", t("weekly"), done + "/" + total, "orange", function () { openForm("weekly"); }));
    if (hub.ex) {
      grid.appendChild(quick("🎓", hub.ex.mode === "score" ? t("exam") : t("decision"),
                             hub.ex.nx ? "➜ " + hub.ex.nx : hub.ex.sn, "blue", function () { openForm("exam"); }));
    }
    grid.appendChild(quick("📚", t("topic"), hub.tp && hub.tp.cur ? hub.tp.cur : t("noTopic"), "green",
                           function () { openForm("topic"); }));
    var ready = cardsReady().length;
    grid.appendChild(quick("💌", t("cards"), ready + "/" + total, "pink", function () { sub(cardsScreen); }));
    grid.appendChild(quick("💡", t("hints"), hintsBad.length ? t("hintsN", { n: hintsBad.length }) : t("noHints"),
                           "yellow", function () { sub(hintsScreen); }, hintsBad.length));
    if (hub.stg && hub.stg.length) {
      grid.appendChild(quick("🗺️", t("tabMap"), hub.gs ? stName(hub.gs) : "—", "blue", function () { go("map"); }));
    } else {
      grid.appendChild(quick("📊", t("tabStats"), t("groupLevel"), "blue", function () { go("stats"); }));
    }
    if (hub.att) {
      var attToday = hub.att.h && hub.att.h["0"];
      grid.appendChild(quick("✅", t("attendance"), attToday ? "✓ " + t("attToday") : t("attMark"), "teal",
                             function () { openForm("attendance"); }));
    }
    box.appendChild(grid);

    // ---- внимание: первые подсказки
    if (hintsBad.length) {
      var head = el("div", "h2row");
      head.appendChild(el("h2", "", t("attention")));
      var all = el("button", "link", t("all") + " ›");
      all.type = "button";
      all.addEventListener("click", function () { sub(hintsScreen); });
      head.appendChild(all);
      box.appendChild(head);
      hintsBad.slice(0, 3).forEach(function (h) { box.appendChild(hintRow(h, true)); });
    }
    box.appendChild(el("p", "hint center footer", t("footer")));
    stagger(box);
  }

  function nextStep(done, total) {
    var card = el("div", "mission");
    var mood, title, subText, btn, action;
    var dx = daysTo(hub.exd);
    var ready = cardsReady().length;
    if (!total) {
      mood = "calm"; title = t("stepEmpty"); subText = t("stepEmptySub");
    } else if (hub.ex && hub.ex.mode === "score" && dx === 0) {
      mood = "happy"; title = t("stepExam"); subText = t("stepExamSub"); btn = t("stepFill");
      action = function () { openForm("exam"); };
    } else if (done < total) {
      var left = total - done;
      var worried = (hub.hn || []).filter(function (h) { return h[4] !== "growth"; }).length;
      mood = worried * 2 > total ? "worried" : "calm";
      title = t("stepReport"); subText = t("stepReportSub", { n: left, w: words(left, "st1", "st2", "st5") });
      btn = t("stepFill"); action = function () { openForm("weekly"); };
    } else if (ready) {
      mood = "happy"; title = t("stepCards");
      subText = t("stepCardsSub", { n: ready, w: words(ready, "cardsW1", "cardsW2", "cardsW5") });
      btn = t("stepSend"); action = function () { sub(cardsScreen); };
    } else {
      mood = "party"; title = t("stepDone"); subText = t("stepDoneSub");
    }
    var top = el("div", "mission-top");
    top.appendChild(SB.mascot(mood, 76));
    var text = el("div", "grow");
    text.appendChild(el("small", "", t("nextStep")));
    text.appendChild(el("b", "", title));
    text.appendChild(el("span", "", subText));
    top.appendChild(text);
    card.appendChild(top);
    if (btn) {
      var b = el("button", "btn", btn);
      b.type = "button";
      b.addEventListener("click", action);
      card.appendChild(b);
    }
    // праздник: все отчёты недели заполнены (один раз за неделю)
    if (total && done === total) {
      var key = "party:" + hub.gid + ":" + (hub.wk && hub.wk.wk);
      if (!SB.draftGet(key)) { SB.draftSet(key, 1); setTimeout(SB.confetti, 350); }
    }
    return card;
  }

  function quick(icon, title, subText, color, onClick, badge) {
    var b = el("button", "qtile " + color);
    b.type = "button";
    b.appendChild(el("span", "qicon", icon));
    b.appendChild(el("b", "", title));
    b.appendChild(el("span", "sub", subText));
    if (badge) b.appendChild(el("span", "count", String(badge)));
    b.addEventListener("click", onClick);
    return b;
  }

  function hintRow(h, link) {
    var s = student(h[1]);
    var row = el(link ? "button" : "div", "hintrow " + (h[4] === "growth" ? "good" : "bad"));
    if (link) row.type = "button";
    row.appendChild(SB.avatar(s ? s[1] : "?", h[1]));
    var text = el("span", "grow");
    text.appendChild(el("b", "", (s ? s[1] : "") + " · " + h[2]));
    if (h[3]) text.appendChild(el("span", "sub", t("why") + ": " + h[3]));
    row.appendChild(text);
    row.appendChild(el("span", "hint-icon", h[4] === "growth" ? "🌟" : "⚠️"));
    if (link && s) row.addEventListener("click", function () { tab = "students"; renderTabbar(); sub(function () { profile(s[0]); }); });
    return row;
  }

  // ---------------------------------------------------------------- ученики

  var filter = "all";
  function studentsTab() {
    var box = screen("students");
    var head = el("div", "tabhead");
    head.appendChild(el("h1", "", t("tabStudents")));
    head.appendChild(el("span", "group-chip", "👥 " + hub.g + " · " + hub.st.length));
    box.appendChild(head);

    var seg = el("div", "filters");
    [["all", t("filterAll")], ["noreport", t("filterNoReport")], ["attention", t("filterAttention")],
     ["stars", t("filterStars")]].forEach(function (f) {
      var b = el("button", "fchip" + (filter === f[0] ? " on" : ""), f[1]);
      b.type = "button";
      b.addEventListener("click", function () { filter = f[0]; SB.haptic("select"); studentsTab(); });
      seg.appendChild(b);
    });
    box.appendChild(seg);

    var list = el("div", "slist");
    var shown = hub.st.filter(function (s) {
      if (filter === "noreport") return !reportDone(s[0]);
      if (filter === "attention") return badHints(s[0]).length > 0;
      if (filter === "stars") return starred(s[0]) || hintsOf(s[0]).some(function (h) { return h[4] === "growth"; });
      return true;
    });
    if (!shown.length) list.appendChild(el("div", "empty-state", t("nobody")));
    shown.forEach(function (s) { list.appendChild(studentRow(s)); });
    box.appendChild(list);
    stagger(list);
  }

  function levelAvatar(s, size) {
    var lv = levelOf(s);
    var wrap = el("span", "lvl-avatar");
    var r = SB.ring(lv === null ? 0 : pct(lv), size || 50, 4, "lvl-ring lv" + (lv === null ? "x" : lv >= 6 ? "hi" : lv >= 4 ? "mid" : "lo"));
    var av = SB.avatar(s[1], s[0]);
    av.style.fontSize = Math.round((size || 50) * 0.36) + "px";
    r.appendChild(av);
    wrap.appendChild(r);
    if (starred(s[0])) wrap.appendChild(el("span", "star-badge", "⭐"));
    return wrap;
  }

  function studentRow(s) {
    var b = el("button", "srow");
    b.type = "button";
    b.appendChild(levelAvatar(s, 50));
    var mid = el("span", "grow");
    mid.appendChild(el("b", "", s[1]));
    var meta = el("span", "meta");
    if (hub.stg && hub.stg.length && s[3]) meta.appendChild(el("span", "mini-chip", stName(s[3])));
    meta.appendChild(el("span", "mini-chip " + (reportDone(s[0]) ? "ok" : "todo"),
                        reportDone(s[0]) ? "✓ " + t("reportDone") : t("noReport")));
    var bad = badHints(s[0]).length;
    if (bad) meta.appendChild(el("span", "mini-chip warn", "⚠️ " + bad));
    mid.appendChild(meta);
    b.appendChild(mid);
    var right = el("span", "sright");
    right.appendChild(SB.sparkline(hist(s), 72, 26));
    var lv = levelOf(s);
    right.appendChild(el("small", "", lv === null ? "—" : pct(lv) + "%"));
    b.appendChild(right);
    b.addEventListener("click", function () { SB.haptic("select"); sub(function () { profile(s[0]); }); });
    return b;
  }

  function profile(sid) {
    var s = student(sid);
    var box = screen("profile");
    backRow(box, s[1]);
    var head = el("div", "phead");
    head.appendChild(levelAvatar(s, 84));
    var info = el("div", "grow");
    var lv = levelOf(s);
    var big = el("div", "pbig");
    big.appendChild(el("b", "", lv === null ? "—" : pct(lv) + "%"));
    big.appendChild(el("span", "", t("level")));
    info.appendChild(big);
    var chips = el("div", "meta");
    chips.appendChild(el("span", "mini-chip", t("card") + ": " + (s[2] || "ru").toUpperCase()));
    chips.appendChild(el("span", "mini-chip " + (s[4] ? "ok" : "warn"), s[4] ? "✓ " + t("consentYes") : t("consentNo")));
    if (starred(sid)) chips.appendChild(el("span", "mini-chip star", "⭐ " + t("star")));
    info.appendChild(chips);
    head.appendChild(info);
    box.appendChild(head);

    // уровень по неделям — столбики
    var chart = el("div", "card");
    chart.appendChild(el("h3", "ctitle", t("levelWeeks")));
    chart.appendChild(columns(hist(s).split(""), function (ch) { return ch === "-" ? null : +ch / 9 * 100; }));
    box.appendChild(chart);

    // последний отчёт: показатели
    var r = rec(sid), code = r["0"] || r["1"];
    var answers = el("div", "card");
    answers.appendChild(el("h3", "ctitle", r["0"] ? t("lastReport") : t("lastReportPrev")));
    if (!code) answers.appendChild(el("p", "hint", t("noAnswers")));
    else hub.wk.q.forEach(function (q, i) {
      var ch = code.charAt(i), v = ch >= "0" && ch <= "3" ? +ch : null;
      var row = el("div", "metric");
      var lab = el("span", "grow");
      lab.appendChild(el("b", "", q[1]));
      lab.appendChild(el("small", "", v === null ? t("skipped") : q[2 + v]));
      row.appendChild(lab);
      var bar = el("span", "seg3");
      for (var k = 0; k < 3; k++) bar.appendChild(el("i", v !== null && k < v ? "on" : ""));
      row.appendChild(bar);
      answers.appendChild(row);
    });
    box.appendChild(answers);

    var own = hintsOf(sid);
    if (own.length) {
      box.appendChild(el("h2", "", t("hints")));
      own.forEach(function (h) { box.appendChild(hintRow(h, false)); });
    }

    if (hub.stg && hub.stg.length) {
      var st = el("div", "card station-card");
      var cur = station(s[3]);
      st.appendChild(el("small", "hint", t("station")));
      st.appendChild(el("b", "", cur ? cur[1] : "—"));
      if (cur && cur[3]) st.appendChild(el("span", "hint", cur[3]));
      var mv = el("button", "btn ghost", "🔀 " + t("moveStudent"));
      mv.type = "button";
      mv.addEventListener("click", function () { sub(function () { pickStation(sid); }); });
      st.appendChild(mv);
      box.appendChild(st);
    }
    var fill = el("button", "btn", "📝 " + t("fillReport"));
    fill.type = "button";
    fill.addEventListener("click", function () { openForm("weekly", { sid: sid }); });
    box.appendChild(fill);
    stagger(box);
  }

  // Столбики по неделям (значения 0–100 или null)
  function columns(items, value) {
    var wrap = el("div", "cols");
    var n = items.length;
    items.forEach(function (it, i) {
      var v = value(it);
      var col = el("span", "col" + (i === n - 1 ? " now" : "") + (v === null ? " none" : ""));
      var fill = el("i");
      fill.style.height = "0%";
      col.appendChild(fill);
      col.appendChild(el("small", "", i === n - 1 ? t("thisWeekShort") : "−" + (n - 1 - i)));
      wrap.appendChild(col);
      var h = v === null ? 6 : Math.max(8, v);
      if (SB.reduced) fill.style.height = h + "%";
      else setTimeout(function () { fill.style.height = h + "%"; }, 60 + i * 40);
    });
    return wrap;
  }

  // ---------------------------------------------------------------- выбор станции

  function pickStation(sid) {
    var who = sid === 0 ? t("wholeGroup") + " " + hub.g : student(sid)[1];
    var current = sid === 0 ? hub.gs : student(sid)[3];
    var target = null;
    var draw = function () {
      var box = screen("pick");
      backRow(box, who);
      box.appendChild(el("p", "hint", t("pickStation")));
      var lastSection = null;
      hub.stg.forEach(function (s) {
        if (s[2] !== lastSection) { box.appendChild(el("h2", "", s[2] || "")); lastSection = s[2]; }
        var b = el("button", "choice" + (target === s[0] ? " selected" : "") + (s[0] === current ? " current" : ""));
        b.type = "button";
        b.disabled = s[0] === current;
        var tx = el("span", "grow");
        tx.appendChild(el("span", "", s[1] + (s[0] === current ? " · " + t("here") : "")));
        if (s[3]) tx.appendChild(el("span", "sub", s[3]));
        b.appendChild(tx);
        b.addEventListener("click", function () { target = s[0]; SB.haptic("select"); draw(); });
        box.appendChild(b);
      });
      if (target) {
        var note = el("div", "card soft sticky-note");
        note.appendChild(el("b", "", t("moveConfirm", { who: who, from: stName(current), to: stName(target) })));
        note.appendChild(el("div", "hint", t("skippedNote") + (sid === 0 ? " " + t("examRestart") : "")));
        box.appendChild(note);
        note.scrollIntoView({ behavior: SB.reduced ? "auto" : "smooth", block: "end" });
      }
      SB.setSave(t("move"), function () {
        SB.haptic("success");
        SB.send({ v: 1, u: SB.uuid(), t: "move", g: hub.gid, sid: sid, s: target });
      }, !!target);
    };
    nav = draw;
    SB.setBack(function () { go(tab); });
    draw();
  }

  // ---------------------------------------------------------------- карта

  function mapTab() {
    var box = screen("map");
    var head = el("div", "tabhead");
    head.appendChild(el("h1", "", t("tabMap")));
    head.appendChild(el("span", "group-chip", "👥 " + hub.g));
    box.appendChild(head);
    if (!hub.stg || !hub.stg.length) { box.appendChild(el("div", "empty-state", t("mapEmpty"))); return; }
    box.appendChild(el("p", "hint", t("mapHint")));

    var order = hub.stg.map(function (s) { return s[0]; });
    var groupIdx = order.indexOf(hub.gs);
    var byStation = {};
    hub.st.forEach(function (s) { (byStation[s[3]] = byStation[s[3]] || []).push(s); });

    var path = el("div", "path");
    var lastSection = null, forkShown = false, k = 0;
    var groupSection = groupIdx >= 0 ? hub.stg[groupIdx][2] : null;
    var sectionsBefore = {};
    for (var gi = 0; gi < groupIdx; gi++) if (hub.stg[gi][2] !== groupSection) sectionsBefore[hub.stg[gi][2]] = true;
    var waves = [0, 1, 2, 1, 0, -1, -2, -1];
    var currentNode = null;
    hub.stg.forEach(function (s, i) {
      if ((s[4] === "c" || s[4] === "i") && !forkShown) {
        path.appendChild(el("div", "fork-banner", "🔀 " + t("fork")));
        forkShown = true;
      }
      if (s[2] !== lastSection) {
        var collapsed = sectionsBefore[s[2]] && !mapOpen[s[2]];
        var ban = el(collapsed ? "button" : "div", "section-banner " + ({ k: "kids", m: "main", c: "cefr", i: "ielts" }[s[4]] || "main") +
                     (collapsed ? " collapsed" : ""));
        ban.appendChild(el("b", "", (collapsed ? "▸ " : "") + (s[2] || "")));
        var inSection = hub.stg.filter(function (x) { return x[2] === s[2]; }).length;
        ban.appendChild(el("small", "", inSection + " " + words(inSection, "stw1", "stw2", "stw5") + " · " +
                           (collapsed ? t("before") : s[5] ? t("exam8") : s[6] ? t("monthsN", { n: s[6] }) : t("byTeacher"))));
        if (collapsed) {
          ban.type = "button";
          (function (name) {
            ban.addEventListener("click", function () { mapOpen[name] = true; SB.haptic("select"); mapTab(); });
          })(s[2]);
        }
        path.appendChild(ban);
        lastSection = s[2];
        k = 0;
      }
      if (sectionsBefore[s[2]] && !mapOpen[s[2]]) {
        // свёрнутый раздел: показываем только тех, кто там стоит
        var there = byStation[s[0]] || [];
        if (there.length) {
          var mini = el("button", "mini-node");
          mini.type = "button";
          mini.appendChild(el("span", "", s[1]));
          var st2 = el("span", "avstack");
          there.slice(0, 4).forEach(function (p) { st2.appendChild(SB.avatar(p[1], p[0])); });
          mini.appendChild(st2);
          mini.addEventListener("click", function () { SB.haptic("select"); sub(function () { stationSheet(s[0]); }); });
          path.appendChild(mini);
        }
        return;
      }
      var state = i < groupIdx ? "done" : i === groupIdx ? "current" : "future";
      if (groupIdx < 0) state = "future";
      if ((s[4] === "c" || s[4] === "i") && groupIdx >= 0 && hub.stg[groupIdx][4] !== s[4] &&
          (hub.stg[groupIdx][4] === "c" || hub.stg[groupIdx][4] === "i")) state = "future";
      var node = el("div", "pnode " + state);
      node.style.left = waves[k % waves.length] * 34 + "px";
      k++;
      var btn = el("button", "pbtn");
      btn.type = "button";
      btn.appendChild(el("span", "picon", state === "done" ? "✓" : state === "current" ? "★" : String(i + 1)));
      if (state === "current") btn.appendChild(el("span", "pulse"));
      btn.addEventListener("click", function () { SB.haptic("select"); sub(function () { stationSheet(s[0]); }); });
      node.appendChild(btn);
      var label = el("div", "plabel");
      label.appendChild(el("b", "", s[1]));
      if (state === "current") label.appendChild(el("span", "flag-chip", "🚩 " + t("groupHere")));
      node.appendChild(label);
      var people = byStation[s[0]] || [];
      if (people.length) {
        var stack = el("div", "avstack");
        people.slice(0, 4).forEach(function (p) { stack.appendChild(SB.avatar(p[1], p[0])); });
        if (people.length > 4) stack.appendChild(el("span", "avatar more", "+" + (people.length - 4)));
        node.appendChild(stack);
      }
      path.appendChild(node);
      if (state === "current") currentNode = node;
    });
    box.appendChild(path);
    stagger(path);
    if (currentNode) setTimeout(function () {
      currentNode.scrollIntoView({ behavior: SB.reduced ? "auto" : "smooth", block: "center" });
    }, 250);
  }

  function stationSheet(id) {
    var s = station(id);
    var box = screen("sheet");
    backRow(box, s[1]);
    var card = el("div", "card station-card");
    card.appendChild(el("small", "hint", s[2]));
    if (s[3]) card.appendChild(el("b", "", s[3]));
    card.appendChild(el("span", "hint", s[5] ? t("exam8") : s[6] ? t("monthsN", { n: s[6] }) : t("byTeacher")));
    box.appendChild(card);
    var here = hub.st.filter(function (x) { return x[3] === id; });
    box.appendChild(el("h2", "", t("onStation") + " · " + here.length));
    if (!here.length) box.appendChild(el("div", "empty-state", t("noStudentsHere")));
    here.forEach(function (x) { box.appendChild(studentRow(x)); });
    if (id !== hub.gs) {
      var mv = el("button", "btn ghost", "👥 " + t("moveGroupHere"));
      mv.type = "button";
      mv.addEventListener("click", function () {
        SB.confirm(t("moveConfirm", { who: t("wholeGroup") + " " + hub.g, from: stName(hub.gs), to: s[1] }) + "\n\n" +
                   t("skippedNote") + " " + t("examRestart"), function (ok) {
          if (!ok) return;
          SB.haptic("success");
          SB.send({ v: 1, u: SB.uuid(), t: "move", g: hub.gid, sid: 0, s: id });
        });
      });
      box.appendChild(mv);
    }
    stagger(box);
  }

  // ---------------------------------------------------------------- итоги

  function avgLevelAt(i) {
    var vals = hub.st.map(function (s) { return hist(s).charAt(i); }).filter(function (c) { return c && c !== "-"; });
    if (!vals.length) return null;
    return vals.reduce(function (a, c) { return a + +c; }, 0) / vals.length / 9 * 100;
  }

  function questionAvg(back) {
    var out = hub.wk.q.map(function () { return [0, 0]; });
    hub.st.forEach(function (s) {
      var code = rec(s[0])[String(back)];
      if (!code) return;
      for (var i = 0; i < code.length && i < out.length; i++) {
        var ch = code.charAt(i);
        if (ch >= "0" && ch <= "3") { out[i][0] += +ch; out[i][1]++; }
      }
    });
    return out.map(function (x) { return x[1] ? x[0] / x[1] : null; });
  }

  function statsTab() {
    var box = screen("stats-tab");
    var head = el("div", "tabhead");
    head.appendChild(el("h1", "", t("tabStats")));
    head.appendChild(el("span", "group-chip", "👥 " + hub.g));
    box.appendChild(head);
    var len = hub.st.length ? hist(hub.st[0]).length : 0;
    if (!len) { box.appendChild(el("div", "empty-state", t("noData"))); return; }

    // уровень группы: сейчас и к прошлой неделе
    var now = avgLevelAt(len - 1), prev = avgLevelAt(len - 2);
    var lvl = el("div", "card big-stat");
    var left = el("div", "grow");
    left.appendChild(el("small", "hint", t("groupLevel")));
    var num = el("b", "bignum");
    left.appendChild(num);
    if (now !== null) SB.countUp(num, Math.round(now), "%"); else num.textContent = "—";
    if (now !== null && prev !== null) {
      var d = Math.round(now - prev);
      left.appendChild(el("span", "delta " + (d > 0 ? "up" : d < 0 ? "down" : ""),
                          (d > 0 ? "▲ " + t("deltaUp", { n: d }) : d < 0 ? "▼ " + t("deltaDown", { n: -d }) : "= 0%") +
                          " " + t("vsLastWeek")));
    }
    lvl.appendChild(left);
    lvl.appendChild(SB.mascot(now === null ? "calm" : now >= 70 ? "happy" : now >= 45 ? "calm" : "worried", 64));
    box.appendChild(lvl);

    var weeks = [];
    for (var i = 0; i < len; i++) weeks.push(i);
    var chart = el("div", "card");
    chart.appendChild(el("h3", "ctitle", t("levelWeeks")));
    chart.appendChild(columns(weeks, avgLevelAt));
    box.appendChild(chart);

    var rep = el("div", "card");
    rep.appendChild(el("h3", "ctitle", t("reportsByWeek")));
    rep.appendChild(columns(weeks, function (w) {
      var n = hub.st.filter(function (s) { var c = hist(s).charAt(w); return c && c !== "-"; }).length;
      return hub.st.length ? n / hub.st.length * 100 : null;
    }));
    box.appendChild(rep);

    // показатели недели по группе
    var cur = questionAvg(0), last = questionAvg(1);
    if (cur.some(function (v) { return v !== null; })) {
      var qcard = el("div", "card");
      qcard.appendChild(el("h3", "ctitle", t("questionsWeek")));
      hub.wk.q.forEach(function (q, i) {
        if (cur[i] === null) return;
        var row = el("div", "qbar");
        row.appendChild(el("span", "qname", q[1]));
        var bar = el("span", "qtrack");
        var fill = el("i");
        bar.appendChild(fill);
        row.appendChild(bar);
        var p = Math.round(cur[i] / 3 * 100);
        var dl = last[i] === null ? null : Math.round((cur[i] - last[i]) / 3 * 100);
        row.appendChild(el("small", "qval" + (dl > 0 ? " up" : dl < 0 ? " down" : ""),
                           p + "%" + (dl ? (dl > 0 ? " ▲" : " ▼") : "")));
        qcard.appendChild(row);
        if (SB.reduced) fill.style.width = p + "%"; else setTimeout(function () { fill.style.width = p + "%"; }, 80 + i * 50);
      });
      box.appendChild(qcard);
    }

    // кто растёт и кому помочь: последний уровень против среднего за прошлые недели
    var trend = hub.st.map(function (s) {
      var h = hist(s), lv = levelOf(s), past = [];
      var lastIdx = -1;
      for (var j = h.length - 1; j >= 0; j--) if (h.charAt(j) !== "-") { lastIdx = j; break; }
      for (j = 0; j < lastIdx; j++) if (h.charAt(j) !== "-") past.push(+h.charAt(j));
      var avg = past.length ? past.reduce(function (a, b) { return a + b; }, 0) / past.length : null;
      return { s: s, lv: lv, d: lv === null || avg === null ? null : lv - avg };
    });
    var up = trend.filter(function (x) { return x.d !== null && x.d >= 0.5; })
      .sort(function (a, b) { return b.d - a.d; }).slice(0, 3);
    var down = trend.filter(function (x) { return x.lv !== null && (x.lv <= 3 || (x.d !== null && x.d <= -0.5)); })
      .sort(function (a, b) { return a.lv - b.lv; }).slice(0, 3);
    var two = el("div", "two");
    two.appendChild(peopleCard("🚀 " + t("growing"), up, "good"));
    two.appendChild(peopleCard("🤝 " + t("needHelp"), down, "bad"));
    box.appendChild(two);
    stagger(box);
  }

  function peopleCard(title, items, cls) {
    var c = el("div", "card people " + cls);
    c.appendChild(el("h3", "ctitle", title));
    if (!items.length) c.appendChild(el("p", "hint", t("nobody")));
    items.forEach(function (x) {
      var b = el("button", "person");
      b.type = "button";
      b.appendChild(SB.avatar(x.s[1], x.s[0]));
      b.appendChild(el("span", "grow", x.s[1]));
      b.appendChild(el("small", "", pct(x.lv) + "%"));
      b.addEventListener("click", function () { tab = "students"; renderTabbar(); sub(function () { profile(x.s[0]); }); });
      c.appendChild(b);
    });
    return c;
  }

  // ---------------------------------------------------------------- подсказки

  function hintsScreen() {
    var marked = {};
    var draw = function () {
      var box = screen("hints");
      backRow(box, t("hints"));
      if (!hub.hn || !hub.hn.length) {
        box.appendChild(SB.mascot("happy", 96));
        box.appendChild(el("div", "empty-state", t("hintsEmpty")));
        SB.setSave(t("save"), function () {}, false);
        return;
      }
      box.appendChild(el("p", "hint", t("markToClose")));
      hub.hn.forEach(function (h) {
        var s = student(h[1]);
        var b = el("button", "choice hint-choice" + (marked[h[0]] ? " selected" : "") + (h[4] === "growth" ? " good" : ""));
        b.type = "button";
        b.appendChild(SB.avatar(s ? s[1] : "?", h[1]));
        var text = el("span", "grow");
        text.appendChild(el("span", "", (h[4] === "growth" ? "🌟 " : "⚠️ ") + (s ? s[1] : "") + " — " + h[2]));
        if (h[3]) text.appendChild(el("span", "sub", t("why") + ": " + h[3]));
        b.appendChild(text);
        b.appendChild(el("span", "mark", marked[h[0]] ? "✓" : ""));
        b.addEventListener("click", function () { marked[h[0]] = !marked[h[0]]; SB.haptic("select"); draw(); });
        box.appendChild(b);
      });
      var ids = Object.keys(marked).filter(function (k) { return marked[k]; }).map(Number);
      SB.setSave(t("closeMarked", { n: ids.length }), function () {
        SB.haptic("success");
        SB.send({ v: 1, u: SB.uuid(), t: "hints", g: hub.gid, close: ids });
      }, ids.length > 0);
    };
    nav = draw;
    draw();
  }

  // ---------------------------------------------------------------- карточки

  function cardsScreen() {
    var ready = cardsReady().map(function (s) { return s[0]; });
    var chosen = {};
    ready.forEach(function (id) { chosen[id] = true; });
    var draw = function () {
      var box = screen("cards");
      backRow(box, t("cards"));
      var intro = el("div", "card soft cards-intro");
      intro.appendChild(el("span", "big-emoji", "💌"));
      intro.appendChild(el("span", "grow", t("cardsText")));
      box.appendChild(intro);
      if (ready.length > 1) {
        var all = el("button", "link", "☑ " + t("selectAll"));
        all.type = "button";
        all.addEventListener("click", function () { ready.forEach(function (id) { chosen[id] = true; }); draw(); });
        var h = el("div", "h2row");
        h.appendChild(el("h2", "", t("selectStudents")));
        h.appendChild(all);
        box.appendChild(h);
      }
      hub.st.forEach(function (s) {
        var ok = ready.indexOf(s[0]) >= 0;
        var b = el(ok ? "button" : "div", "choice" + (ok && chosen[s[0]] ? " selected" : "") + (ok ? "" : " muted"));
        if (ok) b.type = "button";
        b.appendChild(SB.avatar(s[1], s[0]));
        var tx = el("span", "grow");
        tx.appendChild(el("span", "", s[1] + (starred(s[0]) ? " ⭐" : "")));
        tx.appendChild(el("span", "sub", ok ? t("cardsReady") : !s[4] ? t("cardsNoConsent") : t("cardsNoReport")));
        b.appendChild(tx);
        if (ok) {
          b.appendChild(el("span", "mark", chosen[s[0]] ? "✓" : ""));
          b.addEventListener("click", function () { chosen[s[0]] = !chosen[s[0]]; SB.haptic("select"); draw(); });
        }
        box.appendChild(b);
      });
      var ids = ready.filter(function (id) { return chosen[id]; });
      SB.setSave(t("sendCards", { n: ids.length }), function () {
        SB.haptic("success");
        var body = { v: 1, u: SB.uuid(), t: "cards", g: hub.gid };
        if (ids.length !== ready.length) body.ids = ids;
        SB.send(body);
      }, ids.length > 0);
    };
    nav = draw;
    draw();
  }

  // ---------------------------------------------------------------- запуск

  document.getElementById("hubback").addEventListener("click", function () { go(tab); });

  SB.load(DEMO, function (d, isDemo) {
    hub = d;
    hub.st = hub.st || [];
    hub.wk = hub.wk || { q: [], a: {}, c: {}, sr: {} };
    demo = isDemo;
    SB.demoMode = isDemo;
    document.title = t("journal") + " " + hub.g;
    var startTab = (/[?&]tab=(\w+)/.exec(location.search) || [])[1];
    go(["home", "students", "map", "stats"].indexOf(startTab) >= 0 ? startTab : "home");
  });
})();
