/* Форма «Посещаемость»: дата урока (до 7 дней назад), нажатие по ученику меняет отметку. */
(function () {
  "use strict";

  var STATUSES = ["present", "late", "absent", "excused"];
  var DAYS_BACK = 7;

  var DEMO = {
    v: 1, f: "att", gid: 1, g: "10-А", lang: "ru", today: SB.localDate(), days: "1,3,5",
    st: [[11, "Азиз К."], [12, "Мадина Ю."], [13, "Жасур А."], [14, "Камила Р."], [15, "Отабек С."],
         [16, "Севара О."], [17, "Тимур Н."], [18, "Лола Т."]],
    h: { "2": "00100320" }
  };

  var data, today, shift = 0, selectedBack = 0, marks = [];
  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;

  function dateFor(back) { return SB.addDays(today, -back); }

  // Отметки в ссылке посчитаны от дня, когда бот собирал кнопку; день на телефоне может быть позже
  function savedFor(back) { return data.h && data.h[String(back - shift)]; }

  function marksFor(back) {
    var saved = savedFor(back);
    return data.st.map(function (s, i) {
      var ch = saved ? saved.charAt(i) : "-";
      return ch >= "0" && ch <= "3" ? +ch : 0; // по умолчанию — «Пришёл»
    });
  }

  function render() {
    app.innerHTML = "";

    var top = el("div", "topbar");
    var title = el("div", "grow");
    title.appendChild(el("h1", "", t("attendance")));
    var chip = el("span", "group-chip", "👥 " + data.g);
    title.appendChild(chip);
    if (data.part) title.appendChild(el("span", "hint", "  " + t("part", { i: data.part[0], n: data.part[1] })));
    top.appendChild(title);
    app.appendChild(top);
    if (SB.demoMode) app.appendChild(el("p", "hint", t("demo")));

    // даты
    var dates = el("div", "dates");
    var lessonDays = (data.days || "").split(",");
    for (var back = 0; back <= DAYS_BACK; back++) {
      (function (back) {
        var d = dateFor(back);
        var b = el("button", "date");
        b.type = "button";
        var isoWd = String(d.getDay() === 0 ? 7 : d.getDay());
        if (lessonDays.indexOf(isoWd) >= 0) b.classList.add("lesson");
        if (savedFor(back)) b.classList.add("saved");
        if (back === selectedBack) b.classList.add("selected");
        b.appendChild(el("small", "", back === 0 ? t("today") : SB.weekday(d)));
        b.appendChild(el("b", "", String(d.getDate())));
        b.appendChild(el("span", "dot"));
        b.addEventListener("click", function () {
          selectedBack = back;
          marks = marksFor(back);
          SB.haptic("select");
          render();
        });
        dates.appendChild(b);
      })(back);
    }
    app.appendChild(dates);

    if (savedFor(selectedBack)) app.appendChild(el("p", "hint ok", "✓ " + t("savedForDate")));

    // счётчики
    var stats = el("div", "stats");
    STATUSES.forEach(function (name, code) {
      var box = el("div", "stat " + name);
      box.appendChild(el("b", "", String(marks.filter(function (m) { return m === code; }).length)));
      box.appendChild(el("small", "", t(name + "Short")));
      stats.appendChild(box);
    });
    app.appendChild(stats);

    var row = el("div", "topbar");
    row.appendChild(el("span", "hint grow", t("tapHint")));
    var all = el("button", "btn ghost small", t("allPresent"));
    all.type = "button";
    all.addEventListener("click", function () {
      marks = marks.map(function () { return 0; });
      SB.haptic("success");
      render();
    });
    row.appendChild(all);
    app.appendChild(row);

    // ученики
    data.st.forEach(function (s, i) {
      var b = el("button", "choice student " + STATUSES[marks[i]]);
      b.type = "button";
      b.appendChild(SB.avatar(s[1], s[0]));
      b.appendChild(el("span", "grow", s[1]));
      b.appendChild(el("span", "pill " + STATUSES[marks[i]], t(STATUSES[marks[i]])));
      b.addEventListener("click", function () {
        marks[i] = (marks[i] + 1) % STATUSES.length;
        SB.haptic("select");
        render();
      });
      app.appendChild(b);
    });

    SB.setSave(t("saveN", { n: data.st.length }), save, data.st.length > 0);
  }

  function save() {
    var payload = {
      v: 1, u: SB.uuid(), t: "att", g: data.gid, d: SB.iso(dateFor(selectedBack)),
      m: data.st.map(function (s, i) { return [s[0], marks[i]]; })
    };
    SB.haptic("success");
    SB.send(payload);
  }

  // Запуск формы: отдельной страницей (forms/*.html) или внутри приложения группы (app/)
  function start(d, demo) {
    selectedBack = 0;
    data = d;
    SB.demoMode = demo;
    today = SB.parseISO(SB.localDate());
    var built = SB.parseISO(data.today || SB.localDate());
    shift = Math.round((today - built) / 86400000);
    marks = marksFor(0);
    render();
  }

  SB.forms = SB.forms || {};
  SB.forms.attendance = { start: start, demo: DEMO };
  if (!window.SB_HUB) SB.load(DEMO, start);
})();
