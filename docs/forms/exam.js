/*
 * Форма «Экзамен».
 * Станции с экзаменом: балл от 0 до максимума, сразу видно «переходит» или «повтор»;
 * учитель может изменить решение, указав причину.
 * Станции без экзамена (Roundup и др.): учитель отмечает, кто переходит дальше.
 * После B2 — выбор пути: CEFR или IELTS.
 */
(function () {
  "use strict";

  var DEMO = {
    v: 1, f: "ex", gid: 1, g: "10-А", lang: "ru", s: 6, sn: "Курс A1", nx: "Курс A2", fork: false,
    mode: "score", pass: 60, max: 100,
    st: [[11, "Азиз К.", 1], [12, "Мадина Ю.", 1], [13, "Жасур А.", 1], [14, "Камила Р.", 0]],
    prev: { "12": [48, 0] }
  };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var data, rows = {};

  function auto(r) { return r.score !== null && r.score >= data.pass ? 1 : 0; }
  function decision(r) { return r.override !== null ? r.override : (data.mode === "score" ? auto(r) : r.choice); }
  function ready(r) { return data.mode === "score" ? r.score !== null : r.choice !== null; }

  function render() {
    app.innerHTML = "";
    var top = el("div", "topbar");
    var title = el("div", "grow");
    title.appendChild(el("h1", "", data.mode === "score" ? t("exam") : t("decision")));
    title.appendChild(el("span", "group-chip", "👥 " + data.g));
    top.appendChild(title);
    app.appendChild(top);
    if (SB.demoMode) app.appendChild(el("p", "hint", t("demo")));

    var info = el("div", "card soft");
    info.appendChild(el("div", "", data.sn + "  ➜  " + (data.nx || (data.fork ? "CEFR / IELTS" : t("endOfRoute")))));
    if (data.mode === "score" && data.pass !== null && data.max !== null) {
      info.appendChild(el("div", "hint", t("passScore", { p: data.pass, m: data.max })));
    }
    info.appendChild(el("div", "hint", data.mode === "score" ? t("scoreHint") : t("teacherHint")));
    app.appendChild(info);

    if (data.mode === "score" && (data.pass === null || data.max === null)) {
      app.appendChild(el("div", "error-box", t("scoresUnset")));
      SB.setSave(t("save"), function () {}, false);
      return;
    }

    data.st.forEach(function (s) {
      var r = rows[s[0]];
      var box = el("div", "card");
      var head = el("div", "topbar");
      head.style.marginBottom = "8px";
      head.appendChild(SB.avatar(s[1], s[0]));
      head.appendChild(el("span", "grow", s[1]));
      box.appendChild(head);
      if (!s[2]) {
        box.style.opacity = "0.55";
        box.appendChild(el("div", "hint", t("otherStage")));
        app.appendChild(box);
        return;
      }

      if (data.mode === "score") {
        var line = el("div", "topbar");
        line.style.marginBottom = "0";
        var input = el("input");
        input.type = "text";
        input.inputMode = "decimal";
        input.placeholder = "0–" + data.max;
        input.style.width = "120px";
        input.style.textAlign = "center";
        input.style.fontSize = "22px";
        input.style.fontWeight = "900";
        if (r.score !== null) input.value = String(r.score);
        var pill = el("span");
        var paint = function () {
          var d = decision(r);
          pill.className = "pill " + (r.score === null ? "empty" : d ? "present" : "late");
          pill.textContent = r.score === null ? "—" : (r.override !== null ? "✎ " : "") + (d ? t("moves") : t("repeat"));
        };
        input.addEventListener("input", function () {
          var v = input.value.replace(",", ".").trim();
          var n = v === "" ? null : Number(v);
          if (n !== null && (isNaN(n) || n < 0 || n > data.max)) { input.classList.add("missing"); n = null; }
          else input.classList.remove("missing");
          r.score = n;
          paint();
          counter();
        });
        line.appendChild(input);
        line.appendChild(el("span", "hint grow", "/ " + data.max));
        line.appendChild(pill);
        paint();
        box.appendChild(line);

        var change = el("button", "btn ghost small", t("changeDecision"));
        change.type = "button";
        change.style.marginTop = "10px";
        change.addEventListener("click", function () {
          if (r.score === null) { SB.toast(t("scoreHint"), true); return; }
          r.override = r.override === null ? 1 - auto(r) : null;
          if (r.override === null) r.reason = "";
          SB.haptic("select");
          render();
        });
        box.appendChild(change);
        if (r.override !== null) {
          var reason = el("input");
          reason.type = "text";
          reason.maxLength = 100;
          reason.placeholder = t("reasonPh");
          reason.value = r.reason;
          reason.style.marginTop = "10px";
          reason.addEventListener("input", function () { r.reason = reason.value; });
          box.appendChild(el("div", "hint", t("reason")));
          box.appendChild(reason);
        }
      } else {
        var seg = el("div", "segments");
        [[1, t("moves")], [0, t("stays")]].forEach(function (opt) {
          var b = el("button", "choice" + (r.choice === opt[0] ? " selected" : ""), opt[1]);
          b.type = "button";
          b.addEventListener("click", function () { r.choice = opt[0]; SB.haptic("select"); render(); });
          seg.appendChild(b);
        });
        box.appendChild(seg);
      }

      if (data.fork && ready(r) && decision(r) === 1) {
        box.appendChild(el("div", "hint", t("path")));
        var paths = el("div", "segments");
        [["cefr", "CEFR"], ["ielts", "IELTS"], ["", t("later")]].forEach(function (opt) {
          var b = el("button", "choice" + (r.path === opt[0] ? " selected" : ""), opt[1]);
          b.type = "button";
          b.addEventListener("click", function () { r.path = opt[0]; SB.haptic("select"); render(); });
          paths.appendChild(b);
        });
        box.appendChild(paths);
      }
      app.appendChild(box);
    });
    counter();
  }

  function chosen() {
    return data.st.filter(function (s) { return s[2] && ready(rows[s[0]]); });
  }

  function counter() {
    var n = chosen().length;
    SB.setSave(t("saveN", { n: n }), save, n > 0);
  }

  function save() {
    var list = chosen();
    if (!list.length) { SB.toast(t("enterScores"), true); return; }
    for (var i = 0; i < list.length; i++) {
      var r = rows[list[i][0]];
      if (r.override !== null && r.reason.replace(/\s+/g, "").length < 3) {
        SB.haptic("error");
        SB.toast(t("needReason"), true);
        return;
      }
    }
    var payload = {
      v: 1, u: SB.uuid(), t: "ex", g: data.gid, s: data.s,
      r: list.map(function (s) {
        var r = rows[s[0]];
        return [s[0], data.mode === "score" ? r.score : null, decision(r),
                r.override !== null ? r.reason.replace(/\s+/g, " ").trim() : "", data.fork ? r.path : ""];
      })
    };
    SB.haptic("success");
    SB.send(payload);
  }

  // Запуск формы: отдельной страницей (forms/*.html) или внутри приложения группы (app/)
  function start(d, demo) {
    rows = {};
    data = d;
    SB.demoMode = demo;
    data.st.forEach(function (s) {
      var prev = (data.prev || {})[String(s[0])];
      var r = { score: null, choice: null, override: null, reason: "", path: "" };
      if (prev && data.mode === "score") {
        r.score = prev[0];
        if ((prev[0] >= data.pass ? 1 : 0) !== prev[1]) r.override = prev[1];
      }
      rows[s[0]] = r;
    });
    render();
  }

  SB.forms = SB.forms || {};
  SB.forms.exam = { start: start, demo: DEMO };
  if (!window.SB_HUB) SB.load(DEMO, start);
})();
