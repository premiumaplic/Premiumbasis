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
      stw1: "станция", stw2: "станции", stw5: "станций",
      exportTitle: "Скачать отчёты группы (Excel)", exportSub: "эта и прошлая неделя, навыки и темы учеников", before: "пройденный раздел — нажмите, чтобы раскрыть",
      tabSkills: "Навыки", skillsTitle: "Навыки и темы", skillsSub: "оценено {k} из {n}",
      segStudents: "Ученики", segTopics: "Темы", rating: "Рейтинг", ratingOf: "из 10", overall: "Общий рейтинг",
      groupSkills: "Навыки группы", notRatedYet: "не оценивали", ratedAgo: "оценка: {d}", ratedBy: "Оценка от {d} · {who}",
      lastTime: "прошлая оценка", now: "сейчас", learned: "Выучил", unclear: "Не понял", learnedN: "Выучил · {n}",
      unclearN: "Не понял · {n}", noTopicsYet: "Пока нет тем", addTopic: "Добавить тему", addTo: "Куда добавлять",
      newTopicPh: "Название темы, например: Past Simple", add: "Добавить", suggestions: "Темы уроков группы",
      moveToLearned: "Выучил", moveToUnclear: "Не понял", removeTopic: "Убрать тему", cancel: "Отмена",
      startedFrom: "Начато с оценки от {d}. Меняйте только то, что изменилось.", tapScale: "Нажмите или проведите по шкале",
      prevStudent: "Предыдущий", nextStudent: "Следующий", saveN: "Сохранить · {n}", unsaved: "Не сохранено: {n}",
      assess: "Оценить", editTopics: "Изменить", topicsTitle: "Темы", skillsCard: "Навыки",
      topicMark: "Отметьте, кто выучил тему", allLearned: "Все выучили", resetAll: "Сбросить",
      topicStats: "выучили {l} · не поняли {u}", newTopicBtn: "Отметить по группе", topicsEmpty: "Тем пока нет. Добавьте тему урока или впишите свою.",
      notSet: "—", supportNote: "Вы работаете в группе учителя {t} как саппорт-учитель", supportNoteNoT: "Вы работаете в этой группе как саппорт-учитель",
      tooBigPf: "Помещается {k} из {n} учеников. Отправить их сейчас? Остальные останутся в черновике.",
      more: "ещё {n}", skillsTile: "Навыки и темы", weakest: "Слабее всего", strongest: "Сильнее всего",
      goalWeek: "Цель недели", consentShort: "Согласие", cardLang: "Карточка", stars8: "Звёзды", reportLevel: "Уровень",
      hiddenTopics: "Показаны последние темы. Всего: выучил {l}, не понял {u}.", crit: "Критерий"
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
      stw1: "bosqich", stw2: "bosqich", stw5: "bosqich",
      exportTitle: "Guruh hisobotlarini yuklab olish (Excel)", exportSub: "shu va oʻtgan hafta, oʻquvchilar koʻnikmalari va mavzulari", before: "oʻtilgan boʻlim — ochish uchun bosing",
      tabSkills: "Koʻnikmalar", skillsTitle: "Koʻnikmalar va mavzular", skillsSub: "{n} tadan {k} tasi baholangan",
      segStudents: "Oʻquvchilar", segTopics: "Mavzular", rating: "Reyting", ratingOf: "10 dan", overall: "Umumiy reyting",
      groupSkills: "Guruh koʻnikmalari", notRatedYet: "baholanmagan", ratedAgo: "baho: {d}", ratedBy: "{d} dagi baho · {who}",
      lastTime: "oldingi baho", now: "hozir", learned: "Oʻzlashtirdi", unclear: "Tushunmadi", learnedN: "Oʻzlashtirdi · {n}",
      unclearN: "Tushunmadi · {n}", noTopicsYet: "Hozircha mavzu yoʻq", addTopic: "Mavzu qoʻshish", addTo: "Qayerga qoʻshish",
      newTopicPh: "Mavzu nomi, masalan: Past Simple", add: "Qoʻshish", suggestions: "Guruh dars mavzulari",
      moveToLearned: "Oʻzlashtirdi", moveToUnclear: "Tushunmadi", removeTopic: "Mavzuni olib tashlash", cancel: "Bekor qilish",
      startedFrom: "{d} dagi bahodan boshlandi. Faqat oʻzgarganini tuzating.", tapScale: "Shkalani bosing yoki barmoq bilan suring",
      prevStudent: "Oldingi", nextStudent: "Keyingi", saveN: "Saqlash · {n}", unsaved: "Saqlanmagan: {n}",
      assess: "Baholash", editTopics: "Oʻzgartirish", topicsTitle: "Mavzular", skillsCard: "Koʻnikmalar",
      topicMark: "Mavzuni kim oʻzlashtirganini belgilang", allLearned: "Hammasi oʻzlashtirdi", resetAll: "Tozalash",
      topicStats: "oʻzlashtirdi {l} · tushunmadi {u}", newTopicBtn: "Guruh boʻyicha belgilash", topicsEmpty: "Hozircha mavzu yoʻq. Dars mavzusini qoʻshing yoki oʻzingiz yozing.",
      notSet: "—", supportNote: "Siz {t} oʻqituvchining guruhida yordamchi oʻqituvchi sifatida ishlayapsiz", supportNoteNoT: "Siz bu guruhda yordamchi oʻqituvchi sifatida ishlayapsiz",
      tooBigPf: "{n} tadan {k} oʻquvchi sigʻadi. Hozir yuborilsinmi? Qolganlari qoralamada qoladi.",
      more: "yana {n}", skillsTile: "Koʻnikmalar va mavzular", weakest: "Eng zaif", strongest: "Eng kuchli",
      goalWeek: "Hafta maqsadi", consentShort: "Rozilik", cardLang: "Karta", stars8: "Yulduzlar", reportLevel: "Daraja",
      hiddenTopics: "Oxirgi mavzular koʻrsatilgan. Jami: oʻzlashtirdi {l}, tushunmadi {u}.", crit: "Mezon"
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
      c: {}, sr: { "0": [12] },
      gl: [[1, "Делать домашнее задание вовремя"], [2, "Быть активнее на уроке"], [4, "Учить по 10 новых слов в день"],
           [5, "Читать по 15 минут в день"], [7, "Повторить грамматику темы"], [8, "Больше говорить на уроке"]],
      go: { "0": [[12, 5]] }
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
    gs: 6,
    tl: ["Unit 5. Present Simple", "Unit 4. My family", "Unit 3. Numbers 1–100", "Артикли a / an / the"],
    rl: 0, tn: "",
    cr: [[1, "Listening · Аудирование"], [2, "Reading · Чтение"], [3, "Writing · Письмо"],
         [4, "Speaking · Говорение"], [5, "Grammar · Грамматика"], [6, "Vocabulary · Словарный запас"]],
    pf: {
      "11": [[6, 7, 5, 6, 5, 7], [5, 6, 5, 5, 4, 6], SB.iso(SB.addDays(new Date(), -5)), "Учитель Т.",
             ["Unit 4. My family", "Unit 3. Numbers 1–100"], ["Артикли a / an / the"], [2, 1]],
      "12": [[9, 9, 8, 9, 8, 9], [8, 9, 8, 8, 8, 9], SB.iso(SB.addDays(new Date(), -5)), "Учитель Т.",
             ["Unit 5. Present Simple", "Unit 4. My family", "Unit 3. Numbers 1–100", "Артикли a / an / the"], [], [4, 0]],
      "13": [[4, 5, 3, 4, 3, 5], null, SB.iso(SB.addDays(new Date(), -12)), "Саида К.",
             ["Unit 3. Numbers 1–100"], ["Unit 5. Present Simple", "Артикли a / an / the", "Unit 4. My family"], [1, 3]],
      "16": [[8, 9, 9, 8, 9, 8], null, SB.iso(SB.addDays(new Date(), -2)), "Учитель Т.",
             ["Unit 5. Present Simple", "Unit 4. My family"], [], [2, 0]]
    }
  };

  var app = document.getElementById("app");
  var el = SB.el, t = SB.t;
  var hub, demo = false, tab = "home", nav = null, mapOpen = {};

  // ---------------------------------------------------------------- данные

  // Элемент «иконка + текст»
  function it(tag, cls, iconName, text) {
    var e = el(tag, cls);
    if (iconName) e.appendChild(SB.icon(iconName));
    if (text !== undefined && text !== null) e.appendChild(document.createTextNode(text));
    return e;
  }

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
  //
  // Вкладки (go) и стопка подэкранов поверх вкладки (sub / back). Каждый переход анимирован
  // через SB.transition: вглубь — «push», назад — «pop», между вкладками — «tab».

  var stack = [], scrollMem = {};

  function setTabs(visible) {
    document.body.classList.toggle("in-form", !visible);
    var bar = document.getElementById("tabbar");
    if (bar) bar.classList.toggle("hidden", !visible);
  }

  function tabItems() {
    var items = [["home", "home", t("tabHome")], ["students", "users", t("tabStudents")]];
    if (hub.cr && hub.cr.length) items.push(["skills", "radar", t("tabSkills")]);
    if (hub.stg && hub.stg.length) items.push(["map", "map", t("tabMap")]);
    items.push(["stats", "chart", t("tabStats")]);
    return items;
  }

  // Нижнее меню строится один раз; при смене вкладки двигается только бегунок (плавно)
  function renderTabbar() {
    var bar = document.getElementById("tabbar");
    var items = tabItems();
    if (!bar.firstChild || bar.getAttribute("data-n") !== String(items.length)) {
      bar.innerHTML = "";
      bar.setAttribute("data-n", items.length);
      var inner = el("div", "tabs-inner");
      inner.appendChild(el("span", "tab-ind"));
      items.forEach(function (x) {
        var b = el("button", "tab");
        b.type = "button";
        b.setAttribute("data-tab", x[0]);
        b.appendChild(SB.icon(x[1]));
        b.appendChild(el("span", "tab-label", x[2]));
        b.addEventListener("click", function () { if (x[0] !== tab || stack.length) go(x[0]); });
        inner.appendChild(b);
      });
      bar.appendChild(inner);
    }
    var att = hub.st.filter(function (s) { return badHints(s[0]).length; }).length;
    var pending = pfChangedCount();
    Array.prototype.forEach.call(bar.querySelectorAll(".tab"), function (b) {
      var on = b.getAttribute("data-tab") === tab;
      b.classList.toggle("active", on);
      b.setAttribute("aria-current", on ? "page" : "false");
      var dot = b.querySelector(".tab-dot");
      var n = b.getAttribute("data-tab") === "students" ? att : b.getAttribute("data-tab") === "skills" ? pending : 0;
      if (n && !dot) { dot = el("span", "tab-dot"); b.appendChild(dot); }
      if (dot) { if (n) { if (dot.textContent !== String(n)) SB.bump(dot); dot.textContent = String(n); } else dot.remove(); }
    });
    moveIndicator();
  }
  function moveIndicator() {
    var bar = document.getElementById("tabbar");
    var ind = bar.querySelector(".tab-ind"), act = bar.querySelector(".tab.active");
    if (!ind || !act) return;
    var w = act.offsetWidth * 0.4;
    ind.style.width = w + "px";
    ind.style.transform = "translateX(" + (act.offsetLeft + (act.offsetWidth - w) / 2) + "px)";
  }
  window.addEventListener("resize", function () { if (hub) moveIndicator(); });
  window.addEventListener("scroll", function () {
    document.body.classList.toggle("scrolled", window.scrollY > 4);
  }, { passive: true });

  function screen(cls) {
    app.innerHTML = "";
    window.scrollTo(0, 0);
    var box = el("div", "screen " + (cls || ""));
    app.appendChild(box);
    return box;
  }

  // Элементы появляются по очереди (первые 8 — с шагом 30 мс, остальные сразу)
  function stagger(container) {
    var kids = container.children;
    for (var i = 0; i < kids.length; i++) {
      kids[i].classList.add("rise");
      kids[i].style.animationDelay = Math.min(i, 8) * 30 + "ms";
    }
  }

  function renderTab(name) {
    if (name === "students") return studentsTab();
    if (name === "skills") return skillsTab();
    if (name === "map") return mapTab();
    if (name === "stats") return statsTab();
    return homeTab();
  }

  function go(name, dir, shared) {
    if (name !== tab) SB.haptic("select");
    var fromSub = stack.length > 0 || document.body.classList.contains("in-form");
    if (!fromSub) scrollMem[tab] = window.scrollY;
    var kind = dir || (fromSub && name === tab ? "pop" : name === tab ? "none" : "tab");
    SB.transition(kind, function () {
      tab = name;
      nav = null;
      stack = [];
      setTabs(true);
      renderTabbar();
      hubbar(false);
      SB.hubHome = null;
      SB.setBack(name === "home" ? null : function () { go("home"); });
      renderTab(name);
      tabSave();
      if (kind === "pop" && scrollMem[name]) window.scrollTo(0, scrollMem[name]);
    }, shared);
  }

  // «Сохранить» на вкладке: видна, если в черновике навыков и тем есть изменения
  function tabSave() {
    var n = pfChangedCount();
    SB.setSave(t("saveN", { n: n }), savePf, n > 0 && tab === "skills" && !stack.length);
  }

  // Подэкран поверх вкладки (профиль, редактор, станция, подсказки, карточки)
  function sub(render, shared) {
    if (!stack.length) scrollMem[tab] = window.scrollY;
    stack.push(render);
    show(render, "push", shared);
  }
  function back(shared) {
    stack.pop();
    if (!stack.length) return go(tab, "pop", shared);
    show(stack[stack.length - 1], "pop", shared);
  }
  function show(render, dir, shared) {
    SB.transition(dir, function () {
      nav = render;
      setTabs(true);
      renderTabbar();
      SB.setSave(t("save"), function () {}, false);
      SB.setBack(function () { back(); });
      render();
    }, shared);
  }
  // Заменить текущий подэкран другим (соседний ученик в редакторе)
  function replaceSub(render, dir) {
    stack[stack.length - 1] = render;
    show(render, dir);
  }

  function backRow(box, title) {
    var top = el("div", "subbar");
    var b = el("button", "icon-btn");
    b.type = "button";
    b.setAttribute("aria-label", "←");
    b.appendChild(SB.icon("back"));
    b.addEventListener("click", function () { back(); });
    top.appendChild(b);
    top.appendChild(el("h1", "grow", title));
    box.appendChild(top);
    return top;
  }

  // Общий элемент для «перелёта»: аватар и имя ученика в строке списка с номером sid
  function rowShared(sid) {
    var row = app.querySelector('[data-sid="' + sid + '"]');
    return row ? { av: row.querySelector(".lvl-avatar, .avatar"), name: row.querySelector("b") } : null;
  }
  function heroShared() {
    return { av: app.querySelector(".phero .lvl-avatar, .phero .avatar"), name: app.querySelector(".phero .pname") };
  }
  function openProfile(sid, rowEl) {
    SB.haptic("select");
    var from = rowEl ? { av: rowEl.querySelector(".lvl-avatar, .avatar"), name: rowEl.querySelector("b") } : rowShared(sid);
    sub(function () { profile(sid); }, { from: from, to: heroShared });
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
    if (!stack.length) scrollMem[tab] = window.scrollY;
    // «Назад» из формы — на экран, откуда её открыли (подэкран или вкладка)
    SB.hubHome = function () {
      if (stack.length) show(stack[stack.length - 1], "pop");
      else go(tab, "pop");
    };
    SB.transition("push", function () {
      setTabs(false);
      hubbar(true);
      window.scrollTo(0, 0);
      SB.setBack(SB.hubHome);
      SB.forms[kind].start(formData(kind), demo, opts || {});
    });
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
      chips.appendChild(it("span", "hchip exam" + (dx <= 7 ? " soon" : ""), "cap",
                           dx === 0 ? t("examToday") : dx === 1 ? t("examTomorrow") : t("examIn", { n: dx })));
    }
    var sk = streak();
    if (sk >= 2) chips.appendChild(it("span", "hchip", "check", t("streak", { n: sk })));
    left.appendChild(chips);
    if (hub.wkt) {
      var segs = el("div", "week-segs");
      for (var i = 1; i <= hub.wkt; i++) segs.appendChild(el("i", i < hub.wkn ? "on" : i === hub.wkn ? "now" : ""));
      segs.appendChild(SB.icon("flag"));
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
    if (hub.rl) box.appendChild(it("div", "support-note", "lifebuoy",
                                   hub.tn ? t("supportNote", { t: hub.tn }) : t("supportNoteNoT")));

    // ---- следующий шаг (как «следующий урок» в Duolingo)
    box.appendChild(nextStep(done, total));

    // ---- быстрые действия
    box.appendChild(el("h2", "", t("actions")));
    var grid = el("div", "quick");
    grid.appendChild(quick("report", t("weekly"), done + "/" + total, "orange", function () { openForm("weekly"); }));
    if (hub.ex) {
      grid.appendChild(quick("cap", hub.ex.mode === "score" ? t("exam") : t("decision"),
                             hub.ex.nx ? "➜ " + hub.ex.nx : hub.ex.sn, "blue", function () { openForm("exam"); }));
    }
    grid.appendChild(quick("book", t("topic"), hub.tp && hub.tp.cur ? hub.tp.cur : t("noTopic"), "green",
                           function () { openForm("topic"); }));
    if (hub.cr && hub.cr.length) {
      var rated = hub.st.filter(function (s) { return effRatings(s[0]).some(function (v) { return v; }); }).length;
      grid.appendChild(quick("radar", t("skillsTile"), t("skillsSub", { k: rated, n: total }), "violet",
                             function () { go("skills"); }, pfChangedCount()));
    }
    var ready = cardsReady().length;
    grid.appendChild(quick("mail", t("cards"), ready + "/" + total, "pink", function () { sub(cardsScreen); }));
    grid.appendChild(quick("bulb", t("hints"), hintsBad.length ? t("hintsN", { n: hintsBad.length }) : t("noHints"),
                           "yellow", function () { sub(hintsScreen); }, hintsBad.length));
    if (hub.stg && hub.stg.length) {
      grid.appendChild(quick("map", t("tabMap"), hub.gs ? stName(hub.gs) : "—", "blue", function () { go("map"); }));
    } else {
      grid.appendChild(quick("chart", t("tabStats"), t("groupLevel"), "blue", function () { go("stats"); }));
    }
    if (hub.att) {
      var attToday = hub.att.h && hub.att.h["0"];
      grid.appendChild(quick("checkbox", t("attendance"), attToday ? t("attToday") : t("attMark"), "teal",
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
    if (mood === "party" || mood === "happy") card.classList.add("done");
    var ic = el("span", "mission-ic");
    ic.appendChild(SB.icon(mood === "party" ? "check" : btn === t("stepSend") ? "mail" :
                           hub.ex && dx === 0 && hub.ex.mode === "score" ? "cap" : total ? "report" : "users", "ic-lg"));
    card.appendChild(ic);
    var text = el("div", "grow");
    text.appendChild(el("small", "", t("nextStep")));
    text.appendChild(el("b", "", title));
    text.appendChild(el("span", "sub", subText));
    card.appendChild(text);
    if (btn) {
      var b = el("button", "btn", btn);
      b.type = "button";
      b.addEventListener("click", action);
      card.appendChild(b);
    }
    return card;
  }
  function quick(icon, title, subText, color, onClick, badge) {
    var b = el("button", "qtile " + color);
    b.type = "button";
    var qi = el("span", "qicon");
    qi.appendChild(SB.icon(icon));
    b.appendChild(qi);
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
    row.appendChild(it("span", "hint-icon", h[4] === "growth" ? "trendUp" : "alert"));
    if (link && s) row.addEventListener("click", function () { openProfile(s[0]); });
    return row;
  }

  // ---------------------------------------------------------------- ученики

  var filter = "all";
  function studentsTab() {
    var box = screen("students");
    var head = el("div", "tabhead");
    head.appendChild(el("h1", "", t("tabStudents")));
    head.appendChild(el("span", "group-chip", hub.g + " · " + hub.st.length));
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
    if (starred(s[0])) wrap.appendChild(it("span", "star-badge", "starFill"));
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
    meta.appendChild(it("span", "mini-chip " + (reportDone(s[0]) ? "ok" : "todo"), reportDone(s[0]) ? "check" : null,
                        reportDone(s[0]) ? t("reportDone") : t("noReport")));
    var bad = badHints(s[0]).length;
    if (bad) meta.appendChild(it("span", "mini-chip warn", "alert", String(bad)));
    var ovr = hub.cr && hub.cr.length ? overallOf(effRatings(s[0])) : null;
    if (ovr !== null) meta.appendChild(it("span", "mini-chip", "radar", fmt(ovr) + "/10"));
    mid.appendChild(meta);
    b.appendChild(mid);
    var right = el("span", "sright");
    right.appendChild(SB.sparkline(hist(s), 72, 26));
    var lv = levelOf(s);
    right.appendChild(el("small", "", lv === null ? "—" : pct(lv) + "%"));
    b.appendChild(right);
    b.setAttribute("data-sid", s[0]);
    b.addEventListener("click", function () { openProfile(s[0], b); });
    return b;
  }

  // ---------------------------------------------------------------- профиль ученика

  function goalText(sid) {
    var list = ((hub.wk.go || {})["0"] || []).concat((hub.wk.go || {})["1"] || []);
    var hit = list.filter(function (x) { return x[0] === sid; })[0];
    if (!hit) return null;
    var g = (hub.wk.gl || []).filter(function (x) { return x[0] === hit[1]; })[0];
    return g ? g[1] : null;
  }

  function profile(sid) {
    var s = student(sid);
    var box = screen("profile");
    backRow(box, "");
    // ---- шапка: аватар с кольцом уровня, имя, станция и отметки
    var head = el("div", "phero");
    head.appendChild(levelAvatar(s, 76));
    var info = el("div", "grow");
    info.appendChild(el("h1", "pname", s[1]));
    var chips = el("div", "meta");
    if (hub.stg && hub.stg.length && s[3]) chips.appendChild(it("span", "mini-chip", "map", stName(s[3])));
    chips.appendChild(el("span", "mini-chip", t("cardLang") + ": " + (s[2] || "ru").toUpperCase()));
    chips.appendChild(it("span", "mini-chip " + (s[4] ? "ok" : "warn"), s[4] ? "check" : "alert",
                         s[4] ? t("consentYes") : t("consentNo")));
    if (starred(sid)) chips.appendChild(it("span", "mini-chip star", "starFill", t("star")));
    info.appendChild(chips);
    head.appendChild(info);
    box.appendChild(head);

    // ---- три главных числа: уровень по отчётам, рейтинг навыков, темы
    var lv = levelOf(s), vals = effRatings(sid), ov = overallOf(vals), pv = overallOf(prevRatings(sid) || []);
    var tops = effTopics(sid), counts = topicCounts(sid, tops);
    var k3 = el("div", "kpi3");
    k3.appendChild(ktile(t("reportLevel"), lv === null ? "—" : pct(lv), lv === null ? "" : "%", trendText(s)));
    k3.appendChild(ktile(t("rating"), ov === null ? "—" : fmt(ov), ov === null ? "" : "/10",
                         ov !== null && pv !== null ? deltaText(ov - pv) : ov === null ? t("notRatedYet") : ""));
    k3.appendChild(ktile(t("topicsTitle"), String(counts[0]), "", counts[1] ? t("unclearN", { n: counts[1] }) : t("learned").toLowerCase(),
                         counts[1] ? "down" : ""));
    box.appendChild(k3);

    // ---- навыки: радар + полосы по критериям
    if (hub.cr && hub.cr.length) {
      var sk = el("div", "card");
      var sh = el("div", "card-head");
      sh.appendChild(el("h3", "ctitle", t("skillsCard")));
      sh.appendChild(smallBtn("pen", t("assess"), function () { openEditor(sid); }));
      sk.appendChild(sh);
      if (ov === null) {
        sk.appendChild(el("p", "hint", t("notRatedYet")));
      } else {
        sk.appendChild(SB.radar(hub.cr.map(function (c) { return shortCrit(c[1]); }), vals, prevRatings(sid)));
        if (prevRatings(sid)) {
          var lg = el("div", "legend-line");
          lg.appendChild(legendItem("", t("now")));
          lg.appendChild(legendItem("dash", t("lastTime")));
          sk.appendChild(lg);
        }
        sk.appendChild(critBars(vals, prevRatings(sid)));
        var rec0 = pfRec(sid);
        if (rec0 && rec0[2]) sk.appendChild(el("div", "byline", t("ratedBy", { d: dmy(rec0[2]), who: rec0[3] || "—" })));
      }
      box.appendChild(sk);

      // ---- темы: выучил / не понял
      var tc = el("div", "card");
      var th = el("div", "card-head");
      th.appendChild(el("h3", "ctitle", t("topicsTitle")));
      th.appendChild(smallBtn("pen", t("editTopics"), function () { openEditor(sid, "topics"); }));
      tc.appendChild(th);
      if (!counts[0] && !counts[1]) tc.appendChild(el("p", "hint", t("noTopicsYet")));
      else {
        if (counts[1]) tc.appendChild(topicGroup(sid, tops, "unclear", 6, false));
        if (counts[0]) tc.appendChild(topicGroup(sid, tops, "learned", 8, false));
      }
      var pfr = pfRec(sid);
      if (pfr && pfr[6] && (pfr[6][0] > pfr[4].length || pfr[6][1] > pfr[5].length)) {
        tc.appendChild(el("p", "hint", t("hiddenTopics", { l: pfr[6][0], u: pfr[6][1] })));
      }
      box.appendChild(tc);
    }

    // ---- уровень по неделям — столбики
    var chart = el("div", "card");
    chart.appendChild(el("h3", "ctitle", t("levelWeeks")));
    chart.appendChild(columns(hist(s).split(""), function (ch) { return ch === "-" ? null : +ch / 9 * 100; }));
    box.appendChild(chart);

    // ---- последний отчёт: показатели
    var r = rec(sid), code = r["0"] || r["1"];
    var answers = el("div", "card");
    var ah = el("div", "card-head");
    ah.appendChild(el("h3", "ctitle", r["0"] ? t("lastReport") : t("lastReportPrev")));
    ah.appendChild(smallBtn("report", t("fillReport"), function () { openForm("weekly", { sid: sid }); }));
    answers.appendChild(ah);
    var goal = goalText(sid);
    if (goal) answers.appendChild(it("div", "mini-chip goal", "target", t("goalWeek") + ": " + goal));
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
      var mv = it("button", "btn ghost", "route", t("moveStudent"));
      mv.type = "button";
      mv.addEventListener("click", function () { sub(function () { pickStation(sid); }); });
      st.appendChild(mv);
      box.appendChild(st);
    }
    stagger(box);
  }

  function ktile(label, value, unit, subText, subCls) {
    var k = el("div", "ktile");
    k.appendChild(el("span", "klab", label));
    var v = el("span", "kval", value);
    if (unit) v.appendChild(el("small", "", unit));
    k.appendChild(v);
    if (subText) k.appendChild(el("span", "ksub " + (subCls || (/^\+/.test(subText) ? "up" : /^−/.test(subText) ? "down" : "")), subText));
    return k;
  }
  function smallBtn(iconName, text, onClick) {
    var b = it("button", "small-btn", iconName, text);
    b.type = "button";
    b.addEventListener("click", onClick);
    return b;
  }
  function legendItem(cls, text) {
    var x = el("span", "");
    x.appendChild(el("i", cls));
    x.appendChild(document.createTextNode(text));
    return x;
  }
  function fmt(v) { return (Math.round(v * 10) / 10).toFixed(1).replace(/\.0$/, "").replace(".", SB.lang() === "ru" ? "," : "."); }
  function deltaText(d) {
    if (Math.abs(d) < 0.05) return "= 0";
    return (d > 0 ? "+" : "−") + fmt(Math.abs(d));
  }
  function dmy(isoDate) { var p = isoDate.split("-"); return p[2] + "." + p[1]; }
  function trendText(s) {
    var h = hist(s), vals = [];
    for (var i = 0; i < h.length; i++) if (h.charAt(i) !== "-") vals.push(+h.charAt(i));
    if (vals.length < 2) return "";
    var d = Math.round((vals[vals.length - 1] - vals[vals.length - 2]) / 9 * 100);
    return d > 0 ? "+" + d + "%" : d < 0 ? "−" + -d + "%" : "= 0%";
  }
  // «Listening · Аудирование» → «Listening» на радаре (коротко), полное — в полосах
  function shortCrit(name) { return name.split(" · ")[0]; }
  function rateCls(v) { return v >= 9 ? "r-hi" : v >= 7 ? "r-ok" : v >= 4 ? "r-mid" : "r-lo"; }

  function critBars(vals, prev) {
    var wrap = el("div", "crits");
    (hub.cr || []).forEach(function (c, i) {
      var v = vals[i] || 0, p = prev ? prev[i] || 0 : 0;
      var row = el("div", "crit");
      row.appendChild(el("span", "cname", c[1]));
      var val = el("span", "cval", v ? String(v) : "—");
      if (v && p && v !== p) val.appendChild(el("small", v > p ? "up" : "down", (v > p ? "▲" : "▼") + Math.abs(v - p)));
      row.appendChild(val);
      var track = el("span", "ctrack " + (v ? rateCls(v) : ""));
      var fill = el("i");
      track.appendChild(fill);
      if (p) { var mark = el("b"); mark.style.left = "calc(" + p * 10 + "% - 1px)"; track.appendChild(mark); }
      row.appendChild(track);
      wrap.appendChild(row);
      if (SB.reduced) fill.style.width = v * 10 + "%";
      else setTimeout(function () { fill.style.width = v * 10 + "%"; }, 120 + i * 50);
    });
    return wrap;
  }

  // Группа чипов тем (выучил / не понял); editable — в редакторе (нажатие открывает шторку)
  function topicGroup(sid, tops, status, limit, editable, onChange) {
    var g = el("div", "topic-group");
    var items = Object.keys(tops).map(function (k) { return tops[k]; }).filter(function (x) { return x.status === status; });
    var h = it("h4", status, status === "learned" ? "checkCircle" : "help", status === "learned" ? t("learned") : t("unclear"));
    h.appendChild(el("small", "", "· " + items.length));
    g.appendChild(h);
    var chips = el("div", "kchips");
    if (!items.length) chips.appendChild(el("span", "topic-empty", t("noTopicsYet")));
    var shown = limit && !editable ? items.slice(0, limit) : items;
    shown.forEach(function (x) {
      var c = it(editable ? "button" : "span", "kchip " + status + (x.status !== x.base ? " changed" : "") + (x.fresh ? " new" : ""),
                 status === "learned" ? "check" : "help", null);
      c.appendChild(el("span", "", x.title));
      if (editable) {
        c.type = "button";
        c.addEventListener("click", function () { topicSheet(sid, x, onChange); });
      }
      chips.appendChild(c);
    });
    if (shown.length < items.length) chips.appendChild(el("span", "kchip more", t("more", { n: items.length - shown.length })));
    g.appendChild(chips);
    return g;
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
      col.appendChild(el("small", "colval", v === null ? "" : String(Math.round(v))));
      col.appendChild(fill);
      col.appendChild(el("small", "", i === n - 1 ? t("thisWeekShort") : "−" + (n - 1 - i)));
      wrap.appendChild(col);
      var h = v === null ? 6 : Math.max(6, v * 0.82);   // место сверху для подписи
      if (SB.reduced) fill.style.height = h + "%";
      else setTimeout(function () { fill.style.height = h + "%"; }, 60 + i * 40);
    });
    return wrap;
  }

  // ---------------------------------------------------------------- навыки и темы: данные
  //
  // hub.cr — критерии [[номер, название]]; hub.pf — {ученик: [оценки, прошлые, дата, кто, выучил,
  // не понял, [всего выучил, всего не понял]]}. Изменения копятся в черновике на телефоне
  // (pfDraft) и уходят боту одной отправкой «Сохранить · N».

  var pfDraft = {};

  function pfRec(sid) { return (hub.pf || {})[String(sid)] || null; }
  function zeros() { return (hub.cr || []).map(function () { return 0; }); }
  function baseRatings(sid) { var r = pfRec(sid); return r && r[0] ? r[0].slice() : zeros(); }
  function prevRatings(sid) { var r = pfRec(sid); return r && r[1] ? r[1] : null; }
  function sameArr(a, b) { return a.length === b.length && a.every(function (v, i) { return v === b[i]; }); }
  function overallOf(vals) {
    var v = (vals || []).filter(function (x) { return x > 0; });
    return v.length ? v.reduce(function (a, b) { return a + b; }, 0) / v.length : null;
  }
  function effRatings(sid) {
    var d = pfDraft[sid];
    return d && d.r ? d.r.slice() : baseRatings(sid);
  }
  // Темы ученика с учётом черновика: {ключ: {title, status: learned/unclear/x, base}}
  function effTopics(sid) {
    var r = pfRec(sid), map = {};
    if (r) {
      r[4].forEach(function (x) { map[x.toLowerCase()] = { title: x, status: "learned", base: "learned" }; });
      r[5].forEach(function (x) { map[x.toLowerCase()] = { title: x, status: "unclear", base: "unclear" }; });
    }
    var d = (pfDraft[sid] || {}).t || {};
    Object.keys(d).forEach(function (k) {
      if (map[k]) map[k].status = d[k].s;
      else if (d[k].s !== "x") map[k] = { title: d[k].title, status: d[k].s, base: null };
    });
    return map;
  }
  function topicCounts(sid, tops) {
    var r = pfRec(sid), shown = [0, 0], now = [0, 0];
    if (r) { shown = [r[4].length, r[5].length]; }
    Object.keys(tops).forEach(function (k) {
      if (tops[k].status === "learned") now[0]++;
      if (tops[k].status === "unclear") now[1]++;
    });
    // в ссылке могли прийти не все темы: прибавляем скрытые
    var hidden = r && r[6] ? [r[6][0] - shown[0], r[6][1] - shown[1]] : [0, 0];
    return [now[0] + Math.max(0, hidden[0]), now[1] + Math.max(0, hidden[1])];
  }
  function draftOf(sid) { return pfDraft[sid] || (pfDraft[sid] = { t: {} }); }
  function setTopic(sid, title, status) {
    var k = title.toLowerCase(), tops = effTopics(sid), d = draftOf(sid);
    var base = tops[k] ? tops[k].base : null;
    if (status === base || (status === "x" && !base)) delete d.t[k];
    else d.t[k] = { title: tops[k] ? tops[k].title : title, s: status };
    pfSaveDraft();
  }
  function setRatings(sid, vals) {
    var d = draftOf(sid);
    if (sameArr(vals, baseRatings(sid)) || !vals.some(function (v) { return v; })) delete d.r;
    else d.r = vals.slice();
    pfSaveDraft();
  }
  function pfChanged(sid) {
    var d = pfDraft[sid];
    return !!d && (!!d.r || Object.keys(d.t || {}).length > 0);
  }
  function pfChangedIds() {
    return hub.st.map(function (s) { return s[0]; }).filter(pfChanged);
  }
  function pfChangedCount() { return hub && hub.cr ? pfChangedIds().length : 0; }
  function pfRow(sid) {
    var d = pfDraft[sid], tops = effTopics(sid), L = [], U = [], X = [];
    Object.keys(d.t || {}).forEach(function (k) {
      var x = d.t[k];
      if (x.s === "learned") L.push(x.title); else if (x.s === "unclear") U.push(x.title); else X.push(tops[k] ? tops[k].title : x.title);
    });
    return [sid, d.r || null, L, U, X];
  }

  function draftKey() { return "pf:" + hub.gid; }
  function pfSaveDraft() {
    Object.keys(pfDraft).forEach(function (k) { if (!pfChanged(+k)) delete pfDraft[k]; });
    if (demo) return;
    var ids = (hub.cr || []).map(function (c) { return c[0]; });
    if (Object.keys(pfDraft).length) SB.draftSet(draftKey(), { c: ids, d: pfDraft });
    else SB.draftClear(draftKey());
  }
  // Черновик с телефона: только если критерии те же и ученики ещё в группе; значения проверяются
  function pfLoadDraft() {
    pfDraft = {};
    var saved = SB.draftGet(draftKey());
    var ids = (hub.cr || []).map(function (c) { return c[0]; });
    if (!saved || !saved.d || !Array.isArray(saved.c) || !sameArr(saved.c, ids)) return;
    Object.keys(saved.d).forEach(function (k) {
      var sid = +k, d = saved.d[k];
      if (!student(sid) || !d || typeof d !== "object") return;
      var out = { t: {} };
      if (Array.isArray(d.r) && d.r.length === ids.length &&
          d.r.every(function (v) { return v === (v | 0) && v >= 0 && v <= 10; })) out.r = d.r;
      Object.keys(d.t || {}).forEach(function (key) {
        var x = d.t[key];
        if (x && typeof x.title === "string" && x.title.trim() && x.title.length <= 60 &&
            ["learned", "unclear", "x"].indexOf(x.s) >= 0 && key === x.title.toLowerCase()) out.t[key] = { title: x.title, s: x.s };
      });
      pfDraft[sid] = out;
    });
    pfSaveDraft();
  }

  function savePf() {
    var ids = pfChangedIds();
    if (!ids.length) return;
    var body = { v: 1, u: SB.uuid(), t: "pf", g: hub.gid, c: hub.cr.map(function (c) { return c[0]; }), r: [] };
    var fit = [];
    ids.forEach(function (sid) {
      var test = JSON.parse(JSON.stringify(body));
      test.r = body.r.concat([pfRow(sid)]);
      if (SB.byteSize(JSON.stringify(test)) <= SB.SEND_LIMIT) { body.r = test.r; fit.push(sid); }
    });
    var go2 = function () {
      SB.haptic("success");
      fit.forEach(function (sid) { delete pfDraft[sid]; });
      pfSaveDraft();
      if (!SB.send(body)) {     // не Telegram (просмотр): вернуть черновик
        if (demo) SB.toast(t("demoNote"));
      }
    };
    if (!fit.length) return SB.toast(t("nothingToSave"), true);
    if (fit.length < ids.length) {
      SB.confirm(t("tooBigPf", { k: fit.length, n: ids.length }), function (ok) { if (ok) go2(); });
    } else go2();
  }

  // Все темы, которые стоит предложить: уроки группы, юниты книги, темы других учеников
  function allTopics() {
    var seen = {}, out = [];
    var add = function (x) { var k = x.toLowerCase(); if (x && !seen[k]) { seen[k] = true; out.push(x); } };
    (hub.tl || []).forEach(add);
    if (hub.tp && hub.tp.cur) add(hub.tp.cur);
    ((hub.tp || {}).u || []).forEach(function (u) { add("Unit " + u[1] + ". " + u[2]); });
    hub.st.forEach(function (s) {
      var tops = effTopics(s[0]);
      Object.keys(tops).forEach(function (k) { if (tops[k].status !== "x") add(tops[k].title); });
    });
    return out;
  }

  // ---------------------------------------------------------------- вкладка «Навыки»

  var skillsSeg = "students";
  function skillsTab() {
    var box = screen("skills");
    var head = el("div", "tabhead");
    head.appendChild(el("h1", "", t("skillsTitle")));
    head.appendChild(el("span", "group-chip", hub.g));
    box.appendChild(head);
    box.appendChild(segmented([["students", t("segStudents")], ["topics", t("segTopics")]], skillsSeg, function (v) {
      skillsSeg = v;
      SB.transition("none", function () { skillsTab(); tabSave(); });
    }));
    var n = pfChangedCount();
    if (n) box.appendChild(it("div", "draft-pill", "pen", t("unsaved", { n: n })));
    if (skillsSeg === "topics") topicsList(box); else skillsStudents(box);
    stagger(box.querySelector(".klist") || box);
  }

  function segmented(options, value, onPick) {
    var wrap = el("div", "seg2");
    var ind = el("span", "seg-ind");
    wrap.appendChild(ind);
    var idx = 0;
    options.forEach(function (o, i) {
      var b = el("button", "seg-btn" + (o[0] === value ? " on" : ""), o[1]);
      b.type = "button";
      if (o[0] === value) idx = i;
      b.addEventListener("click", function () {
        if (o[0] === value) return;
        SB.haptic("select");
        ind.style.transform = "translateX(" + i * 100 + "%)";
        Array.prototype.forEach.call(wrap.querySelectorAll(".seg-btn"), function (x) { x.classList.remove("on"); });
        b.classList.add("on");
        setTimeout(function () { onPick(o[0]); }, SB.reduced ? 0 : 160);
      });
      wrap.appendChild(b);
    });
    ind.style.width = "calc((100% - 6px) / " + options.length + ")";
    ind.style.transform = "translateX(" + idx * 100 + "%)";
    return wrap;
  }

  function groupAverage() {
    var sums = zeros(), cnt = zeros(), rated = 0;
    hub.st.forEach(function (s) {
      var v = effRatings(s[0]);
      if (v.some(function (x) { return x; })) rated++;
      v.forEach(function (x, i) { if (x) { sums[i] += x; cnt[i]++; } });
    });
    return { vals: sums.map(function (x, i) { return cnt[i] ? x / cnt[i] : 0; }), rated: rated };
  }

  function skillsStudents(box) {
    var avg = groupAverage(), ov = overallOf(avg.vals);
    var card = el("div", "card");
    var top = el("div", "overall");
    var left = el("div", "grow");
    left.appendChild(el("small", "hint", t("groupSkills")));
    var num = el("b", "bignum", ov === null ? "—" : fmt(ov));
    if (ov !== null) num.appendChild(el("small", "", " /10"));
    left.appendChild(num);
    left.appendChild(el("span", "delta", t("skillsSub", { k: avg.rated, n: hub.st.length })));
    top.appendChild(left);
    if (ov !== null) {
      var best = 0, worst = 0;
      avg.vals.forEach(function (v, i) { if (v > avg.vals[best]) best = i; if (v && (v < avg.vals[worst] || !avg.vals[worst])) worst = i; });
      var bw = el("div", "grow");
      bw.appendChild(it("span", "mini-chip ok", "trendUp", t("strongest") + ": " + shortCrit(hub.cr[best][1])));
      bw.appendChild(it("span", "mini-chip warn", "trendDown", t("weakest") + ": " + shortCrit(hub.cr[worst][1])));
      bw.style.alignItems = "flex-end";
      top.appendChild(bw);
    }
    card.appendChild(top);
    if (ov !== null) card.appendChild(SB.radar(hub.cr.map(function (c) { return shortCrit(c[1]); }), avg.vals, null, { size: 240 }));
    box.appendChild(card);

    var list = el("div", "klist");
    hub.st.forEach(function (s) { list.appendChild(skillRow(s)); });
    box.appendChild(list);
  }

  function skillRow(s) {
    var sid = s[0], vals = effRatings(sid), ov = overallOf(vals);
    var tops = effTopics(sid), counts = topicCounts(sid, tops);
    var b = el("button", "krow" + (pfChanged(sid) ? " changed" : ""));
    b.type = "button";
    b.setAttribute("data-sid", sid);
    b.appendChild(SB.avatar(s[1], sid));
    var mid = el("span", "grow");
    mid.appendChild(el("b", "", s[1]));
    var meta = el("span", "meta");
    var bars = el("span", "mini-bars");
    vals.forEach(function (v, i) {
      var x = el("i", v ? "" : "none");
      x.style.height = (v ? 4 + v * 1.4 : 3) + "px";
      x.style.animationDelay = i * 40 + "ms";
      bars.appendChild(x);
    });
    meta.appendChild(bars);
    if (counts[0]) meta.appendChild(it("span", "mini-chip ok", "check", String(counts[0])));
    if (counts[1]) meta.appendChild(it("span", "mini-chip warn", "help", String(counts[1])));
    var r = pfRec(sid);
    meta.appendChild(el("span", "mini-chip", pfChanged(sid) ? t("unsaved", { n: "✎" }) :
                        r && r[2] ? t("ratedAgo", { d: SB.ago(r[2], hub.today) }) : t("notRatedYet")));
    mid.appendChild(meta);
    b.appendChild(mid);
    var badge = el("span", "rbadge " + (ov === null ? "" : rateCls(ov)), ov === null ? "—" : fmt(ov));
    badge.appendChild(el("small", "", t("ratingOf")));
    b.appendChild(badge);
    b.addEventListener("click", function () { openEditor(sid, null, b); });
    return b;
  }

  // ---- темы группы: сколько выучили и не поняли каждую тему
  function topicsList(box) {
    var add = el("div", "add-row");
    var input = el("input");
    input.type = "text"; input.maxLength = 60; input.placeholder = t("newTopicPh");
    var go2 = it("button", "btn small", "plus", t("newTopicBtn"));
    go2.type = "button";
    var openNew = function () {
      var title = input.value.replace(/\s+/g, " ").trim();
      if (!title) { SB.haptic("error"); input.focus(); return; }
      topicOpen(title);
    };
    go2.addEventListener("click", openNew);
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") openNew(); });
    add.appendChild(input);
    add.appendChild(go2);
    box.appendChild(add);
    var titles = allTopics();
    var list = el("div", "klist");
    if (!titles.length) list.appendChild(el("div", "empty-state", t("topicsEmpty")));
    titles.forEach(function (title) {
      var k = title.toLowerCase(), l = 0, u = 0;
      hub.st.forEach(function (s) {
        var x = effTopics(s[0])[k];
        if (x && x.status === "learned") l++;
        if (x && x.status === "unclear") u++;
      });
      var row = el("button", "trow");
      row.type = "button";
      var ic = el("span", "qicon");
      ic.appendChild(SB.icon("book"));
      row.appendChild(ic);
      var mid = el("span", "grow");
      mid.appendChild(el("b", "", title));
      var split = el("span", "split");
      var li = el("i", "l"), ui2 = el("i", "u");
      split.appendChild(li); split.appendChild(ui2);
      mid.appendChild(split);
      mid.appendChild(el("small", "", t("topicStats", { l: l, u: u })));
      row.appendChild(mid);
      row.appendChild(SB.icon("chevron"));
      row.addEventListener("click", function () { topicOpen(title); });
      list.appendChild(row);
      var n = hub.st.length || 1;
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        li.style.width = l / n * 100 + "%"; ui2.style.width = u / n * 100 + "%";
      }); });
    });
    box.appendChild(list);
  }

  function topicOpen(title) {
    SB.haptic("select");
    sub(function () { topicScreen(title); });
  }

  // ---- одна тема по всей группе: у каждого ученика «—», «Выучил» или «Не понял»
  function topicScreen(title) {
    var draw = function () {
      var box = screen("topic-screen");
      backRow(box, title);
      box.appendChild(el("p", "hint", t("topicMark")));
      var k = title.toLowerCase();
      var bulk = el("div", "bulk-row");
      bulk.appendChild(smallBtn("checkCircle", t("allLearned"), function () {
        hub.st.forEach(function (s) { setTopic(s[0], title, "learned"); });
        SB.haptic("success"); draw(); updateSave();
      }));
      bulk.appendChild(smallBtn("repeat", t("resetAll"), function () {
        hub.st.forEach(function (s) {
          var x = effTopics(s[0])[k];
          setTopic(s[0], title, x && x.base ? x.base : "x");
        });
        SB.haptic("select"); draw(); updateSave();
      }));
      box.appendChild(bulk);
      hub.st.forEach(function (s) {
        var row = el("div", "tstud");
        row.appendChild(SB.avatar(s[1], s[0]));
        row.appendChild(el("span", "grow", s[1]));
        var x = effTopics(s[0])[k], cur = x ? x.status : "x";
        var tri = el("div", "tri");
        [["x", "n", "minus", ""], ["learned", "l", "check", t("learned")], ["unclear", "u", "help", t("unclear")]].forEach(function (o) {
          var b = it("button", o[1] + (cur === o[0] ? " on" : ""), o[2], o[3]);
          b.type = "button";
          b.setAttribute("aria-pressed", cur === o[0] ? "true" : "false");
          b.addEventListener("click", function () {
            if (cur === o[0]) return;
            setTopic(s[0], title, o[0]);
            cur = o[0];
            SB.haptic("select");
            Array.prototype.forEach.call(tri.children, function (c) { c.classList.remove("on"); c.setAttribute("aria-pressed", "false"); });
            b.classList.add("on");
            b.setAttribute("aria-pressed", "true");
            SB.bump(b);
            updateSave();
          });
          tri.appendChild(b);
        });
        row.appendChild(tri);
        box.appendChild(row);
      });
    };
    nav = draw;
    draw();
    updateSave();
  }

  function updateSave() {
    var n = pfChangedCount();
    SB.setSave(t("saveN", { n: n }), savePf, n > 0);
    renderTabbar();
  }

  // ---------------------------------------------------------------- редактор ученика

  function openEditor(sid, focus, rowEl) {
    SB.haptic("select");
    var from = rowEl ? { av: rowEl.querySelector(".avatar"), name: rowEl.querySelector("b") } : null;
    sub(function () { editor(sid, focus); }, from ? { from: from, to: heroShared } : null);
  }

  function editor(sid, focus) {
    var s = student(sid);
    var addStatus = "learned";
    var box = screen("editor");
    backRow(box, "");
    var head = el("div", "phero");
    head.appendChild(SB.avatar(s[1], sid));
    head.firstChild.classList.add("xl");
    var info = el("div", "grow");
    info.appendChild(el("h1", "pname", s[1]));
    var r = pfRec(sid);
    info.appendChild(el("span", "hint", r && r[2] ? t("ratedBy", { d: dmy(r[2]), who: r[3] || "—" }) : t("notRatedYet")));
    head.appendChild(info);
    box.appendChild(head);

    // ---- общий рейтинг и радар (обновляются сразу при каждом изменении)
    var vals = effRatings(sid), base = baseRatings(sid);
    var card = el("div", "card");
    var ovRow = el("div", "overall");
    var left = el("div", "grow");
    left.appendChild(el("small", "hint", t("overall")));
    var num = el("b", "bignum");
    left.appendChild(num);
    var delta = el("span", "delta");
    left.appendChild(delta);
    ovRow.appendChild(left);
    card.appendChild(ovRow);
    var rad = SB.radar(hub.cr.map(function (c) { return shortCrit(c[1]); }), vals, base.some(function (v) { return v; }) ? base : null, { size: 240 });
    card.appendChild(rad);
    box.appendChild(card);
    var shownOv = overallOf(vals) || 0;
    function paintOverall(animate) {
      var ov = overallOf(vals), bo = overallOf(base);
      var target = ov || 0;
      var paint = function (x) {
        num.textContent = ov === null ? "—" : fmt(x);
        if (ov !== null) num.appendChild(el("small", "", " /10"));
      };
      if (animate) SB.tween(shownOv, target, 300, paint); else paint(target);
      shownOv = target;
      delta.textContent = ov !== null && bo !== null && !sameArr(vals, base) ? t("lastTime") + ": " + fmt(bo) + " (" + deltaText(ov - bo) + ")" :
        ov === null ? t("notRatedYet") : "";
      delta.className = "delta" + (ov !== null && bo !== null && ov > bo + 0.04 ? " up" : ov !== null && bo !== null && ov < bo - 0.04 ? " down" : "");
    }
    paintOverall(false);

    // ---- шкалы 1–10 по каждому критерию
    var rc = el("div", "card");
    rc.appendChild(el("h3", "ctitle", t("rating") + " · 1–10"));
    if (base.some(function (v) { return v; }) && r && r[2]) rc.appendChild(el("p", "start-note", t("startedFrom", { d: dmy(r[2]) })));
    else rc.appendChild(el("p", "start-note", t("tapScale")));
    hub.cr.forEach(function (c, i) {
      var row = el("div", "rate");
      var rh = el("div", "rate-head");
      rh.appendChild(el("b", "", c[1]));
      var valEl = el("span", "rate-val");
      rh.appendChild(valEl);
      row.appendChild(rh);
      var scale = el("div", "scale");
      var btns = [];
      for (var k = 1; k <= 10; k++) {
        var b = el("button", base[i] === k ? "was" : "", String(k));
        b.type = "button";
        b.setAttribute("aria-label", c[1] + ": " + k);
        b.setAttribute("data-v", k);
        btns.push(b);
        scale.appendChild(b);
      }
      var paint = function (bumpIt) {
        var v = vals[i];
        scale.className = "scale " + (v ? rateCls(v) : "");
        btns.forEach(function (b, j) {
          b.classList.toggle("on", j < v);
          b.classList.toggle("top", j === v - 1);
          b.style.transitionDelay = SB.reduced ? "0ms" : Math.abs(j - (v - 1)) * 18 + "ms";
        });
        valEl.textContent = v ? String(v) : t("notSet");
        valEl.className = "rate-val" + (v ? "" : " none");
        if (bumpIt) SB.bump(valEl);
      };
      var setV = function (v) {
        if (vals[i] === v) return;
        vals[i] = v;
        SB.haptic("select");
        paint(true);
        setRatings(sid, vals);
        rad.set(vals, 300);
        paintOverall(true);
        updateSave();
      };
      // нажатие — значение; повторное нажатие на то же — снять; провести пальцем — плавно выбрать
      var dragging = false, startV = null;
      scale.addEventListener("pointerdown", function (e) {
        var b = e.target.closest("button");
        if (!b) return;
        dragging = true; startV = vals[i];
        try { scale.setPointerCapture(e.pointerId); } catch (er) { /* старый браузер */ }
        setV(+b.getAttribute("data-v"));
        e.preventDefault();
      });
      scale.addEventListener("pointermove", function (e) {
        if (!dragging) return;
        var hit = document.elementFromPoint(e.clientX, e.clientY);
        var b = hit && hit.closest ? hit.closest(".scale button") : null;
        if (b && b.parentNode === scale) setV(+b.getAttribute("data-v"));
      });
      var end = function (e) {
        if (!dragging) return;
        dragging = false;
        var hit = e && document.elementFromPoint(e.clientX, e.clientY);
        var b = hit && hit.closest ? hit.closest(".scale button") : null;
        if (b && startV === +b.getAttribute("data-v") && vals[i] === startV) setV(0);
      };
      scale.addEventListener("pointerup", end);
      scale.addEventListener("click", function (e) {      // клавиатура (Enter/пробел): pointer-событий нет
        if (e.detail !== 0) return;
        var b = e.target.closest("button");
        if (b) setV(vals[i] === +b.getAttribute("data-v") ? 0 : +b.getAttribute("data-v"));
      });
      scale.addEventListener("pointercancel", function () { dragging = false; });
      row.appendChild(scale);
      var cap = el("div", "scale-cap");
      cap.appendChild(el("span", "", "1 · " + t("lv0")));
      cap.appendChild(el("span", "", base[i] ? t("lastTime") + ": " + base[i] : ""));
      cap.appendChild(el("span", "", t("lv3") + " · 10"));
      row.appendChild(cap);
      paint(false);
      rc.appendChild(row);
    });
    box.appendChild(rc);

    // ---- темы
    var tc = el("div", "card topics-card");
    tc.appendChild(el("h3", "ctitle", t("topicsTitle")));
    var groups = el("div", "");
    tc.appendChild(groups);
    var drawTopics = function () {
      groups.innerHTML = "";
      var tops = effTopics(sid);
      groups.appendChild(topicGroup(sid, tops, "learned", 0, true, drawAll));
      groups.appendChild(topicGroup(sid, tops, "unclear", 0, true, drawAll));
    };
    var addBox = el("div", "");
    tc.appendChild(addBox);
    var drawAdd = function () {
      addBox.innerHTML = "";
      addBox.appendChild(el("div", "sugg-title", t("addTo")));
      addBox.appendChild(segmented([["learned", t("learned")], ["unclear", t("unclear")]], addStatus, function (v) {
        addStatus = v; drawAdd();
      }));
      var row = el("div", "add-row");
      var input = el("input");
      input.type = "text"; input.maxLength = 60; input.placeholder = t("newTopicPh");
      var btn = it("button", "btn small", "plus", t("add"));
      btn.type = "button";
      var addIt = function () {
        var title = input.value.replace(/\s+/g, " ").trim();
        if (!title) { SB.haptic("error"); input.focus(); return; }
        addTopic(title);
        input.value = "";
      };
      btn.addEventListener("click", addIt);
      input.addEventListener("keydown", function (e) { if (e.key === "Enter") addIt(); });
      row.appendChild(input);
      row.appendChild(btn);
      addBox.appendChild(row);
      var tops = effTopics(sid);
      var sugg = allTopics().filter(function (x) { var y = tops[x.toLowerCase()]; return !y || y.status === "x"; }).slice(0, 14);
      if (sugg.length) {
        addBox.appendChild(el("div", "sugg-title", t("suggestions")));
        var chips = el("div", "kchips");
        sugg.forEach(function (x) {
          var c = it("button", "kchip add", "plus", null);
          c.appendChild(el("span", "", x));
          c.type = "button";
          c.addEventListener("click", function () { addTopic(x); });
          chips.appendChild(c);
        });
        addBox.appendChild(chips);
      }
    };
    var fresh = null;
    function addTopic(title) {
      setTopic(sid, title, addStatus);
      fresh = title.toLowerCase();
      SB.haptic("success");
      drawAll();
    }
    function drawAll() {
      drawTopics();
      if (fresh) {
        var chip = Array.prototype.filter.call(groups.querySelectorAll(".kchip"), function (c) {
          return c.textContent.toLowerCase() === fresh;
        })[0];
        if (chip) chip.classList.add("new");
        fresh = null;
      }
      drawAdd();
      updateSave();
    }
    drawTopics();
    drawAdd();
    box.appendChild(tc);

    // ---- соседние ученики
    var idx = hub.st.indexOf(s);
    var navRow = el("div", "ed-nav");
    var prevS = hub.st[idx - 1], nextS = hub.st[idx + 1];
    var pb = it("button", "btn ghost", "prev", prevS ? prevS[1] : t("prevStudent"));
    pb.type = "button"; pb.disabled = !prevS;
    pb.addEventListener("click", function () { SB.haptic("select"); replaceSub(function () { editor(prevS[0]); }, "pop"); });
    var nb = it("button", "btn ghost", null, nextS ? nextS[1] : t("nextStudent"));
    nb.appendChild(SB.icon("next"));
    nb.type = "button"; nb.disabled = !nextS;
    nb.addEventListener("click", function () { SB.haptic("select"); replaceSub(function () { editor(nextS[0]); }, "push"); });
    navRow.appendChild(pb);
    navRow.appendChild(nb);
    box.appendChild(navRow);
    nav = function () { editor(sid, focus); };
    updateSave();
    stagger(box);
    if (focus === "topics") setTimeout(function () {
      tc.scrollIntoView({ behavior: SB.reduced ? "auto" : "smooth", block: "start" });
    }, 350);
  }

  // Шторка темы: перенести в «Выучил» / «Не понял» или убрать
  function topicSheet(sid, x, onChange) {
    SB.haptic("select");
    SB.sheet(x.title, function (body, close) {
      [["learned", "checkCircle", t("moveToLearned")], ["unclear", "help", t("moveToUnclear")], ["x", "close", t("removeTopic")]]
        .forEach(function (o) {
          if (o[0] === x.status) return;
          var b = it("button", "choice", o[1], o[2]);
          b.type = "button";
          b.addEventListener("click", function () {
            setTopic(sid, x.title, o[0]);
            SB.haptic(o[0] === "x" ? "warning" : "success");
            close();
            if (onChange) onChange();
          });
          body.appendChild(b);
        });
      var c = el("button", "btn ghost", t("cancel"));
      c.type = "button";
      c.addEventListener("click", close);
      body.appendChild(c);
    });
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
    draw();
  }

  // ---------------------------------------------------------------- карта

  function mapTab() {
    var box = screen("map");
    var head = el("div", "tabhead");
    head.appendChild(el("h1", "", t("tabMap")));
    head.appendChild(el("span", "group-chip", hub.g));
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
        path.appendChild(el("div", "fork-banner", t("fork")));
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
      var pic = el("span", "picon");
      if (state === "done") pic.appendChild(SB.icon("check"));
      else if (state === "current") pic.appendChild(SB.icon("starFill"));
      else pic.textContent = String(i + 1);
      btn.appendChild(pic);
      if (state === "current") btn.appendChild(el("span", "pulse"));
      btn.addEventListener("click", function () { SB.haptic("select"); sub(function () { stationSheet(s[0]); }); });
      node.appendChild(btn);
      var label = el("div", "plabel");
      label.appendChild(el("b", "", s[1]));
      if (s[3]) label.appendChild(el("small", "", s[3]));
      if (state === "current") label.appendChild(it("span", "flag-chip", "flag", t("groupHere")));
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
      var mv = it("button", "btn ghost", "users", t("moveGroupHere"));
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
    head.appendChild(el("span", "group-chip", hub.g));
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
    var bi = el("span", "big-ic");
    bi.appendChild(SB.icon(now !== null && prev !== null && now < prev ? "trendDown" : "trendUp"));
    lvl.appendChild(bi);
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
    two.appendChild(peopleCard(t("growing"), up, "good"));
    two.appendChild(peopleCard(t("needHelp"), down, "bad"));
    box.appendChild(two);
    box.appendChild(exportRow());
    stagger(box);
  }

  // Excel с отчётами группы за эту и прошлую неделю — бот пришлёт файл в чат
  function exportRow() {
    var b = el("button", "action-row violet");
    b.type = "button";
    b.style.marginTop = "12px";
    var qi = el("span", "qicon");
    qi.appendChild(SB.icon("download"));
    b.appendChild(qi);
    var tx = el("span", "grow");
    tx.appendChild(el("b", "", t("exportTitle")));
    tx.appendChild(el("span", "sub", t("exportSub")));
    b.appendChild(tx);
    b.appendChild(SB.icon("chevron"));
    b.addEventListener("click", function () {
      SB.haptic("success");
      SB.send({ v: 1, u: SB.uuid(), t: "export", g: hub.gid });
    });
    return b;
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
      b.addEventListener("click", function () { openProfile(x.s[0], b); });
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
        text.appendChild(el("span", "", (s ? s[1] : "") + " — " + h[2]));
        if (h[3]) text.appendChild(el("span", "sub", t("why") + ": " + h[3]));
        b.appendChild(text);
        var mk = el("span", "mark");
        if (marked[h[0]]) mk.appendChild(SB.icon("check"));
        b.appendChild(mk);
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
      var ib = el("span", "big-ic");
      ib.appendChild(SB.icon("mail"));
      intro.appendChild(ib);
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
        tx.appendChild(el("span", "", s[1] + (starred(s[0]) ? " ★" : "")));
        tx.appendChild(el("span", "sub", ok ? t("cardsReady") : !s[4] ? t("cardsNoConsent") : t("cardsNoReport")));
        b.appendChild(tx);
        if (ok) {
          var mk2 = el("span", "mark");
          if (chosen[s[0]]) mk2.appendChild(SB.icon("check"));
          b.appendChild(mk2);
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

  document.getElementById("hubback").addEventListener("click", function () { SB.hubHome(); });

  SB.load(DEMO, function (d, isDemo) {
    hub = d;
    hub.st = hub.st || [];
    hub.wk = hub.wk || { q: [], a: {}, c: {}, sr: {} };
    demo = isDemo;
    SB.demoMode = isDemo;
    hub.pf = hub.pf || {};
    hub.cr = hub.cr || [];
    pfLoadDraft();
    document.title = t("journal") + " " + hub.g;
    var startTab = (/[?&]tab=(\w+)/.exec(location.search) || [])[1];
    go(["home", "students", "skills", "map", "stats"].indexOf(startTab) >= 0 ? startTab : "home", "none");
  });
})();
