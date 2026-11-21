/*
 * Приложение группы — главный интерфейс учителя.
 * Открывается кнопкой «📱 Группа» под полем ввода в чате бота. Все данные группы приходят
 * в ссылке; сохранение — одним Telegram.WebApp.sendData (после него Telegram закрывает приложение,
 * а бот отвечает в чат).
 *
 * Главный экран: неделя и экзамен, прогресс недельных отчётов, плитки разделов:
 * посещаемость, недельный отчёт, экзамен, тема (готовые формы из ../forms/),
 * станции учеников, подсказки, карточки для родителей (здесь же).
 */
(function () {
  "use strict";

  var DEMO = {
    v: 1, f: "hub", gid: 1, g: "10-А", sj: "Английский", lang: "ru", hdr: "Курс A1 · неделя 6 из 8 · экзамен 15 декабря",
    st: [[11, "Азиз К.", "uz", 6, 1], [12, "Мадина Ю.", "ru", 6, 1], [13, "Жасур А.", "uz", 6, 0],
         [14, "Камила Р.", "ru", 4, 1], [15, "Отабек С.", "uz", 6, 1], [16, "Севара О.", "ru", 6, 1]],
    att: { today: SB.localDate(), days: "1,3,5", h: { "2": "000100" } },
    wk: {
      wk: SB.iso(SB.addDays(new Date(), -((new Date().getDay() + 6) % 7))),
      q: [[1, "Домашнее задание", "не сделано", "частично", "сделано с ошибками", "сделано хорошо"],
          [2, "Работа на уроке", "пассивен", "отвечает, когда спросят", "активно участвует", "помогает другим"],
          [3, "Новые слова", "не выучены", "выучена часть", "выучено большинство", "выучены все"],
          [4, "Грамматика темы", "не понял", "понимает с подсказкой", "применяет с ошибками", "применяет уверенно"],
          [5, "Говорение", "молчит", "отдельные слова", "простые фразы", "свободно для своего уровня"],
          [7, "Дисциплина", "мешал", "отвлекался", "нормально", "образцово"]],
      ph: [["Молодец!", "Barakalla!"], ["Нужно повторять слова.", "Soʻzlarni takrorlash kerak."]],
      a: { "11": { "0": "322123", "1": "211012" }, "12": { "0": "333232" }, "13": { "1": "211012" } }, c: {}
    },
    ex: { s: 6, sn: "Курс A1", nx: "Курс A2", fork: false, mode: "score", pass: 60, max: 100, prev: {} },
    tp: { cur: "Unit 5. Present Simple", u: [[1, 5, "Present Simple"], [2, 6, "My day"]] },
    hn: [[101, 13, "Свяжитесь с родителем", "пропуски: 12 ноября и 14 ноября"],
         [102, 11, "Похвалите", "средний балл растёт 3 недели подряд"]],
    stg: [[4, "Roundup 4"], [6, "Курс A1"], [7, "Курс A2"], [8, "Курс B1"]], gs: 6
  };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var hub, demo = false;

  function stName(id) {
    var found = (hub.stg || []).filter(function (s) { return s[0] === id; })[0];
    return found ? found[1] : "—";
  }

  function student(id) { return hub.st.filter(function (s) { return s[0] === id; })[0]; }

  // ---------------------------------------------------------------- данные для готовых форм

  function sub(kind) {
    var base = { v: 1, gid: hub.gid, g: hub.g, lang: hub.lang };
    var out = {};
    for (var k in base) out[k] = base[k];
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

  // Полоска «← Журнал 10-А» над разделом: на всех устройствах есть дорога на главный экран
  function hubbar(show) {
    var bar = document.getElementById("hubbar");
    if (!bar) return;
    document.getElementById("hubname").textContent = t("journal") + " " + hub.g;
    bar.classList.toggle("hidden", !show);
  }

  function open(kind) {
    SB.haptic("select");
    hubbar(true);
    window.scrollTo(0, 0);
    SB.hubHome = home;
    SB.setBack(home);
    if (SB.forms[kind]) return SB.forms[kind].start(sub(kind), demo);
    if (kind === "hints") return hints();
    if (kind === "stations") return stations();
    if (kind === "cards") return cards();
  }

  // ---------------------------------------------------------------- главный экран

  function weeklyDone() {
    return hub.st.filter(function (s) {
      var rec = (hub.wk.a || {})[String(s[0])];
      return rec && rec["0"];
    }).length;
  }

  function tile(icon, title, subText, kind, opts) {
    opts = opts || {};
    var b = el("button", "tile" + (opts.wide ? " wide" : "") + (opts.disabled ? " disabled" : ""));
    b.type = "button";
    b.appendChild(el("span", "icon", icon));
    var text = el("span", "text");
    text.appendChild(el("b", "", title));
    text.appendChild(el("span", "sub", subText));
    b.appendChild(text);
    if (opts.count) b.appendChild(el("span", "count", String(opts.count)));
    if (!opts.disabled) b.addEventListener("click", function () { open(kind); });
    return b;
  }

  function home() {
    hubbar(false);
    SB.hubHome = null;
    SB.setBack(null);
    SB.setSave(t("save"), function () {}, false);
    app.innerHTML = "";
    window.scrollTo(0, 0);

    var hero = el("div", "hero");
    hero.appendChild(el("small", "", t("journal") + (hub.sj ? " · " + hub.sj : "")));
    hero.appendChild(el("div", "title", hub.g));
    hero.appendChild(el("div", "line", hub.hdr || ""));
    var done = weeklyDone(), total = hub.st.length;
    var bar = el("div", "progress");
    var fill = el("span");
    fill.style.width = (total ? Math.round(100 * done / total) : 0) + "%";
    bar.appendChild(fill);
    hero.appendChild(bar);
    var label = el("div", "progress-label");
    label.appendChild(el("span", "", t("reportsWeek")));
    label.appendChild(el("span", "", done + " / " + total));
    hero.appendChild(label);
    app.appendChild(hero);
    if (demo) app.appendChild(el("p", "hint", t("demo")));

    var grid = el("div", "tiles");
    var attToday = hub.att && hub.att.h && hub.att.h["0"];
    grid.appendChild(tile("✅", t("attendance"), attToday ? "✓ " + t("attToday") : t("attMark"), "attendance"));
    grid.appendChild(tile("📝", t("weekly"), done + " / " + total, "weekly"));
    if (hub.ex) {
      grid.appendChild(tile("🎓", hub.ex.mode === "score" ? t("exam") : t("decision"),
                            hub.ex.sn + (hub.ex.nx ? " ➜ " + hub.ex.nx : ""), "exam"));
    } else {
      grid.appendChild(tile("🎓", t("exam"), t("noExam"), "exam", { disabled: true }));
    }
    grid.appendChild(tile("📚", t("topic"), hub.tp && hub.tp.cur ? hub.tp.cur : t("noTopic"), "topic"));
    if (hub.stg && hub.stg.length) {
      grid.appendChild(tile("🗺", t("stations"), hub.gs ? stName(hub.gs) : t("stationsSub"), "stations"));
    }
    var hintCount = (hub.hn || []).length;
    grid.appendChild(tile("⚠️", t("hints"), hintCount ? t("hintsN", { n: hintCount }) : t("noHints"), "hints",
                          { count: hintCount }));
    var ready = cardsReady().length;
    grid.appendChild(tile("📤", t("cards"), t("cardsSub", { k: ready, n: total }), "cards", { wide: true }));
    app.appendChild(grid);
    app.appendChild(el("p", "hint", t("footer")));
  }

  // ---------------------------------------------------------------- подсказки

  function hints() {
    var marked = {};
    var draw = function () {
      app.innerHTML = "";
      header(t("hints"));
      if (!hub.hn || !hub.hn.length) {
        app.appendChild(el("div", "card soft", t("hintsEmpty")));
        SB.setSave(t("save"), function () {}, false);
        return;
      }
      app.appendChild(el("p", "hint", t("markToClose")));
      hub.hn.forEach(function (h) {
        var s = student(h[1]);
        var b = el("button", "choice" + (marked[h[0]] ? " selected" : ""));
        b.type = "button";
        b.appendChild(SB.avatar(s ? s[1] : "?", h[1]));
        var text = el("span", "grow");
        text.appendChild(el("span", "", (s ? s[1] : "") + " — " + h[2]));
        text.appendChild(el("span", "sub", t("why") + ": " + h[3]));
        b.appendChild(text);
        b.appendChild(el("span", "mark", marked[h[0]] ? "✓" : ""));
        b.addEventListener("click", function () { marked[h[0]] = !marked[h[0]]; SB.haptic("select"); draw(); });
        app.appendChild(b);
      });
      var ids = Object.keys(marked).filter(function (k) { return marked[k]; }).map(Number);
      SB.setSave(t("closeMarked", { n: ids.length }), function () {
        SB.haptic("success");
        SB.send({ v: 1, u: SB.uuid(), t: "hints", g: hub.gid, close: ids });
      }, ids.length > 0);
    };
    draw();
  }

  // ---------------------------------------------------------------- станции

  function stations() {
    var who = null, target = null;  // who: 0 — вся группа, иначе ученик
    var draw = function () {
      app.innerHTML = "";
      window.scrollTo(0, 0);
      header(t("stations"));
      if (who === null) {
        SB.setBack(home);
        SB.setSave(t("save"), function () {}, false);
        var g = el("button", "choice");
        g.type = "button";
        g.appendChild(el("span", "icon", "👥"));
        var gt = el("span", "grow");
        gt.appendChild(el("span", "", t("wholeGroup")));
        gt.appendChild(el("span", "sub", t("groupNow", { s: stName(hub.gs) })));
        g.appendChild(gt);
        g.addEventListener("click", function () { who = 0; SB.haptic("select"); draw(); });
        app.appendChild(g);
        hub.st.forEach(function (s) {
          var b = el("button", "choice");
          b.type = "button";
          b.appendChild(SB.avatar(s[1], s[0]));
          var st = el("span", "grow");
          st.appendChild(el("span", "", s[1]));
          st.appendChild(el("span", "sub", stName(s[3])));
          b.appendChild(st);
          b.addEventListener("click", function () { who = s[0]; SB.haptic("select"); draw(); });
          app.appendChild(b);
        });
        return;
      }
      SB.setBack(function () { who = null; target = null; draw(); });
      var current = who === 0 ? hub.gs : (student(who) || [])[3];
      var name = who === 0 ? t("wholeGroup") + " " + hub.g : student(who)[1];
      app.appendChild(el("h2", "", name + " — " + t("pickStation")));
      hub.stg.forEach(function (s) {
        if (s[0] === current) return;
        var b = el("button", "choice" + (target === s[0] ? " selected" : ""), s[1]);
        b.type = "button";
        b.addEventListener("click", function () { target = s[0]; SB.haptic("select"); draw(); });
        app.appendChild(b);
      });
      if (target) {
        var note = el("div", "card soft");
        note.appendChild(el("div", "", t("moveConfirm", { who: name, from: stName(current), to: stName(target) })));
        note.appendChild(el("div", "hint", t("skippedNote") + (who === 0 ? " " + t("examRestart") : "")));
        app.appendChild(note);
      }
      SB.setSave(t("move"), function () {
        SB.haptic("success");
        SB.send({ v: 1, u: SB.uuid(), t: "move", g: hub.gid, sid: who, s: target });
      }, !!target);
    };
    draw();
  }

  // ---------------------------------------------------------------- карточки

  function cardsReady() {
    return hub.st.filter(function (s) {
      var rec = (hub.wk.a || {})[String(s[0])];
      return s[4] && rec && (rec["0"] || rec["1"]);
    });
  }

  function cards() {
    app.innerHTML = "";
    header(t("cards"));
    app.appendChild(el("div", "card soft", t("cardsText")));
    var ready = cardsReady().map(function (s) { return s[0]; });
    hub.st.forEach(function (s) {
      var rec = (hub.wk.a || {})[String(s[0])];
      var reason = ready.indexOf(s[0]) >= 0 ? t("cardsReady") : !s[4] ? t("cardsNoConsent") : t("cardsNoReport");
      var row = el("div", "choice");
      row.appendChild(SB.avatar(s[1], s[0]));
      row.appendChild(el("span", "grow", s[1]));
      row.appendChild(el("span", "pill " + (ready.indexOf(s[0]) >= 0 ? "done" : "empty"), reason));
      app.appendChild(row);
      void rec;
    });
    SB.setSave(t("sendCards", { n: ready.length }), function () {
      SB.haptic("success");
      SB.send({ v: 1, u: SB.uuid(), t: "cards", g: hub.gid });
    }, ready.length > 0);
  }

  function header(title) {
    var top = el("div", "topbar");
    var tt = el("div", "grow");
    tt.appendChild(el("h1", "", title));
    tt.appendChild(el("span", "group-chip", "👥 " + hub.g));
    top.appendChild(tt);
    app.appendChild(top);
  }

  document.getElementById("hubback").addEventListener("click", function () { home(); });

  SB.load(DEMO, function (d, isDemo) {
    hub = d;
    demo = isDemo;
    SB.demoMode = isDemo;
    home();
  });
})();
