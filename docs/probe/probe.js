/* Тестовая форма этапа 0: показывает, что дошло в ссылке, и отправляет боту пробные данные. */
(function () {
  "use strict";

  var tg = window.Telegram && window.Telegram.WebApp;
  var state = { data: null, method: "—", decodeOk: false, src: "нет", mode: "short" };

  // Комментарий ровно 80 букв кириллицы — худший случай по размеру
  var LONG_COMMENT = "Хорошо работал на уроке, но домашнее задание сдал поздно. Нужно повторить слова.".slice(0, 80);
  while (LONG_COMMENT.length < 80) LONG_COMMENT += "ж";

  var CHOICES = [
    ["short", "Короткая проверка", "небольшой пакет с результатами проверки"],
    ["weekly20", "Недельный отчёт на 20 учеников", "у каждого комментарий 80 букв — самый тяжёлый случай"],
    ["max4096", "Ровно 4096 байт", "предел Telegram — должно дойти"],
    ["over", "4097 байт", "больше предела — Telegram не должен отправить"]
  ];

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function addRow(box, label, value, cls) {
    var r = el("div", "row");
    r.appendChild(el("div", "label", label));
    r.appendChild(el("div", "value " + (cls || ""), value));
    box.appendChild(r);
  }

  function showError(text) {
    var box = document.getElementById("error");
    box.textContent = text;
    box.classList.remove("hidden");
  }

  // ---------- что отправляем ----------

  function baseInfo() {
    var p = SB.readParam("d");
    return {
      v: 1,
      u: SB.uuid(),
      t: "probe",
      m: state.mode,
      k: state.data && state.data.k ? state.data.k : "?",
      src: state.src,
      h: !!p.hash,
      q: !!p.query,
      ok: state.decodeOk,
      dm: state.method,
      dn: SB.hasNativeInflate(),
      ul: p.href.length,
      L: state.data && state.data.L ? state.data.L : 0,
      ns: state.data && state.data.students ? state.data.students.length : 0,
      p: tg ? tg.platform : "нет Telegram",
      tv: tg ? tg.version : "",
      tz: -new Date().getTimezoneOffset(),
      d: SB.localDate(),
      st: Math.floor(Date.now() / 1000),
      n: 0
    };
  }

  // Вписывает в пакет его собственный размер (n), чтобы бот сверил целостность
  function withSize(obj) {
    for (var i = 0; i < 3; i++) {
      obj.n = SB.byteSize(JSON.stringify(obj));
    }
    return JSON.stringify(obj);
  }

  function padTo(obj, target) {
    // Дополняем поле f буквами «ж» (2 байта) и «x» (1 байт) до нужного размера
    obj.f = "";
    obj.n = target;
    var size = SB.byteSize(JSON.stringify(obj));
    var need = target - size;
    var zh = Math.floor(need / 2);
    obj.f = new Array(zh + 1).join("ж") + (need % 2 ? "x" : "");
    return JSON.stringify(obj);
  }

  function buildPayload() {
    var obj = baseInfo();
    if (state.mode === "weekly20") {
      var studs = (state.data && state.data.students) || [];
      var prev = (state.data && state.data.prev) || {};
      obj.r = [];
      for (var i = 0; i < 20; i++) {
        var sid = studs[i] ? studs[i][0] : 1001 + i;
        var answers = prev[String(sid)] || [3, 2, 1, 0, 2, 3];
        obj.r.push([sid, answers, [1, 4], LONG_COMMENT]);
      }
      return withSize(obj);
    }
    if (state.mode === "max4096") return padTo(obj, SB.SEND_LIMIT);
    if (state.mode === "over") return padTo(obj, SB.SEND_LIMIT + 1);
    return withSize(obj);
  }

  // ---------- экран ----------

  function renderCounter() {
    var text = buildPayload();
    var size = SB.byteSize(text);
    var cls = size > SB.SEND_LIMIT ? "bad" : size > SB.SEND_LIMIT * 0.9 ? "warn" : "ok";
    var c = document.getElementById("counter");
    c.innerHTML = "";
    c.appendChild(el("span", cls, "Размер отправки: " + size + " из " + SB.SEND_LIMIT + " байт"));
    if (tg && tg.MainButton) {
      tg.MainButton.setText("Отправить (" + size + " байт)");
      tg.MainButton.show();
    }
  }

  function renderChoices() {
    var box = document.getElementById("choices");
    box.innerHTML = "";
    CHOICES.forEach(function (ch) {
      var b = el("button", "choice" + (state.mode === ch[0] ? " selected" : ""));
      b.type = "button";
      var t = el("div");
      t.appendChild(el("div", "", ch[1]));
      t.appendChild(el("div", "hint", ch[2]));
      b.appendChild(t);
      b.addEventListener("click", function () {
        state.mode = ch[0];
        renderChoices();
        renderCounter();
      });
      box.appendChild(b);
    });
  }

  function renderDiag() {
    var p = SB.readParam("d");
    var box = document.getElementById("diag");
    box.innerHTML = "";
    addRow(box, "Данные после # (fragment)", p.hash ? "дошли" : "нет", p.hash ? "ok" : "bad");
    addRow(box, "Данные после ? (query)", p.query ? "дошли" : "нет", p.query ? "ok" : "hint");
    addRow(box, "Расшифровка", state.decodeOk ? "успешно" : "не удалась", state.decodeOk ? "ok" : "bad");
    addRow(box, "Распаковка", state.method + (SB.hasNativeInflate() ? "" : " (встроенной нет)"));
    if (state.data && state.data.students) {
      addRow(box, "Учеников в ссылке", String(state.data.students.length));
    }
    if (state.data && state.data.q) {
      addRow(box, "Вопросов в ссылке", String(state.data.q.length));
    }
    if (state.data && state.data.L) {
      addRow(box, "Проверка длины ссылки", "≈" + state.data.L + " символов дошли целиком", "ok");
    }
    addRow(box, "Длина ссылки сейчас", p.href.length + " символов");
    addRow(box, "Telegram", tg ? (tg.platform + ", версия " + tg.version) : "не найден");
    addRow(box, "Дата на телефоне", SB.localDate());
  }

  function send() {
    var text = buildPayload();
    if (!tg || !tg.sendData) {
      showError("Форма открыта не из Telegram — отправить нельзя.");
      return;
    }
    try {
      tg.sendData(text); // после этого Telegram сам закроет форму
    } catch (e) {
      if (state.mode === "over") {
        showError("Telegram не дал отправить " + SB.byteSize(text) + " байт — так и должно быть. Проверка пройдена.");
      } else {
        showError("Не удалось отправить: " + e.message);
      }
    }
  }

  function start() {
    if (tg) {
      tg.ready();
      tg.expand();
      tg.MainButton.onClick(send);
    }
    var p = SB.readParam("d");
    var raw = p.hash || p.query;
    state.src = p.hash ? "hash" : p.query ? "query" : "нет";
    var after = function () {
      renderDiag();
      renderChoices();
      renderCounter();
    };
    if (!raw) {
      showError("В ссылке нет данных. Откройте форму кнопкой в чате бота.");
      after();
      return;
    }
    SB.decodeParam(raw).then(function (res) {
      state.data = res.data;
      state.method = res.method;
      state.decodeOk = true;
      after();
    }).catch(function (e) {
      showError("Данные в ссылке повреждены или обрезаны (" + e.message.slice(0, 40) + ").");
      after();
    });
  }

  start();
})();
