/*
 * Панель центра — приложение владельца (Telegram Mini App).
 * Кнопка «📊 Панель центра» под полем ввода у владельца. Все данные — в ссылке кнопки.
 * Вкладки: Обзор · Учителя · Группы · Станции.
 * Команды боту (sendData): напомнить учителям, сводка в чат, бэкап.
 * Владелец видит только итоги: имена учеников — имя и первая буква фамилии.
 */
(function () {
  "use strict";

  var el = SB.el, t = SB.t;
  var app = document.getElementById("app");
  var D, demo = false, tab = "home", gFilter = "all", teacherFilter = null;

  // поля группы в ссылке
  var G = { id: 0, name: 1, tIdx: 2, sc: 3, sj: 4, stage: 5, n: 6, done: 7, lvl: 8, prev: 9, hints: 10,
            exd: 11, wkn: 12, wkt: 13, stars: 14, skills: 15 };

  function mondayISO(back) {
    var d = new Date(), wd = (d.getDay() + 6) % 7;
    return SB.iso(SB.addDays(d, -wd - 7 * back));
  }
  var DEMO = {
    v: 2, f: "owner", lang: "ru", today: SB.localDate(), wk: mondayISO(0), center: "Учебный центр", att: false,
    k: [96, 81, 8, 5],
    t: [[1, "Дилноза А.", 0], [2, "Бахтиёр Р.", 0], [3, "Гульнора С.", 0], [4, "Сардор К.", 0], [5, "Саида К.", 1]],
    g: [[1, "10-А", 0, "en", "Английский", "Курс A1", 14, 14, 7, 6, 1, SB.iso(SB.addDays(new Date(), 5)), 7, 8, 2, 74],
        [2, "Kids-2", 0, "en", "Английский", "Roundup 3", 11, 6, 6, 6, 2, "", 9, 0, 1, 61],
        [3, "11-Б", 1, "en", "Английский", "Курс B1", 12, 12, 8, 7, 0, SB.iso(SB.addDays(new Date(), 30)), 4, 8, 3, 80],
        [4, "IELTS-1", 1, "en", "Английский", "IELTS", 9, 3, 6, 7, 3, "", 6, 0, 0, 68],
        [5, "М-5", 2, "math", "Математика", "5 класс", 13, 13, 5, 4, 1, "", 11, 0, 1, 66],
        [6, "М-8", 2, "math", "Математика", "8 класс", 12, 9, 6, 6, 0, "", 3, 0, 0, -1],
        [7, "Рус-1", 3, "ru", "Русский", "", 15, 0, -1, 5, 0, "", 5, 0, 0, -1],
        [8, "Kor-1", 3, "ko", "Корейский", "", 10, 7, 5, 5, 1, "", 2, 0, 0, 58]],
    hist: [[mondayISO(7), 70, 96], [mondayISO(6), 82, 96], [mondayISO(5), 88, 96], [mondayISO(4), 79, 96],
           [mondayISO(3), 91, 96], [mondayISO(2), 93, 96], [mondayISO(1), 95, 96], [mondayISO(0), 64, 96]],
    grades: [40, 160, 310, 230],
    dist: [["Английский", [["Starter", 0, "Для детей"], ["Roundup 1", 3, "Для детей"], ["Roundup 2", 5, "Для детей"],
                           ["Roundup 3", 11, "Для детей"], ["Roundup 4", 2, "Для детей"], ["Курс A1", 14, "Общий английский"],
                           ["Курс A2", 4, "Общий английский"], ["Курс B1", 12, "Общий английский"], ["Курс B2", 3, "Общий английский"],
                           ["Pre-IELTS", 2, "Экзамен IELTS"], ["IELTS", 9, "Экзамен IELTS"]]],
           ["Математика", [["4 класс", 2, "1–4 класс"], ["5 класс", 13, "5–8 класс"], ["8 класс", 12, "5–8 класс"]]]],
    risk: [["Жасур А.", "10-А", "Риск не сдать экзамен", "уровень 45% при проходном 60%"],
           ["Нигора Х.", "IELTS-1", "Резкий спад: говорение", "было 2,5, стало 1"],
           ["Ислом М.", "Kids-2", "Домашка проседает", "недели: 09.11–14.11, 16.11–21.11"]],
    good: [["Севара О.", "11-Б", "Похвалите", "средний балл растёт 3 недели подряд"],
           ["Мадина Ю.", "10-А", "★ Звезда недели", ""]]
  };

  SB.addTexts({
    ru: {
      oTitle: "Панель центра", oOverview: "Обзор", oTeachers: "Учителя", oGroups: "Группы", oStations: "Станции",
      oCenter: "Панель центра", oWeek: "Неделя {w}", oReports: "отчёты недели",
      oStudents: "учеников", oConsent: "с согласием", oGroupsK: "групп", oTeachersK: "учителей",
      oActions: "Команды боту", oRemind: "Напомнить учителям", oRemindSub: "у кого есть незаполненные отчёты",
      oRemindAsk: "Отправить напоминание учителям, у которых не заполнены отчёты этой недели?",
      oExport: "Выгрузить отчёты в Excel", oExportSub: "эта и прошлая неделя: все ученики, оценки, цели, комментарии",
      oSummary: "Сводка в чат", oSummarySub: "отчёты, оценки, экзамены", oBackup: "Бэкап сейчас", oBackupSub: "в закрытый канал",
      oByWeeks: "Отчёты по неделям, %", oGrades: "Оценки недели", oInflated: "Почти все ответы «отлично» — возможно, оценки завышены",
      oExams: "Экзамены скоро", oNoExams: "В ближайшие 3 недели экзаменов нет", oInDays: "через {n} дн.", oToday: "сегодня",
      oHelp: "Кому нужна помощь", oPraise: "Кого похвалить", oNobody: "Пока никого",
      oFilled: "{d} из {n}", oLevel: "уровень", oSkills: "навыки {v}/10", oSupport: "саппорт · все группы", oNoTeacher: "без учителя", oHints: "подсказок: {n}",
      fAll: "Все", fBehind: "Отстают", fExams: "Экзамены", fHints: "Подсказки",
      oAllGroups: "Все группы", oOnStation: "учеников на станциях", oNoMap: "Нет предметов с картой станций",
      oDataAt: "Данные на момент нажатия кнопки. Чтобы обновить — «🔄 Обновить» в чате.",
      oDemo: "Демо: все имена и цифры выдуманы", oStars: "★ {n}", oWeekOf: "нед. {n}/{t}", oWeekN: "нед. {n}",
      g0: "слабо", g1: "так себе", g2: "хорошо", g3: "отлично", oTeacherGroups: "Группы учителя {n}"
    },
    uz: {}
  });

  function it(tag, cls, iconName, text) {
    var e = el(tag, cls);
    if (iconName) e.appendChild(SB.icon(iconName));
    if (text !== undefined && text !== null) e.appendChild(document.createTextNode(text));
    return e;
  }

  function pctOf(a, b) { return b ? Math.round(100 * a / b) : 0; }
  function daysTo(iso) { return iso ? Math.round((SB.parseISO(iso) - SB.parseISO(D.today)) / 86400000) : null; }
  function lvlPct(l) { return l < 0 ? null : Math.round(l / 9 * 100); }
  function teacherName(i) { return i >= 0 && D.t[i] ? D.t[i][1] : t("oNoTeacher"); }

  function screen() {
    app.innerHTML = "";
    window.scrollTo(0, 0);
    var box = el("div", "screen");
    app.appendChild(box);
    return box;
  }
  function stagger(container) {
    for (var i = 0; i < container.children.length; i++) {
      container.children[i].classList.add("rise");
      container.children[i].style.animationDelay = Math.min(i * 45, 400) + "ms";
    }
  }
  function head(box, title) {
    var h = el("div", "tabhead");
    var tr = el("div", "title-row");
    tr.appendChild(SB.logo());
    tr.appendChild(el("h1", "", title));
    h.appendChild(tr);
    if (D.center) h.appendChild(el("span", "group-chip", D.center));
    box.appendChild(h);
  }

  function tabbar() {
    var bar = document.getElementById("tabbar");
    bar.innerHTML = "";
    [["home", "home", t("oOverview")], ["teachers", "user", t("oTeachers")], ["groups", "users", t("oGroups")],
     ["stations", "map", t("oStations")]].forEach(function (it) {
      var b = el("button", "tab" + (tab === it[0] ? " active" : ""));
      b.type = "button";
      b.appendChild(SB.icon(it[1]));
      b.appendChild(el("span", "tab-label", it[2]));
      b.addEventListener("click", function () { go(it[0]); });
      bar.appendChild(b);
    });
  }

  function go(name, keepFilter) {
    if (name !== tab) SB.haptic("select");
    tab = name;
    if (!keepFilter) teacherFilter = null;
    tabbar();
    SB.setSave(t("save"), function () {}, false);
    SB.setBack(name === "home" ? null : function () { go("home"); });
    if (name === "teachers") return teachersTab();
    if (name === "groups") return groupsTab();
    if (name === "stations") return stationsTab();
    return homeTab();
  }

  function send(kind, ask) {
    var run = function () { SB.haptic("success"); SB.send({ v: 1, u: SB.uuid(), t: kind }); };
    if (ask) SB.confirm(ask, function (ok) { if (ok) run(); }); else run();
  }

  // ---------------------------------------------------------------- обзор

  function totals() {
    var n = 0, done = 0;
    D.g.forEach(function (g) { n += g[G.n]; done += g[G.done]; });
    return [done, n];
  }

  function homeTab() {
    var box = screen();
    var tot = totals(), p = pctOf(tot[0], tot[1]);
    var hero = el("div", "hero2");
    var left = el("div", "hero-left");
    left.appendChild(el("small", "", t("oCenter")));
    left.appendChild(el("div", "title", D.center || "SchoolBot"));
    var chips = el("div", "hero-chips");
    var mon = SB.parseISO(D.wk);
    chips.appendChild(el("span", "hchip", t("oWeek", { w: SB.weekRange(mon) })));
    chips.appendChild(el("span", "hchip", t("oFilled", { d: tot[0], n: tot[1] })));
    left.appendChild(chips);
    hero.appendChild(left);
    var r = SB.ring(p, 92, 10, "hero-ring");
    var mid = el("span", "ring-mid");
    var num = el("b");
    mid.appendChild(num);
    mid.appendChild(el("small", "", "%"));
    r.appendChild(mid);
    r.appendChild(el("span", "ring-cap", t("oReports")));
    SB.countUp(num, p);
    hero.appendChild(r);
    box.appendChild(hero);
    if (demo) box.appendChild(el("p", "hint center", t("oDemo")));

    var kpi = el("div", "kpis");
    [[D.k[0], t("oStudents"), "cap"], [D.k[1], t("oConsent"), "pen"], [D.k[2], t("oGroupsK"), "users"],
     [D.k[3], t("oTeachersK"), "user"]].forEach(function (k) {
      var c = el("div", "kpi");
      c.appendChild(it("span", "kpi-icon", k[2]));
      var b = el("b");
      SB.countUp(b, k[0]);
      c.appendChild(b);
      c.appendChild(el("small", "", k[1]));
      kpi.appendChild(c);
    });
    box.appendChild(kpi);

    box.appendChild(el("h2", "", t("oActions")));
    var acts = el("div");
    acts.appendChild(action("bell", t("oRemind"), t("oRemindSub"), "orange", function () { send("o_remind", t("oRemindAsk")); }));
    acts.appendChild(action("download", t("oExport"), t("oExportSub"), "violet", function () { send("o_export"); }));
    acts.appendChild(action("file", t("oSummary"), t("oSummarySub"), "blue", function () { send("o_summary"); }));
    acts.appendChild(action("database", t("oBackup"), t("oBackupSub"), "green", function () { send("o_backup"); }));
    box.appendChild(acts);

    // отчёты по неделям
    var ch = el("div", "card");
    ch.appendChild(el("h3", "ctitle", t("oByWeeks")));
    var cols = el("div", "cols");
    D.hist.forEach(function (w, i) {
      var v = w[2] ? 100 * w[1] / w[2] : null;
      var col = el("span", "col" + (i === D.hist.length - 1 ? " now" : "") + (v === null ? " none" : ""));
      var fill = el("i");
      col.appendChild(el("small", "colval", v === null ? "" : Math.round(v) + ""));
      col.appendChild(fill);
      col.appendChild(el("small", "", SB.parseISO(w[0]).getDate() + "." + (SB.parseISO(w[0]).getMonth() + 1)));
      cols.appendChild(col);
      var h = v === null ? 6 : Math.max(6, v * 0.85);
      setTimeout(function () { fill.style.height = h + "%"; }, 60 + i * 40);
    });
    ch.appendChild(cols);
    box.appendChild(ch);

    // оценки недели
    var sum = D.grades.reduce(function (a, b) { return a + b; }, 0);
    if (sum) {
      var gc = el("div", "card");
      gc.appendChild(el("h3", "ctitle", t("oGrades")));
      var bar = el("div", "stack-bar");
      D.grades.forEach(function (c, i) {
        var part = el("i", "g" + i);
        part.style.width = (100 * c / sum) + "%";
        bar.appendChild(part);
      });
      gc.appendChild(bar);
      var legend = el("div", "legend");
      D.grades.forEach(function (c, i) {
        var l = el("span", "");
        l.appendChild(el("i", "g" + i));
        l.appendChild(document.createTextNode(t("g" + i) + " " + Math.round(100 * c / sum) + "%"));
        legend.appendChild(l);
      });
      gc.appendChild(legend);
      if (sum >= 20 && D.grades[3] / sum >= 0.8) gc.appendChild(el("div", "error-box", t("oInflated")));
      box.appendChild(gc);
    }

    // экзамены скоро
    var soon = D.g.filter(function (g) { var d = daysTo(g[G.exd]); return d !== null && d >= 0 && d <= 21; })
      .sort(function (a, b) { return daysTo(a[G.exd]) - daysTo(b[G.exd]); });
    box.appendChild(el("h2", "", t("oExams")));
    if (!soon.length) box.appendChild(el("div", "empty-state", t("oNoExams")));
    soon.forEach(function (g) {
      var d = daysTo(g[G.exd]);
      var row = el("div", "hintrow " + (d <= 7 ? "bad" : "good"));
      var tx = el("span", "grow");
      tx.appendChild(el("b", "", g[G.name] + " · " + g[G.stage]));
      tx.appendChild(el("span", "sub", teacherName(g[G.tIdx]) + " · " + SB.parseISO(g[G.exd]).getDate() + "." +
                        (SB.parseISO(g[G.exd]).getMonth() + 1)));
      row.appendChild(tx);
      row.appendChild(el("span", "mini-chip " + (d <= 7 ? "warn" : ""), d === 0 ? t("oToday") : t("oInDays", { n: d })));
      box.appendChild(row);
    });

    box.appendChild(people(t("oHelp"), D.risk, "bad"));
    box.appendChild(people(t("oPraise"), D.good, "good"));
    box.appendChild(el("p", "hint center footer", t("oDataAt")));
    stagger(box);
  }

  function action(icon, title, subText, color, onClick) {
    var b = el("button", "action-row " + color);
    b.type = "button";
    var qi = el("span", "qicon");
    qi.appendChild(SB.icon(icon));
    b.appendChild(qi);
    var tx = el("span", "grow");
    tx.appendChild(el("b", "", title));
    tx.appendChild(el("span", "sub", subText));
    b.appendChild(tx);
    b.appendChild(SB.icon("chevron"));
    b.addEventListener("click", onClick);
    return b;
  }

  function people(title, items, cls) {
    var c = el("div", "card people " + cls);
    c.appendChild(el("h3", "ctitle", title));
    if (!items.length) c.appendChild(el("p", "hint", t("oNobody")));
    items.forEach(function (x, i) {
      var row = el("div", "person");
      row.appendChild(SB.avatar(x[0], i + (cls === "bad" ? 3 : 0)));
      var tx = el("span", "grow");
      tx.appendChild(el("span", "pname", x[0] + " · " + x[1]));
      tx.appendChild(el("small", "psub", x[2] + (x[3] ? ": " + x[3] : "")));
      row.appendChild(tx);
      c.appendChild(row);
    });
    return c;
  }

  // ---------------------------------------------------------------- учителя

  function teachersTab() {
    var box = screen();
    head(box, t("oTeachers"));
    var list = el("div");
    D.t.forEach(function (tc, i) {
      var groups = D.g.filter(function (g) { return g[G.tIdx] === i; });
      var n = 0, done = 0, hints = 0, lv = [];
      groups.forEach(function (g) { n += g[G.n]; done += g[G.done]; hints += g[G.hints]; if (g[G.lvl] >= 0) lv.push(g[G.lvl]); });
      var p = pctOf(done, n);
      var b = el("button", "srow");
      b.type = "button";
      var r = SB.ring(p, 56, 6, "lvl-ring " + (p >= 90 ? "lvhi" : p >= 50 ? "lvmid" : "lvlo"));
      r.appendChild(el("b", "ring-num", n ? p + "%" : "—"));
      b.appendChild(r);
      var mid = el("span", "grow");
      mid.appendChild(el("b", "", tc[1]));
      var meta = el("span", "meta");
      if (tc[2]) meta.appendChild(it("span", "role-chip", "lifebuoy", t("oSupport")));
      meta.appendChild(el("span", "mini-chip", groups.length + " " + t("oGroupsK")));
      if (n) meta.appendChild(el("span", "mini-chip " + (done === n ? "ok" : "todo"), t("oFilled", { d: done, n: n })));
      if (hints) meta.appendChild(it("span", "mini-chip warn", "alert", String(hints)));
      mid.appendChild(meta);
      b.appendChild(mid);
      var avg = lv.length ? Math.round(lv.reduce(function (a, c) { return a + c; }, 0) / lv.length / 9 * 100) : null;
      var right = el("span", "sright");
      right.appendChild(el("small", "", avg === null ? "—" : avg + "%"));
      right.appendChild(el("span", "hint", t("oLevel")));
      b.appendChild(right);
      b.addEventListener("click", function () { teacherFilter = i; gFilter = "all"; go("groups", true); });
      list.appendChild(b);
    });
    box.appendChild(list);
    stagger(list);
  }

  // ---------------------------------------------------------------- группы

  function groupsTab() {
    var box = screen();
    head(box, teacherFilter !== null ? t("oTeacherGroups", { n: teacherName(teacherFilter) }) : t("oGroups"));
    var seg = el("div", "filters");
    [["all", t("fAll")], ["behind", t("fBehind")], ["exams", t("fExams")], ["hints", t("fHints")]].forEach(function (f) {
      var b = el("button", "fchip" + (gFilter === f[0] ? " on" : ""), f[1]);
      b.type = "button";
      b.addEventListener("click", function () { gFilter = f[0]; SB.haptic("select"); groupsTab(); });
      seg.appendChild(b);
    });
    if (teacherFilter !== null) {
      var all = el("button", "fchip", "× " + t("oAllGroups"));
      all.type = "button";
      all.addEventListener("click", function () { teacherFilter = null; groupsTab(); });
      seg.appendChild(all);
    }
    box.appendChild(seg);
    var rows = D.g.filter(function (g) {
      if (teacherFilter !== null && g[G.tIdx] !== teacherFilter) return false;
      if (gFilter === "behind") return g[G.done] < g[G.n];
      if (gFilter === "exams") { var d = daysTo(g[G.exd]); return d !== null && d >= 0 && d <= 21; }
      if (gFilter === "hints") return g[G.hints] > 0;
      return true;
    }).sort(function (a, b) { return pctOf(a[G.done], a[G.n]) - pctOf(b[G.done], b[G.n]); });
    var list = el("div");
    if (!rows.length) list.appendChild(el("div", "empty-state", t("oNobody")));
    rows.forEach(function (g) { list.appendChild(groupCard(g)); });
    box.appendChild(list);
    stagger(list);
  }

  function groupCard(g) {
    var c = el("div", "gcard");
    var top = el("div", "gtop");
    var name = el("div", "grow");
    name.appendChild(el("b", "", g[G.name]));
    name.appendChild(el("span", "sub", g[G.sj] + (g[G.stage] ? " · " + g[G.stage] : "") + " · " + teacherName(g[G.tIdx])));
    top.appendChild(name);
    var lv = lvlPct(g[G.lvl]), pv = lvlPct(g[G.prev]);
    var lvBox = el("span", "glevel");
    lvBox.appendChild(el("b", "", lv === null ? "—" : lv + "%"));
    if (lv !== null && pv !== null && lv !== pv) lvBox.appendChild(el("small", lv > pv ? "up" : "down", (lv > pv ? "▲" : "▼") + Math.abs(lv - pv)));
    lvBox.appendChild(el("small", "cap", t("oLevel")));
    top.appendChild(lvBox);
    c.appendChild(top);
    var bar = el("div", "progress");
    var fill = el("span");
    bar.appendChild(fill);
    c.appendChild(bar);
    setTimeout(function () { fill.style.width = pctOf(g[G.done], g[G.n]) + "%"; }, 80);
    var meta = el("div", "meta");
    meta.appendChild(it("span", "mini-chip " + (g[G.done] === g[G.n] ? "ok" : "todo"), "report", t("oFilled", { d: g[G.done], n: g[G.n] })));
    if (g[G.wkn]) meta.appendChild(el("span", "mini-chip", g[G.wkt] ? t("oWeekOf", { n: g[G.wkn], t: g[G.wkt] }) : t("oWeekN", { n: g[G.wkn] })));
    var d = daysTo(g[G.exd]);
    if (d !== null && d >= 0) meta.appendChild(it("span", "mini-chip " + (d <= 7 ? "warn" : ""), "cap", d === 0 ? t("oToday") : t("oInDays", { n: d })));
    if (g[G.hints]) meta.appendChild(it("span", "mini-chip warn", "alert", String(g[G.hints])));
    if (g[G.stars]) meta.appendChild(el("span", "mini-chip star", t("oStars", { n: g[G.stars] })));
    if (g[G.skills] >= 0) meta.appendChild(it("span", "mini-chip", "radar", t("oSkills", { v: (g[G.skills] / 10).toFixed(1) })));
    c.appendChild(meta);
    return c;
  }

  // ---------------------------------------------------------------- станции

  function stationsTab() {
    var box = screen();
    head(box, t("oStations"));
    if (!D.dist || !D.dist.length) { box.appendChild(el("div", "empty-state", t("oNoMap"))); return; }
    D.dist.forEach(function (subj) {
      var c = el("div", "card");
      var total = subj[1].reduce(function (a, s) { return a + s[1]; }, 0);
      c.appendChild(el("h3", "ctitle", subj[0] + " · " + total + " " + t("oStudents")));
      var max = Math.max.apply(null, subj[1].map(function (s) { return s[1]; }).concat([1]));
      var lastSection = null;
      subj[1].forEach(function (s, i) {
        if (s[2] !== lastSection) { c.appendChild(el("div", "dist-section", s[2])); lastSection = s[2]; }
        var row = el("div", "qbar" + (s[1] ? "" : " zero"));
        row.appendChild(el("span", "qname", s[0]));
        var tr = el("span", "qtrack");
        var f = el("i");
        tr.appendChild(f);
        row.appendChild(tr);
        row.appendChild(el("small", "qval", String(s[1])));
        c.appendChild(row);
        setTimeout(function () { f.style.width = (100 * s[1] / max) + "%"; }, 80 + i * 40);
      });
      box.appendChild(c);
    });
    stagger(box);
  }

  SB.load(DEMO, function (d, isDemo) {
    D = d;
    D.g = D.g || []; D.t = D.t || []; D.hist = D.hist || []; D.grades = D.grades || [0, 0, 0, 0];
    D.risk = D.risk || []; D.good = D.good || [];
    demo = isDemo;
    SB.demoMode = isDemo;
    SB.splash(D.center || t("oTitle"));
    var startTab = (/[?&]tab=(\w+)/.exec(location.search) || [])[1];
    go(["home", "teachers", "groups", "stations"].indexOf(startTab) >= 0 ? startTab : "home");
  });
})();
