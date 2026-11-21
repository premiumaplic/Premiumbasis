/*
 * Форма «Недельный отчёт».
 *
 * 1. Настройки перед отчётом: неделя (эта / прошлая), способ заполнения (по ученикам или по навыкам —
 *    один навык сразу для всего класса), какие навыки оценивались на этой неделе, с чего начать
 *    (как на прошлой неделе / с чистого листа / всем «хорошо»), кого заполнять (всех / без отчёта / выбрать).
 * 2. Заполнение: уровень одним нажатием (4 ступени), необязательный навык можно пропустить «—».
 * 3. Для каждого ученика: ⭐ звезда недели, цель на следующую неделю, готовые фразы и комментарий до 80 букв.
 * Отправляются только заполненные ученики. Если не помещаются в 4096 байт — часть, остальные
 * остаются в черновике на телефоне. Черновик и настройки хранятся на телефоне.
 */
(function () {
  "use strict";

  var COMMENT_MAX = 80;

  SB.addTexts({
    ru: {
      wkSetup: "Настройки отчёта", wkStepWeek: "Неделя", wkStepMode: "Как заполнять", wkStepSkills: "Что оценивали",
      wkStepStart: "С чего начать", wkStepWho: "Кого заполнять",
      wkModeStudent: "По ученикам", wkModeStudentD: "Каждый ученик отдельно: навыки, звезда, цель, комментарий",
      wkModeSkill: "По навыкам", wkModeSkillD: "Один навык — сразу весь класс. Быстрее для большой группы",
      wkSkillsHint: "Выключенные навыки на этой неделе не оцениваются и не попадут на карточку",
      wkRequired: "обязательный",
      wkStartPrev: "Как на прошлой неделе", wkStartPrevD: "Подставить прошлые ответы и поправить изменения",
      wkStartEmpty: "С чистого листа", wkStartEmptyD: "Все ответы пустые — выбрать заново",
      wkStartGood: "Всем «хорошо»", wkStartGoodD: "Быстро отметить и поправить только отличия",
      wkWhoAll: "Всех · {n}", wkWhoMissing: "Без отчёта · {n}", wkWhoPick: "Выбрать",
      wkBegin: "Начать · {n} {w}", wkNobody: "Выберите хотя бы одного ученика",
      wkDraft: "Есть черновик: заполнено {k}", wkDraftD: "Можно продолжить с того же места", wkContinue: "Продолжить",
      wkFilledWeek: "заполнено {k} из {n}", wkSettings: "Настройки",
      wkSkillOf: "Навык {i} из {n}", wkAll: "Всем:", wkNextSkill: "Дальше", wkPrevSkill: "Назад",
      wkToSummary: "К итогам", wkNotAll: "Отметьте уровень у всех учеников",
      wkSummary: "Итоги отчёта", wkSummaryHint: "Нажмите на ученика, чтобы добавить звезду, цель и комментарий",
      wkExtras: "Звезда, цель и комментарий", wkGoal: "Цель на следующую неделю", wkGoalHint: "видна родителю",
      wkNoGoal: "Без цели", wkLevel: "уровень", wkPrevStudent: "Предыдущий", wkStudentOf: "{i} из {n}",
      wkStar: "★", wkGoalShort: "цель", wkCommentShort: "комментарий", wkReady: "готов", wkNotReady: "не всё отмечено",
      stu1: "ученик", stu2: "ученика", stu5: "учеников"
    },
    uz: {
      wkSetup: "Hisobot sozlamalari", wkStepWeek: "Hafta", wkStepMode: "Qanday toʻldirish", wkStepSkills: "Nima baholandi",
      wkStepStart: "Nimadan boshlash", wkStepWho: "Kimni toʻldirish",
      wkModeStudent: "Oʻquvchilar boʻyicha", wkModeStudentD: "Har bir oʻquvchi alohida: koʻnikmalar, yulduz, maqsad, izoh",
      wkModeSkill: "Koʻnikmalar boʻyicha", wkModeSkillD: "Bitta koʻnikma — butun sinf uchun. Katta guruhda tezroq",
      wkSkillsHint: "Oʻchirilgan koʻnikmalar bu hafta baholanmaydi va kartaga chiqmaydi",
      wkRequired: "majburiy",
      wkStartPrev: "Oʻtgan haftadagidek", wkStartPrevD: "Oʻtgan javoblarni qoʻyib, oʻzgarganini tuzatish",
      wkStartEmpty: "Toza varaqdan", wkStartEmptyD: "Barcha javoblar boʻsh",
      wkStartGood: "Hammaga «yaxshi»", wkStartGoodD: "Tez belgilab, faqat farqlarini tuzatish",
      wkWhoAll: "Hammasi · {n}", wkWhoMissing: "Hisobotsiz · {n}", wkWhoPick: "Tanlash",
      wkBegin: "Boshlash · {n} {w}", wkNobody: "Kamida bitta oʻquvchini tanlang",
      wkDraft: "Qoralama bor: {k} ta toʻldirilgan", wkDraftD: "Shu joydan davom ettirish mumkin", wkContinue: "Davom etish",
      wkFilledWeek: "{n} tadan {k} toʻldirildi", wkSettings: "Sozlamalar",
      wkSkillOf: "{n} tadan {i}-koʻnikma", wkAll: "Hammaga:", wkNextSkill: "Keyingi", wkPrevSkill: "Orqaga",
      wkToSummary: "Natijalarga", wkNotAll: "Barcha oʻquvchilarga daraja qoʻying",
      wkSummary: "Hisobot natijalari", wkSummaryHint: "Yulduz, maqsad va izoh qoʻshish uchun oʻquvchini bosing",
      wkExtras: "Yulduz, maqsad va izoh", wkGoal: "Keyingi hafta maqsadi", wkGoalHint: "ota-onaga koʻrinadi",
      wkNoGoal: "Maqsadsiz", wkLevel: "daraja", wkPrevStudent: "Oldingi", wkStudentOf: "{n} tadan {i}",
      wkStar: "★", wkGoalShort: "maqsad", wkCommentShort: "izoh", wkReady: "tayyor", wkNotReady: "hammasi belgilanmagan",
      stu1: "oʻquvchi", stu2: "oʻquvchi", stu5: "oʻquvchi"
    }
  });

  function demoMonday(back) {
    var d = new Date(), wd = (d.getDay() + 6) % 7;
    return SB.iso(SB.addDays(d, -wd - 7 * (back || 0)));
  }
  var DEMO = {
    v: 1, f: "wk", gid: 1, g: "10-А", lang: "ru", wk: demoMonday(0),
    st: [[11, "Азиз К.", "uz"], [12, "Мадина Ю.", "ru"], [13, "Жасур А.", "uz"], [14, "Камила Р.", "ru"],
         [15, "Отабек С.", "uz"], [16, "Севара О.", "ru"]],
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
    a: { "11": { "1": "32212xxx3" }, "12": { "0": "333232333" }, "13": { "p": "21101xxx2" } },
    c: { "0": [12] }, sr: { "0": [12] },
    gl: [[1, "Делать домашнее задание вовремя"], [2, "Быть активнее на уроке"], [4, "Учить по 10 новых слов в день"],
         [5, "Читать по 15 минут в день"], [8, "Больше говорить на уроке"]],
    go: { "0": [[12, 5]] }
  };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var data, weekShift = 0, weekIdx = 0, draft = {}, setup = null, targets = [];

  // ---------------------------------------------------------------- даты, черновик, настройки

  function monday(d) {
    var x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var wd = x.getDay() === 0 ? 7 : x.getDay();
    return SB.addDays(x, 1 - wd);
  }
  function weekMonday(idx) { return SB.addDays(monday(new Date()), -7 * (idx === undefined ? weekIdx : idx)); }
  function own(idx) { return (idx === undefined ? weekIdx : idx) - weekShift; }   // номер недели в данных ссылки
  function draftKey(idx) { return (SB.demoMode ? "demo-wk:" : "wk:") + data.gid + ":" + SB.iso(weekMonday(idx)); }
  function setupKey() { return (SB.demoMode ? "demo-wkset:" : "wkset:") + data.gid; }
  function saveDraft() { SB.draftSet(draftKey(), draft); }
  function saveSetup() { SB.draftSet(setupKey(), { mode: setup.mode, skills: setup.skills, start: setup.start }); }

  // Черновик с телефона: берём только записи под нынешний список вопросов
  // (после смены вопросов старый черновик иначе отправил бы испорченные ответы)
  function loadDraft(idx) {
    var saved = SB.draftGet(draftKey(idx)) || {}, out = {};
    Object.keys(saved).forEach(function (sid) {
      var e = saved[sid];
      if (!e || !e.a || e.a.length !== data.q.length) return;
      var ok = e.a.every(function (v) { return v === null || (typeof v === "number" && v >= 0 && v <= 3); });
      if (ok) out[sid] = e;
    });
    return out;
  }

  function loadSetup() {
    var s = SB.draftGet(setupKey()) || {};
    var skills = {};
    data.q.forEach(function (q, i) { skills[i] = !optional(i) || !s.skills || s.skills[i] !== false; });
    return { mode: s.mode === "skill" ? "skill" : "student", skills: skills,
             start: ["prev", "empty", "good"].indexOf(s.start) >= 0 ? s.start : "prev", who: "all", picked: {} };
  }

  function optional(qi) { return !!data.q[qi][6]; }
  function enabled(qi) { return !optional(qi) || setup.skills[qi] !== false; }
  function enabledQs() { return data.q.map(function (q, i) { return i; }).filter(enabled); }
  function student(sid) { return data.st.filter(function (s) { return s[0] === sid; })[0]; }
  function words(n) { return SB.plural(n, [t("stu1"), t("stu2"), t("stu5")]); }

  // ---------------------------------------------------------------- ответы из ссылки

  function fromLink(sid, idx) {
    var rec = (data.a && data.a[String(sid)]) || {};
    var o = own(idx);
    if (o >= 0 && rec[String(o)]) return { a: rec[String(o)], saved: true };
    for (var k = Math.max(o + 1, 0); k <= 3; k++) if (rec[String(k)]) return { a: rec[String(k)], prev: true };
    if (rec.p) return { a: rec.p, prev: true };
    return { a: "", prev: false };
  }
  function savedFlag(map, sid) { return ((map && map[String(own())]) || []).indexOf(sid) >= 0; }
  function savedGoal(sid) {
    var list = (data.go && data.go[String(own())]) || [];
    for (var i = 0; i < list.length; i++) if (list[i][0] === sid) return list[i][1];
    return 0;
  }

  function freshEntry(sid) {
    var src = fromLink(sid), answers = [];
    for (var i = 0; i < data.q.length; i++) {
      var v = null;
      if (enabled(i)) {
        if (setup.start === "good") v = 2;
        else if (setup.start === "prev" || src.saved) {
          var ch = src.a.charAt(i);
          v = ch >= "0" && ch <= "3" ? +ch : null;
        }
      }
      answers.push(v);
    }
    return { a: answers, c: "", done: false, prev: !!src.prev && setup.start === "prev",
             s: savedFlag(data.sr, sid), g: savedGoal(sid) };
  }
  function entry(sid) {
    if (!draft[sid]) draft[sid] = freshEntry(sid);
    return draft[sid];
  }
  function complete(e) {
    for (var i = 0; i < data.q.length; i++) if (enabled(i) && !optional(i) && e.a[i] === null) return false;
    return true;
  }
  function status(sid) {
    if (draft[sid] && draft[sid].done) return "done";
    if (fromLink(sid).saved) return "saved";
    return "empty";
  }
  function filledCount(list) {
    return (list || data.st).filter(function (s) { return status(s[0]) !== "empty"; }).length;
  }
  function doneIds() {
    return data.st.filter(function (s) { return draft[s[0]] && draft[s[0]].done; }).map(function (s) { return s[0]; });
  }
  function avgLevel(e) {
    var vals = e.a.filter(function (v) { return v !== null; });
    return vals.length ? Math.round(vals.reduce(function (a, b) { return a + b; }, 0) / vals.length / 3 * 100) : null;
  }

  // ---------------------------------------------------------------- общие части

  function clear() { app.innerHTML = ""; window.scrollTo(0, 0); }

  function progressBar(k, n) {
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

  function stepTitle(n, title, note) {
    var h = el("div", "step-title");
    h.appendChild(el("span", "n", String(n)));
    h.appendChild(el("b", "", title));
    if (note) h.appendChild(el("small", "", note));
    return h;
  }

  function optCard(icon, title, desc, on, onClick) {
    var b = el("button", "opt-card" + (on ? " on" : ""));
    b.type = "button";
    var ic = el("span", "oc-ic");
    ic.appendChild(SB.icon(icon));
    b.appendChild(ic);
    b.appendChild(el("b", "", title));
    if (desc) b.appendChild(el("span", "d", desc));
    b.appendChild(el("span", "radio"));
    b.addEventListener("click", function () { SB.haptic("select"); onClick(); });
    return b;
  }

  function topbar(title, onBack) {
    var top = el("div", "topbar");
    if (onBack) {
      var back = el("button", "icon-btn");
      back.type = "button";
      back.appendChild(SB.icon("back"));
      back.addEventListener("click", onBack);
      top.appendChild(back);
    }
    var tt = el("div", "grow");
    tt.appendChild(el("h1", "", title));
    var chip = el("span", "group-chip", data.g + " · " + SB.weekRange(weekMonday()));
    tt.appendChild(chip);
    if (data.part) tt.appendChild(el("span", "hint", "  " + t("part", { i: data.part[0], n: data.part[1] })));
    top.appendChild(tt);
    app.appendChild(top);
  }

  // ---------------------------------------------------------------- 1. настройки

  function renderSetup() {
    clear();
    SB.setBack(null);
    var hero = el("div", "wk-hero");
    hero.appendChild(el("h1", "", t("weekly")));
    hero.appendChild(el("span", "group-chip", data.g));
    if (data.part) hero.appendChild(el("span", "hint", "  " + t("part", { i: data.part[0], n: data.part[1] })));
    var k = filledCount(), n = data.st.length;
    var pw = el("div");
    pw.style.marginTop = "12px";
    pw.appendChild(progressBar(k, n));
    hero.appendChild(pw);
    app.appendChild(hero);
    if (SB.demoMode) app.appendChild(el("p", "hint", t("demo")));

    var inDraft = Object.keys(draft).filter(function (sid) { return draft[sid].done; }).length;
    if (inDraft) {
      var ban = el("div", "draft-banner");
      ban.appendChild(SB.icon("pen"));
      var bt = el("span", "grow");
      bt.appendChild(el("b", "", t("wkDraft", { k: inDraft })));
      bt.appendChild(el("small", "", t("wkDraftD")));
      ban.appendChild(bt);
      var go = el("button", "btn", t("wkContinue"));
      go.type = "button";
      go.addEventListener("click", function () { begin(true); });
      ban.appendChild(go);
      app.appendChild(ban);
    }

    // 1. неделя
    app.appendChild(stepTitle(1, t("wkStepWeek")));
    var weeks = el("div", "opt-cards");
    [0, 1].forEach(function (idx) {
      var dr = loadDraft(idx);
      var cnt = data.st.filter(function (s) { return (dr[s[0]] && dr[s[0]].done) || fromLink(s[0], idx).saved; }).length;
      weeks.appendChild(optCard("calendar", idx === 0 ? t("thisWeek") : t("lastWeek"),
        SB.weekRange(weekMonday(idx)) + " · " + t("wkFilledWeek", { k: cnt, n: data.st.length }), weekIdx === idx, function () {
          if (weekIdx === idx) return;
          weekIdx = idx;
          draft = loadDraft();
          renderSetup();
        }));
    });
    app.appendChild(weeks);

    // 2. способ
    app.appendChild(stepTitle(2, t("wkStepMode")));
    var modes = el("div", "opt-cards");
    modes.appendChild(optCard("user", t("wkModeStudent"), t("wkModeStudentD"), setup.mode === "student",
                              function () { setup.mode = "student"; saveSetup(); renderSetup(); }));
    modes.appendChild(optCard("grid", t("wkModeSkill"), t("wkModeSkillD"), setup.mode === "skill",
                              function () { setup.mode = "skill"; saveSetup(); renderSetup(); }));
    app.appendChild(modes);

    // 3. навыки недели
    var on = enabledQs().length;
    app.appendChild(stepTitle(3, t("wkStepSkills"), on + " / " + data.q.length));
    var chips = el("div", "tchips");
    data.q.forEach(function (q, i) {
      var c = el("button", "tchip" + (enabled(i) ? " on" : "") + (optional(i) ? "" : " locked"));
      c.type = "button";
      if (enabled(i)) c.appendChild(SB.icon("check"));
      c.appendChild(document.createTextNode(q[1]));
      if (optional(i)) {
        c.addEventListener("click", function () {
          setup.skills[i] = !enabled(i);
          SB.haptic("select");
          saveSetup();
          renderSetup();
        });
      } else {
        c.title = t("wkRequired");
      }
      chips.appendChild(c);
    });
    app.appendChild(chips);
    app.appendChild(el("p", "hint", t("wkSkillsHint")));

    // 4. начальные значения
    app.appendChild(stepTitle(4, t("wkStepStart")));
    var starts = el("div", "opt-cards one");
    [["prev", "repeat", t("wkStartPrev"), t("wkStartPrevD")], ["empty", "empty", t("wkStartEmpty"), t("wkStartEmptyD")],
     ["good", "thumb", t("wkStartGood"), t("wkStartGoodD")]].forEach(function (o) {
      starts.appendChild(optCard(o[1], o[2], o[3], setup.start === o[0],
                                 function () { setup.start = o[0]; saveSetup(); renderSetup(); }));
    });
    app.appendChild(starts);

    // 5. кого заполнять
    var missing = data.st.filter(function (s) { return status(s[0]) === "empty"; });
    app.appendChild(stepTitle(5, t("wkStepWho")));
    var seg = el("div", "seg");
    [["all", t("wkWhoAll", { n: data.st.length })], ["missing", t("wkWhoMissing", { n: missing.length })],
     ["pick", t("wkWhoPick")]].forEach(function (w) {
      var b = el("button", setup.who === w[0] ? "on" : "", w[1]);
      b.type = "button";
      b.addEventListener("click", function () { setup.who = w[0]; SB.haptic("select"); renderSetup(); });
      seg.appendChild(b);
    });
    app.appendChild(seg);
    if (setup.who === "pick") {
      var list = el("div", "pick-list");
      list.style.marginTop = "10px";
      data.st.forEach(function (s) {
        var b = el("button", "choice" + (setup.picked[s[0]] ? " selected" : ""));
        b.type = "button";
        b.appendChild(SB.avatar(s[1], s[0]));
        var tx = el("span", "grow", s[1]);
        var st = status(s[0]);
        tx.appendChild(el("span", "sub", st === "empty" ? t("empty") : st === "saved" ? t("saved") : t("done")));
        b.appendChild(tx);
        var mk = el("span", "mark");
        if (setup.picked[s[0]]) mk.appendChild(SB.icon("check"));
        b.appendChild(mk);
        b.addEventListener("click", function () {
          setup.picked[s[0]] = !setup.picked[s[0]];
          SB.haptic("select");
          renderSetup();
        });
        list.appendChild(b);
      });
      app.appendChild(list);
    }

    targets = chosen();
    SB.setSave(t("wkBegin", { n: targets.length, w: words(targets.length) }), function () {
      if (!targets.length) { SB.haptic("error"); SB.toast(t("wkNobody"), true); return; }
      begin(false);
    }, true);
  }

  function chosen() {
    return data.st.filter(function (s) {
      if (setup.who === "missing") return status(s[0]) === "empty";
      if (setup.who === "pick") return !!setup.picked[s[0]];
      return true;
    });
  }

  // Начать (или продолжить черновик): ответы готовятся по настройкам
  function begin(fromDraft) {
    targets = fromDraft ? data.st.filter(function (s) { return draft[s[0]]; }) : chosen();
    if (!targets.length) targets = data.st.slice();
    targets.forEach(function (s) {
      var e = draft[s[0]];
      if (!fromDraft && e && !e.done) e = draft[s[0]] = freshEntry(s[0]);
      e = entry(s[0]);
      for (var i = 0; i < data.q.length; i++) if (!enabled(i)) e.a[i] = null;   // навык не оценивался
    });
    saveDraft();
    SB.haptic("success");
    if (setup.mode === "skill") renderSkill(0); else renderList();
  }

  // ---------------------------------------------------------------- 2а. по ученикам: список

  function renderList() {
    clear();
    SB.setBack(function () { saveDraft(); renderSetup(); });
    topbar(t("weekly"), function () { saveDraft(); renderSetup(); });
    var box = el("div");
    box.style.margin = "4px 0 14px";
    box.appendChild(progressBar(filledCount(targets), targets.length));
    app.appendChild(box);
    targets.forEach(function (s, i) {
      var st = status(s[0]);
      var b = el("button", "choice");
      b.type = "button";
      b.appendChild(SB.avatar(s[1], s[0]));
      var name = el("span", "grow", s[1]);
      var e = draft[s[0]];
      var extra = [t("card") + ": " + (s[2] || "ru").toUpperCase()];
      if (e && e.s) extra.push("★");
      if (e && e.g) extra.push(t("wkGoalShort"));
      name.appendChild(el("span", "sub", extra.join(" · ")));
      b.appendChild(name);
      b.appendChild(el("span", "pill " + st, st === "done" ? t("done") : st === "saved" ? t("saved") : t("empty")));
      b.addEventListener("click", function () { SB.haptic("select"); renderStudent(i); });
      app.appendChild(b);
    });
    var n = doneIds().length;
    SB.setSave(t("saveN", { n: n }), save, n > 0);
  }

  // ---------------------------------------------------------------- 2а. по ученикам: экран ученика

  function levelRow(e, qi, onChange) {
    var q = data.q[qi];
    var block = el("div", "qcard" + (e.a[qi] !== null || optional(qi) ? " answered" : ""));
    block.id = "q" + qi;
    var h = el("div", "qhead");
    h.appendChild(el("span", "num", String(enabledQs().indexOf(qi) + 1)));
    h.appendChild(el("b", "", q[1]));
    if (optional(qi)) h.appendChild(el("span", "opt-tag", t("optional")));
    block.appendChild(h);
    var row = el("div", "levels" + (optional(qi) ? " with-skip" : ""));
    var text = el("div", "answer-text");
    var LV = [t("lv0"), t("lv1"), t("lv2"), t("lv3")];
    var paint = function () {
      var v = e.a[qi];
      var buttons = row.querySelectorAll(".lv");
      for (var j = 0; j < buttons.length; j++) {
        var bv = buttons[j].getAttribute("data-v");
        buttons[j].classList.toggle("sel", bv === "x" ? v === null && optional(qi) : v !== null && +bv === v);
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
          paint();
          onChange();
        });
        row.appendChild(b);
      })(v);
    }
    if (optional(qi)) {
      var skip = el("button", "lv skip", "—");
      skip.type = "button";
      skip.setAttribute("data-v", "x");
      skip.title = t("notRated");
      skip.addEventListener("click", function () { e.a[qi] = null; SB.haptic("select"); paint(); onChange(); });
      row.appendChild(skip);
    }
    block.appendChild(row);
    block.appendChild(text);
    paint();
    return block;
  }

  // звезда, цель, фразы, комментарий — общие для обоих способов
  function extras(s, e) {
    var wrap = el("div");
    var cardLang = s[2] === "uz" ? 1 : 0;

    var star = el("button", "star-toggle" + (e.s ? " on" : ""));
    star.type = "button";
    var si = el("span", "s");
    si.appendChild(SB.icon("starFill"));
    star.appendChild(si);
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
    wrap.appendChild(star);

    if (data.gl && data.gl.length) {
      var gb = el("div", "goal-box");
      var gh = el("div", "gh");
      gh.appendChild(SB.icon("target"));
      gh.appendChild(el("b", "", t("wkGoal")));
      gh.appendChild(el("small", "", t("wkGoalHint")));
      gb.appendChild(gh);
      var gc = el("div", "gchips");
      var paintGoals = function () {
        var all = gc.querySelectorAll(".gchip");
        for (var j = 0; j < all.length; j++) all[j].classList.toggle("on", +all[j].getAttribute("data-g") === (e.g || 0));
      };
      [[0, t("wkNoGoal")]].concat(data.gl).forEach(function (g) {
        var c = el("button", "gchip", g[1]);
        c.type = "button";
        c.setAttribute("data-g", String(g[0]));
        c.addEventListener("click", function () { e.g = g[0]; SB.haptic("select"); paintGoals(); saveDraft(); });
        gc.appendChild(c);
      });
      paintGoals();
      gb.appendChild(gc);
      wrap.appendChild(gb);
    }

    wrap.appendChild(el("h2", "", t("comment")));
    if (savedFlag(data.c, s[0])) wrap.appendChild(el("p", "hint", t("commentExists")));
    var area = el("textarea");
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
      wrap.appendChild(chips);
    }
    area.maxLength = COMMENT_MAX;
    area.placeholder = t("commentHint");
    area.value = e.c || "";
    var counter = el("div", "counter-line");
    counter.appendChild(el("span", "", t("card") + ": " + (s[2] || "ru").toUpperCase()));
    var count = el("span", "", area.value.length + "/" + COMMENT_MAX);
    counter.appendChild(count);
    area.addEventListener("input", function () {
      if (area.value.length > COMMENT_MAX) area.value = area.value.slice(0, COMMENT_MAX);
      e.c = area.value;
      count.textContent = area.value.length + "/" + COMMENT_MAX;
      saveDraft();
    });
    wrap.appendChild(area);
    wrap.appendChild(counter);
    return wrap;
  }

  function studentHead(s, e, note) {
    var head = el("div", "student-head");
    head.appendChild(SB.avatar(s[1], s[0]));
    var nm = el("div", "grow");
    nm.appendChild(el("div", "student-name", s[1]));
    var lv = avgLevel(e);
    nm.appendChild(el("span", "badge", note + (lv === null ? "" : " · " + t("wkLevel") + " " + lv + "%")));
    head.appendChild(nm);
    return head;
  }

  function renderStudent(index) {
    var s = targets[index], sid = s[0], e = entry(sid);
    clear();
    SB.setSave(t("save"), save, false);
    var backToList = function () { saveDraft(); renderList(); };
    SB.setBack(backToList);
    var top = el("div", "topbar");
    var back = el("button", "icon-btn");
    back.type = "button";
    back.appendChild(SB.icon("back"));
    back.addEventListener("click", backToList);
    top.appendChild(back);
    var bar = el("div", "grow");
    bar.appendChild(progressBar(filledCount(targets), targets.length));
    top.appendChild(bar);
    app.appendChild(top);

    var headBox = el("div");
    app.appendChild(headBox);
    var refreshHead = function () {
      headBox.innerHTML = "";
      headBox.appendChild(studentHead(s, e, t("wkStudentOf", { i: index + 1, n: targets.length })));
    };
    refreshHead();
    if (e.prev && !e.done) app.appendChild(el("p", "hint", t("fromLastWeek")));

    enabledQs().forEach(function (qi) {
      app.appendChild(levelRow(e, qi, function () { saveDraft(); refreshHead(); }));
    });
    app.appendChild(extras(s, e));

    var actions = el("div", "btn-row");
    if (index > 0) {
      var prev = el("button", "btn ghost", t("wkPrevStudent"));
      prev.type = "button";
      prev.addEventListener("click", function () { saveDraft(); renderStudent(index - 1); });
      actions.appendChild(prev);
    }
    var next = el("button", "btn");
    next.type = "button";
    next.appendChild(document.createTextNode(t("next")));
    next.appendChild(SB.icon("arrow"));
    next.addEventListener("click", function () { finishStudent(index); });
    actions.appendChild(next);
    app.appendChild(actions);
    var list = el("button", "btn ghost", t("toList"));
    list.type = "button";
    list.style.marginTop = "8px";
    list.addEventListener("click", backToList);
    app.appendChild(list);
  }

  function finishStudent(index) {
    var e = entry(targets[index][0]);
    var missing = -1;
    for (var i = 0; i < e.a.length; i++) if (enabled(i) && e.a[i] === null && !optional(i)) { missing = i; break; }
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
    for (var step = 1; step <= targets.length; step++) {
      var k = (index + step) % targets.length;
      if (status(targets[k][0]) !== "done" && k !== index) {
        SB.toast(t("great", { k: filledCount(targets), n: targets.length }));
        return renderStudent(k);
      }
    }
    renderList();
    SB.toast(t("allDone"));
  }

  // ---------------------------------------------------------------- 2б. по навыкам

  function renderSkill(pos) {
    var qs = enabledQs();
    if (pos >= qs.length) return renderSummary();
    var qi = qs[pos], q = data.q[qi];
    clear();
    var goBack = function () { saveDraft(); if (pos === 0) renderSetup(); else renderSkill(pos - 1); };
    SB.setBack(goBack);
    SB.setSave(t("save"), save, false);
    topbar(t("weekly"), goBack);

    var steps = el("div", "steps");
    for (var i = 0; i <= qs.length; i++) steps.appendChild(el("i", i < pos ? "on" : i === pos ? "now" : ""));
    app.appendChild(steps);

    var head = el("div", "skill-head");
    head.appendChild(el("div", "kicker", t("wkSkillOf", { i: pos + 1, n: qs.length }) +
                                       (optional(qi) ? " · " + t("optional") : "")));
    head.appendChild(el("h2", "", q[1]));
    var legend = el("div", "legend-lv");
    for (var v = 0; v <= 3; v++) {
      var item = el("span");
      var sw = el("i");
      sw.style.background = "var(--lv" + v + ")";
      item.appendChild(sw);
      item.appendChild(document.createTextNode(q[2 + v]));
      legend.appendChild(item);
    }
    head.appendChild(legend);
    app.appendChild(head);

    var rows = {};
    var bulk = el("div", "bulk");
    bulk.appendChild(el("span", "hint", t("wkAll")));
    [0, 1, 2, 3].forEach(function (v) {
      var c = el("button", "chip", t("lv" + v));
      c.type = "button";
      c.addEventListener("click", function () {
        targets.forEach(function (s) { entry(s[0]).a[qi] = v; });
        SB.haptic("success");
        saveDraft();
        Object.keys(rows).forEach(function (sid) { rows[sid](); });
      });
      bulk.appendChild(c);
    });
    app.appendChild(bulk);

    targets.forEach(function (s) {
      var e = entry(s[0]);
      var row = el("div", "srow-lv");
      row.id = "s" + s[0];
      row.appendChild(SB.avatar(s[1], s[0]));
      var nm = el("span", "grow");
      nm.appendChild(el("b", "", s[1]));
      var ans = el("small");
      nm.appendChild(ans);
      row.appendChild(nm);
      var box = el("span", "lvb");
      var buttons = [];
      var paint = function () {
        var cur = e.a[qi];
        buttons.forEach(function (b) {
          var bv = b.getAttribute("data-v");
          b.classList.toggle("sel", bv === "x" ? cur === null && optional(qi) : cur !== null && +bv === cur);
        });
        ans.textContent = cur === null ? (optional(qi) ? "— " + t("notRated") : t("pickLevel")) : q[2 + cur];
      };
      [0, 1, 2, 3].forEach(function (v) {
        var b = el("button", "l" + v);
        b.type = "button";
        b.setAttribute("data-v", String(v));
        b.title = q[2 + v];
        var bars = el("span", "bars v" + v);
        for (var k = 0; k < 4; k++) bars.appendChild(el("i"));
        b.appendChild(bars);
        b.addEventListener("click", function () {
          e.a[qi] = v; SB.haptic("select"); saveDraft(); paint();
          row.style.borderColor = "";
        });
        buttons.push(b);
        box.appendChild(b);
      });
      if (optional(qi)) {
        var sk = el("button", "skip", "—");
        sk.type = "button";
        sk.setAttribute("data-v", "x");
        sk.addEventListener("click", function () { e.a[qi] = null; SB.haptic("select"); saveDraft(); paint(); });
        buttons.push(sk);
        box.appendChild(sk);
      }
      row.appendChild(box);
      rows[s[0]] = paint;
      paint();
      app.appendChild(row);
    });

    var actions = el("div", "btn-row");
    var prev = el("button", "btn ghost", t("wkPrevSkill"));
    prev.type = "button";
    prev.addEventListener("click", goBack);
    actions.appendChild(prev);
    var next = el("button", "btn");
    next.type = "button";
    next.appendChild(document.createTextNode(pos === qs.length - 1 ? t("wkToSummary") : t("wkNextSkill")));
    next.appendChild(SB.icon("arrow"));
    next.addEventListener("click", function () {
      if (!optional(qi)) {
        var miss = targets.filter(function (s) { return entry(s[0]).a[qi] === null; });
        if (miss.length) {
          SB.haptic("error");
          SB.toast(t("wkNotAll"), true);
          miss.forEach(function (s) { var r = document.getElementById("s" + s[0]); if (r) r.style.borderColor = "var(--absent)"; });
          document.getElementById("s" + miss[0][0]).scrollIntoView({ behavior: "smooth", block: "center" });
          return;
        }
      }
      saveDraft();
      SB.haptic("select");
      renderSkill(pos + 1);
    });
    actions.appendChild(next);
    app.appendChild(actions);
  }

  // итоги (по навыкам): звезда, цель, комментарий по каждому ученику, затем «Сохранить»
  function renderSummary() {
    clear();
    var qs = enabledQs();
    targets.forEach(function (s) { var e = entry(s[0]); e.done = complete(e); });
    saveDraft();
    SB.setBack(function () { renderSkill(qs.length - 1); });
    topbar(t("wkSummary"), function () { renderSkill(qs.length - 1); });
    var steps = el("div", "steps");
    for (var i = 0; i <= qs.length; i++) steps.appendChild(el("i", i < qs.length ? "on" : "now"));
    app.appendChild(steps);
    app.appendChild(el("p", "hint", t("wkSummaryHint")));
    targets.forEach(function (s) {
      var e = entry(s[0]);
      var b = el("button", "choice");
      b.type = "button";
      b.appendChild(SB.avatar(s[1], s[0]));
      var tx = el("span", "grow", s[1]);
      var meta = el("span", "meta");
      meta.style.marginTop = "4px";
      var lv = avgLevel(e);
      if (lv !== null) meta.appendChild(el("span", "mini-chip", lv + "%"));
      if (e.s) meta.appendChild(el("span", "mini-chip star", "★"));
      if (e.g) meta.appendChild(el("span", "mini-chip goal", t("wkGoalShort")));
      if (e.c) meta.appendChild(el("span", "mini-chip", t("wkCommentShort")));
      tx.appendChild(meta);
      b.appendChild(tx);
      b.appendChild(el("span", "pill " + (e.done ? "done" : "empty"), e.done ? t("wkReady") : t("wkNotReady")));
      b.addEventListener("click", function () { SB.haptic("select"); renderExtras(s); });
      app.appendChild(b);
    });
    var n = doneIds().length;
    SB.setSave(t("saveN", { n: n }), save, n > 0);
  }

  function renderExtras(s) {
    var e = entry(s[0]);
    clear();
    SB.setSave(t("save"), save, false);
    var back = function () { e.c = (e.c || "").replace(/\s+/g, " ").trim(); saveDraft(); renderSummary(); };
    SB.setBack(back);
    topbar(t("wkExtras"), back);
    app.appendChild(studentHead(s, e, t("card") + ": " + (s[2] || "ru").toUpperCase()));
    app.appendChild(extras(s, e));
    var done = el("button", "btn", t("toList"));
    done.type = "button";
    done.style.marginTop = "14px";
    done.addEventListener("click", back);
    app.appendChild(done);
  }

  // ---------------------------------------------------------------- отправка

  function payload(ids) {
    return {
      v: 1, u: SB.uuid(), t: "wk", g: data.gid, w: SB.iso(weekMonday()),
      q: data.q.map(function (q) { return q[0]; }),
      // ответы: 0–3, «-» — навык не оценивался; затем комментарий, звезда недели (0/1), цель (номер, 0 — нет)
      r: ids.map(function (sid) {
        var e = draft[sid];
        return [sid, e.a.map(function (v, i) { return v === null || !enabled(i) ? "-" : String(v); }).join(""),
                e.c || "", e.s ? 1 : 0, e.g || 0];
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

  // Запуск формы: отдельной страницей (forms/*.html) или внутри приложения группы (app/).
  // opts.sid — сразу открыть этого ученика (из профиля в приложении группы).
  function start(d, demo, opts) {
    weekIdx = 0;
    data = d;
    data.q = (data.q || []).map(function (q) { return q.length > 6 ? q : q.concat([0]); });
    SB.demoMode = demo;
    var built = SB.parseISO(data.wk || SB.iso(monday(new Date())));
    weekShift = Math.round((monday(new Date()) - built) / (7 * 86400000));
    setup = loadSetup();
    draft = loadDraft();
    var idx = opts && opts.sid ? data.st.map(function (s) { return s[0]; }).indexOf(opts.sid) : -1;
    if (idx >= 0) {
      setup.mode = "student";
      targets = data.st.slice();
      renderStudent(idx);
    } else {
      renderSetup();
    }
  }

  SB.forms = SB.forms || {};
  SB.forms.weekly = { start: start, demo: DEMO };
  if (!window.SB_HUB) SB.load(DEMO, start);
})();
