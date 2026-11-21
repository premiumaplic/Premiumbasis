/* Форма «Тема урока»: юнит из книги (если владелец загрузил список) или своя тема до 100 знаков. */
(function () {
  "use strict";

  var TOPIC_MAX = 100;
  var DEMO = { v: 1, f: "tp", gid: 1, g: "10-А", lang: "ru", cur: "Unit 4. Family",
               u: [[1, 4, "Family"], [2, 5, "My day"], [3, 6, "Food and drinks"]] };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var data, unit = null;

  function render() {
    app.innerHTML = "";
    var top = el("div", "topbar");
    var title = el("div", "grow");
    title.appendChild(el("h1", "", t("topic")));
    title.appendChild(el("span", "group-chip", "👥 " + data.g));
    top.appendChild(title);
    app.appendChild(top);
    if (SB.demoMode) app.appendChild(el("p", "hint", t("demo")));

    var cur = el("div", "card soft");
    cur.appendChild(el("div", "hint", t("current")));
    cur.appendChild(el("div", "", data.cur || t("noTopic")));
    app.appendChild(cur);

    if (data.u && data.u.length) {
      app.appendChild(el("h2", "", t("chooseUnit")));
      data.u.forEach(function (u) {
        var b = el("button", "choice" + (unit === u[0] ? " selected" : ""));
        b.type = "button";
        b.appendChild(el("span", "num badge", "Unit " + u[1]));
        b.appendChild(el("span", "grow", u[2]));
        b.addEventListener("click", function () {
          unit = unit === u[0] ? null : u[0];
          if (unit) area.value = "";
          SB.haptic("select");
          render();
        });
        app.appendChild(b);
      });
      app.appendChild(el("h2", "", t("ownTopic")));
    }

    var area = el("textarea");
    area.maxLength = TOPIC_MAX;
    area.placeholder = t("topicPlaceholder");
    area.value = render.text || "";
    var count = el("span", "", area.value.length + "/" + TOPIC_MAX);
    area.addEventListener("input", function () {
      render.text = area.value;
      count.textContent = area.value.length + "/" + TOPIC_MAX;
      if (area.value && unit) {
        unit = null; // своя тема вместо юнита
        var picked = app.querySelectorAll(".choice.selected");
        for (var i = 0; i < picked.length; i++) picked[i].classList.remove("selected");
      }
      update();
    });
    app.appendChild(area);
    var line = el("div", "counter-line");
    line.appendChild(el("span", ""));
    line.appendChild(count);
    app.appendChild(line);
    update();
  }

  function update() {
    var text = (render.text || "").replace(/\s+/g, " ").trim();
    SB.setSave(t("save"), save, !!unit || text.length > 0);
  }

  function save() {
    var text = (render.text || "").replace(/\s+/g, " ").trim().slice(0, TOPIC_MAX);
    var payload = { v: 1, u: SB.uuid(), t: "tp", g: data.gid };
    if (unit) payload.unit = unit; else payload.text = text;
    SB.haptic("success");
    SB.send(payload);
  }

  // Запуск формы: отдельной страницей (forms/*.html) или внутри приложения группы (app/)
  function start(d, demo) {
    unit = null;
    render.text = "";
    data = d;
    SB.demoMode = demo;
    render();
  }

  SB.forms = SB.forms || {};
  SB.forms.topic = { start: start, demo: DEMO };
  if (!window.SB_HUB) SB.load(DEMO, start);
})();
