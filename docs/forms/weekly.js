/*
 * Форма «Недельный отчёт».
 * Список учеников → экран ученика: вопросы недели (4 варианта, подставлены с прошлой недели),
 * готовые фразы и комментарий до 80 букв → «Следующий».
 * Отправляются только заполненные ученики. Если не помещаются в 4096 байт — часть, остальные
 * остаются в черновике на телефоне.
 */
(function () {
  "use strict";

  var COMMENT_MAX = 80;

  var DEMO = {
    v: 1, f: "wk", gid: 1, g: "10-А", lang: "ru", wk: SB.iso(monday(new Date())),
    st: [[11, "Азиз К.", "uz"], [12, "Мадина Ю.", "ru"], [13, "Жасур А.", "uz"], [14, "Камила Р.", "ru"],
         [15, "Отабек С.", "uz"], [16, "Севара О.", "ru"]],
    q: [[1, "Домашнее задание", "не сделано", "частично", "сделано с ошибками", "сделано хорошо"],
        [2, "Работа на уроке", "пассивен", "отвечает, когда спросят", "активно участвует", "помогает другим"],
        [3, "Новые слова", "не выучены", "выучена часть", "выучено большинство", "выучены все"],
        [4, "Грамматика темы", "не понял", "понимает с подсказкой", "применяет с ошибками", "применяет уверенно"],
        [5, "Говорение", "молчит", "отдельные слова", "простые фразы", "свободно для своего уровня"],
        [7, "Дисциплина", "мешал", "отвлекался", "нормально", "образцово"]],
    ph: [["Молодец!", "Barakalla!"], ["Старается на уроке.", "Darsda harakat qiladi."],
         ["Нужно повторять слова.", "Soʻzlarni takrorlash kerak."], ["Больше читать дома.", "Uyda koʻproq oʻqish kerak."]],
    a: { "11": { "1": "322123" }, "12": { "0": "333232" }, "13": { "p": "211012" } },
    c: { "0": [12] }
  };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var data, weekShift = 0, weekIdx = 0, draft = {}, screen = -1;

  function monday(d) {
    var x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var wd = x.getDay() === 0 ? 7 : x.getDay();
    return SB.addDays(x, 1 - wd);
  }
  function weekMonday() { return SB.addDays(monday(new Date()), -7 * weekIdx); }
  function draftKey() { return (SB.demoMode ? "demo-wk:" : "wk:") + data.gid + ":" + SB.iso(weekMonday()); }
  function saveDraft() { SB.draftSet(draftKey(), draft); }

  // Ответы из ссылки для ученика: сохранённые за выбранную неделю или последние до неё
  function fromLink(sid) {
    var rec = (data.a && data.a[String(sid)]) || {};
    var own = weekIdx - weekShift;
    if (own >= 0 && rec[String(own)]) return { a: rec[String(own)], saved: true };
    for (var k = Math.max(own + 1, 0); k <= 3; k++) {
      if (rec[String(k)]) return { a: rec[String(k)], prev: true };
    }
    if (rec.p) return { a: rec.p, prev: true };
    return { a: "", prev: false };
  }

  function hasComment(sid) {
    var own = weekIdx - weekShift;
    var list = (data.c && data.c[String(own)]) || [];
    return list.indexOf(sid) >= 0;
  }

  function entry(sid) {
    if (!draft[sid]) {
      var src = fromLink(sid);
      var answers = [];
      for (var i = 0; i < data.q.length; i++) {
        var ch = src.a.charAt(i);
        answers.push(ch >= "0" && ch <= "3" ? +ch : null);
      }
      draft[sid] = { a: answers, c: "", done: false, prev: !!src.prev };
    }
    return draft[sid];
  }

  function status(sid) {
    if (draft[sid] && draft[sid].done) return "done";
    if (fromLink(sid).saved) return "saved";
    return "empty";
  }

  function doneIds() {
    return data.st.filter(function (s) { return draft[s[0]] && draft[s[0]].done; }).map(function (s) { return s[0]; });
  }

  function filledCount() {
    return data.st.filter(function (s) { return status(s[0]) !== "empty"; }).length;
  }

  function progress(k, n) {
    var wrap = el("div");
    var bar = el("div", "progress");
    var fill = el("span");
    fill.style.width = (n ? Math.round(100 * k / n) : 0) + "%";
    bar.appendChild(fill);
    wrap.appendChild(bar);
    var label = el("div", "progress-label");
    label.appendChild(el("span", "", t("filled", { k: k, n: n })));
    label.appendChild(el("span", "", (n ? Math.round(100 * k / n) : 0) + "%"));
    wrap.appendChild(label);
    return wrap;
  }

  // ---------------------------------------------------------------- список

  function renderList() {
    screen = -1;
    SB.setBack(null);
    app.innerHTML = "";
    window.scrollTo(0, 0);
    var top = el("div", "topbar");
    var title = el("div", "grow");
    title.appendChild(el("h1", "", t("weekly")));
    title.appendChild(el("span", "group-chip", "👥 " + data.g));
    if (data.part) title.appendChild(el("span", "hint", "  " + t("part", { i: data.part[0], n: data.part[1] })));
    top.appendChild(title);
    app.appendChild(top);
    if (SB.demoMode) app.appendChild(el("p", "hint", t("demo")));

    var seg = el("div", "segments");
    [0, 1].forEach(function (idx) {
      var b = el("button", "choice" + (idx === weekIdx ? " selected" : ""));
      b.type = "button";
      var inner = el("span", "grow");
      inner.appendChild(el("span", "", idx === 0 ? t("thisWeek") : t("lastWeek")));
      inner.appendChild(el("span", "sub", SB.weekRange(SB.addDays(monday(new Date()), -7 * idx))));
      b.appendChild(inner);
      b.addEventListener("click", function () {
        if (weekIdx === idx) return;
        weekIdx = idx;
        draft = SB.draftGet(draftKey()) || {};
        SB.haptic("select");
        renderList();
      });
      seg.appendChild(b);
    });
    app.appendChild(seg);

    var box = el("div");
    box.style.margin = "16px 0";
    box.appendChild(progress(filledCount(), data.st.length));
    app.appendChild(box);

    data.st.forEach(function (s, i) {
      var st = status(s[0]);
      var b = el("button", "choice");
      b.type = "button";
      b.appendChild(SB.avatar(s[1], s[0]));
      var name = el("span", "grow", s[1]);
      name.appendChild(el("span", "sub", t("card") + ": " + (s[2] || "ru").toUpperCase()));
      b.appendChild(name);
      b.appendChild(el("span", "pill " + st, st === "done" ? "✓ " + t("done") : st === "saved" ? "✓ " + t("saved") : t("empty")));
      b.addEventListener("click", function () { SB.haptic("select"); renderStudent(i); });
      app.appendChild(b);
    });

    var n = doneIds().length;
    SB.setSave(t("saveN", { n: n }), save, n > 0);
  }

  // ---------------------------------------------------------------- экран ученика

  function renderStudent(index) {
    screen = index;
    var s = data.st[index], sid = s[0], e = entry(sid);
    var cardLang = s[2] === "uz" ? 1 : 0;
    app.innerHTML = "";
    window.scrollTo(0, 0);
    SB.setSave(t("save"), save, false);
    SB.setBack(function () { saveDraft(); renderList(); });   // «← Назад» в шапке Telegram

    var top = el("div", "topbar");
    var back = el("button", "icon-btn", "←");
    back.type = "button";
    back.addEventListener("click", function () { saveDraft(); renderList(); });
    top.appendChild(back);
    var bar = el("div", "grow");
    bar.appendChild(progress(filledCount(), data.st.length));
    top.appendChild(bar);
    app.appendChild(top);

    var head = el("div", "student-head");
    head.appendChild(SB.avatar(s[1], sid));
    var nm = el("div", "grow");
    nm.appendChild(el("div", "student-name", s[1]));
    nm.appendChild(el("span", "badge", t("card") + ": " + (s[2] || "ru").toUpperCase()));
    head.appendChild(nm);
    app.appendChild(head);
    if (e.prev && !e.done) app.appendChild(el("p", "hint", "↺ " + t("fromLastWeek")));

    data.q.forEach(function (q, qi) {
      var block = el("div", "question");
      block.id = "q" + qi;
      var h = el("h3");
      h.appendChild(el("span", "num", String(qi + 1)));
      h.appendChild(document.createTextNode(q[1]));
      block.appendChild(h);
      for (var v = 3; v >= 0; v--) {
        (function (v) {
          var b = el("button", "choice" + (e.a[qi] === v ? " selected" : ""));
          b.type = "button";
          var bars = el("span", "bars v" + v);
          for (var k = 0; k < 4; k++) bars.appendChild(el("i"));
          b.appendChild(bars);
          b.appendChild(el("span", "grow", q[2 + v]));
          b.addEventListener("click", function () {
            e.a[qi] = v;
            SB.haptic("select");
            saveDraft();
            var siblings = block.querySelectorAll(".choice");
            for (var j = 0; j < siblings.length; j++) siblings[j].classList.remove("selected", "missing");
            b.classList.add("selected");
          });
          block.appendChild(b);
        })(v);
      }
      app.appendChild(block);
    });

    app.appendChild(el("h2", "", t("comment")));
    if (hasComment(sid)) app.appendChild(el("p", "hint", "💬 " + t("commentExists")));
    if (data.ph && data.ph.length) {
      var chips = el("div", "chips");
      data.ph.forEach(function (p) {
        var text = p[cardLang] || p[0];
        var c = el("button", "chip", "+ " + text);
        c.type = "button";
        c.addEventListener("click", function () {
          var next = (area.value ? area.value.replace(/\s+$/, "") + " " : "") + text;
          if (next.length > COMMENT_MAX) { SB.haptic("error"); SB.toast(t("commentHint"), true); return; }
          area.value = next;
          area.dispatchEvent(new Event("input"));
          SB.haptic("select");
        });
        chips.appendChild(c);
      });
      app.appendChild(chips);
    }
    var area = el("textarea");
    area.maxLength = COMMENT_MAX;
    area.placeholder = t("commentHint");
    area.value = e.c || "";
    var counter = el("div", "counter-line");
    var left = el("span", "", t("commentHint"));
    var count = el("span", "", area.value.length + "/" + COMMENT_MAX);
    counter.appendChild(left);
    counter.appendChild(count);
    area.addEventListener("input", function () {
      if (area.value.length > COMMENT_MAX) area.value = area.value.slice(0, COMMENT_MAX);
      e.c = area.value;
      count.textContent = area.value.length + "/" + COMMENT_MAX;
      saveDraft();
    });
    app.appendChild(area);
    app.appendChild(counter);

    var actions = el("div");
    actions.style.marginTop = "18px";
    var next = el("button", "btn", t("next") + " ➜");
    next.type = "button";
    next.addEventListener("click", function () { finishStudent(index); });
    actions.appendChild(next);
    var list = el("button", "btn ghost", t("toList"));
    list.type = "button";
    list.style.marginTop = "10px";
    list.addEventListener("click", function () { saveDraft(); renderList(); });
    actions.appendChild(list);
    app.appendChild(actions);
  }

  function finishStudent(index) {
    var e = entry(data.st[index][0]);
    var missing = -1;
    for (var i = 0; i < e.a.length; i++) if (e.a[i] === null) { missing = i; break; }
    if (missing >= 0) {
      SB.haptic("error");
      SB.toast(t("answerAll"), true);
      var block = document.getElementById("q" + missing);
      var opts = block.querySelectorAll(".choice");
      for (var j = 0; j < opts.length; j++) opts[j].classList.add("missing");
      block.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    e.done = true;
    e.c = (e.c || "").replace(/\s+/g, " ").trim();
    saveDraft();
    SB.haptic("success");
    // следующий незаполненный ученик после текущего
    for (var step = 1; step <= data.st.length; step++) {
      var k = (index + step) % data.st.length;
      if (status(data.st[k][0]) === "empty") {
        SB.toast(t("great", { k: filledCount(), n: data.st.length }));
        return renderStudent(k);
      }
    }
    renderList();
    SB.toast(t("allDone"));
  }

  // ---------------------------------------------------------------- отправка

  function payload(ids) {
    return {
      v: 1, u: SB.uuid(), t: "wk", g: data.gid, w: SB.iso(weekMonday()),
      q: data.q.map(function (q) { return q[0]; }),
      r: ids.map(function (sid) { var e = draft[sid]; return [sid, e.a.join(""), e.c || ""]; })
    };
  }

  function save() {
    var ids = doneIds();
    if (!ids.length) { SB.toast(t("nothingToSave"), true); return; }
    var fit = ids.length;
    while (fit > 0 && SB.byteSize(JSON.stringify(payload(ids.slice(0, fit)))) > SB.SEND_LIMIT) fit--;
    var go = function (count) {
      var part = ids.slice(0, count);
      var body = payload(part);
      if (count === ids.length) {
        SB.draftClear(draftKey());
      } else {
        part.forEach(function (sid) { delete draft[sid]; });
        saveDraft();
      }
      SB.haptic("success");
      SB.send(body);
    };
    if (fit === ids.length) return go(fit);
    SB.confirm(t("tooBig", { k: fit, n: ids.length }), function (ok) { if (ok) go(fit); });
  }

  // Запуск формы: отдельной страницей (forms/*.html) или внутри приложения группы (app/)
  function start(d, demo) {
    weekIdx = 0;
    screen = -1;
    data = d;
    SB.demoMode = demo;
    var built = SB.parseISO(data.wk || SB.iso(monday(new Date())));
    weekShift = Math.round((monday(new Date()) - built) / (7 * 86400000));
    draft = SB.draftGet(draftKey()) || {};
    renderList();
  }

  SB.forms = SB.forms || {};
  SB.forms.weekly = { start: start, demo: DEMO };
  if (!window.SB_HUB) SB.load(DEMO, start);
})();
