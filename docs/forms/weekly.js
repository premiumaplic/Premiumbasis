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
        [8, "Аудирование", "не понимает на слух", "понимает отдельные слова", "понимает основное", "понимает почти всё", 1],
        [7, "Дисциплина", "мешал", "отвлекался", "нормально", "образцово"]],
    ph: [["Молодец!", "Barakalla!"], ["Старается на уроке.", "Darsda harakat qiladi."],
         ["Нужно повторять слова.", "Soʻzlarni takrorlash kerak."], ["Больше читать дома.", "Uyda koʻproq oʻqish kerak."]],
    a: { "11": { "1": "32212x3" }, "12": { "0": "3332323" }, "13": { "p": "21101x2" } },
    c: { "0": [12] }, sr: { "0": [12] }
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

  // Черновик с телефона: берём только записи под нынешний список вопросов
  // (после смены вопросов старый черновик иначе отправил бы испорченные ответы)
  function loadDraft() {
    var saved = SB.draftGet(draftKey()) || {}, out = {};
    Object.keys(saved).forEach(function (sid) {
      var e = saved[sid];
      if (!e || !e.a || e.a.length !== data.q.length) return;
      var ok = e.a.every(function (v) { return v === null || (typeof v === "number" && v >= 0 && v <= 3); });
      if (ok) out[sid] = e;
    });
    return out;
  }

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
      draft[sid] = { a: answers, c: "", done: false, prev: !!src.prev, s: isStar(sid) };
    }
    return draft[sid];
  }

  function isStar(sid) {
    var own = weekIdx - weekShift;
    return ((data.sr && data.sr[String(own)]) || []).indexOf(sid) >= 0;
  }
  function optional(qi) { return !!data.q[qi][6]; }

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
        draft = loadDraft();
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

    var LV = [t("lv0"), t("lv1"), t("lv2"), t("lv3")];
    data.q.forEach(function (q, qi) {
      var block = el("div", "qcard" + (e.a[qi] !== null || optional(qi) ? " answered" : ""));
      block.id = "q" + qi;
      var h = el("div", "qhead");
      h.appendChild(el("span", "num", String(qi + 1)));
      h.appendChild(el("b", "", q[1]));
      if (optional(qi)) h.appendChild(el("span", "opt-tag", t("optional")));
      block.appendChild(h);
      var row = el("div", "levels" + (optional(qi) ? " with-skip" : ""));
      var text = el("div", "answer-text");
      var paint = function () {
        var v = e.a[qi];
        var buttons = row.querySelectorAll(".lv");
        for (var j = 0; j < buttons.length; j++) {
          var bv = buttons[j].getAttribute("data-v");
          buttons[j].classList.toggle("sel", bv === "x" ? v === null && optional(qi) : +bv === v && v !== null);
        }
        text.textContent = v === null ? (optional(qi) ? "— " + t("notRated") : t("pickLevel")) : q[2 + v];
        text.className = "answer-text" + (v === null ? " empty" : "");
        block.classList.toggle("answered", v !== null || optional(qi));
      };
      for (var v = 0; v <= 3; v++) {
        (function (v) {
          var b = el("button", "lv l" + v);
          b.type = "button";
          b.setAttribute("data-v", String(v));
          var bars = el("span", "bars v" + v);
          for (var k = 0; k < 4; k++) bars.appendChild(el("i"));
          b.appendChild(bars);
          b.appendChild(el("small", "", LV[v]));
          b.addEventListener("click", function () {
            e.a[qi] = v;
            SB.haptic("select");
            block.classList.remove("missing");
            saveDraft();
            paint();
          });
          row.appendChild(b);
        })(v);
      }
      if (optional(qi)) {
        var skip = el("button", "lv skip", "—");
        skip.type = "button";
        skip.setAttribute("data-v", "x");
        skip.title = t("notRated");
        skip.addEventListener("click", function () { e.a[qi] = null; SB.haptic("select"); saveDraft(); paint(); });
        row.appendChild(skip);
      }
      block.appendChild(row);
      block.appendChild(text);
      paint();
      app.appendChild(block);
    });

    var star = el("button", "star-toggle" + (e.s ? " on" : ""));
    star.type = "button";
    star.appendChild(el("span", "s", "⭐"));
    var stx = el("span", "grow");
    stx.appendChild(document.createTextNode(t("starWeek")));
    stx.appendChild(el("small", "", t("starHint")));
    star.appendChild(stx);
    star.addEventListener("click", function () {
      e.s = !e.s;
      star.classList.toggle("on", e.s);
      SB.haptic(e.s ? "success" : "select");
      saveDraft();
    });
    app.appendChild(star);

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
    for (var i = 0; i < e.a.length; i++) if (e.a[i] === null && !optional(i)) { missing = i; break; }
    if (missing >= 0) {
      SB.haptic("error");
      SB.toast(t("answerAll"), true);
      var block = document.getElementById("q" + missing);
      block.classList.remove("missing");
      void block.offsetWidth;            // перезапуск анимации «потрясти»
      block.classList.add("missing");
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
    if (SB.confetti) SB.confetti();
  }

  // ---------------------------------------------------------------- отправка

  function payload(ids) {
    return {
      v: 1, u: SB.uuid(), t: "wk", g: data.gid, w: SB.iso(weekMonday()),
      q: data.q.map(function (q) { return q[0]; }),
      // ответы: 0–3, «-» — необязательный вопрос не оценивался; последний элемент — звезда недели
      r: ids.map(function (sid) {
        var e = draft[sid];
        return [sid, e.a.map(function (v) { return v === null ? "-" : String(v); }).join(""), e.c || "", e.s ? 1 : 0];
      })
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
  // opts.sid — сразу открыть этого ученика (из профиля в приложении группы)
  function start(d, demo, opts) {
    weekIdx = 0;
    screen = -1;
    data = d;
    SB.demoMode = demo;
    var built = SB.parseISO(data.wk || SB.iso(monday(new Date())));
    weekShift = Math.round((monday(new Date()) - built) / (7 * 86400000));
    draft = loadDraft();
    var idx = opts && opts.sid ? data.st.map(function (s) { return s[0]; }).indexOf(opts.sid) : -1;
    if (idx >= 0) renderStudent(idx); else renderList();
  }

  SB.forms = SB.forms || {};
  SB.forms.weekly = { start: start, demo: DEMO };
  if (!window.SB_HUB) SB.load(DEMO, start);
})();
