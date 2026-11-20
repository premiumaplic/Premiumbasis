"""Тексты интерфейса учителя на русском и узбекском (латиница).

Узбекские тексты — ЧЕРНОВИК, на проверку владельцу.
Сообщения владельцу (администратору) — только на русском, они прямо в коде меню.
"""

TEXTS = {
    "no_access": {
        "ru": "Нет доступа.\nВаш Telegram ID: {id}\nПередайте этот номер владельцу центра.",
        "uz": "Ruxsat yoʻq.\nSizning Telegram ID raqamingiz: {id}\nUshbu raqamni markaz egasiga yuboring.",
    },
    "my_id": {
        "ru": "Ваш Telegram ID: {id}",
        "uz": "Sizning Telegram ID raqamingiz: {id}",
    },
    "hello_teacher": {
        "ru": "Здравствуйте, {name}! Выберите группу:",
        "uz": "Assalomu alaykum, {name}! Guruhni tanlang:",
    },
    "no_groups": {
        "ru": "Здравствуйте, {name}! У вас пока нет групп. Обратитесь к владельцу центра.",
        "uz": "Assalomu alaykum, {name}! Sizda hozircha guruh yoʻq. Markaz egasiga murojaat qiling.",
    },
    "group_chosen": {
        "ru": "{header}\n\nКнопки форм — внизу, под полем ввода.",
        "uz": "{header}\n\nShakl tugmalari — pastda, yozish maydoni ostida.",
    },
    "btn_attendance": {"ru": "✅ Посещаемость", "uz": "✅ Davomat"},
    "btn_weekly": {"ru": "📝 Недельный отчёт", "uz": "📝 Haftalik hisobot"},
    "btn_weekly_part": {"ru": "📝 Отчёт {i}/{n}", "uz": "📝 Hisobot {i}/{n}"},
    "btn_topic": {"ru": "📚 Тема", "uz": "📚 Mavzu"},
    "saved_att": {
        "ru": "Сохранено: посещаемость {group} за {date} — {n} учеников, опозданий {late}, пропусков {absent}.",
        "uz": "Saqlandi: {group} davomati, {date} — {n} oʻquvchi, kechikkan {late}, kelmagan {absent}.",
    },
    "saved_wk": {
        "ru": "Сохранено: недельный отчёт {group}, неделя {week} — {n} учеников.",
        "uz": "Saqlandi: {group} haftalik hisoboti, {week} haftasi — {n} oʻquvchi.",
    },
    "wk_all_done": {"ru": "Все ученики заполнены ✅", "uz": "Barcha oʻquvchilar toʻldirildi ✅"},
    "wk_left": {
        "ru": "Ещё не заполнены ({k}): {names}",
        "uz": "Hali toʻldirilmagan ({k}): {names}",
    },
    "saved_topic": {"ru": "Сохранено: тема {group} — {topic}", "uz": "Saqlandi: {group} mavzusi — {topic}"},
    "late_delivery": {
        "ru": "Получено {when}, сохранено.",
        "uz": "{when} qabul qilindi, saqlandi.",
    },
    "duplicate": {
        "ru": "Эти данные уже были сохранены — повтор не записан.",
        "uz": "Bu maʼlumotlar allaqachon saqlangan — takror yozilmadi.",
    },
    "skipped_foreign": {
        "ru": "Не сохранено для {k} учеников: их нет в этой группе (возможно, их перевели). Откройте форму заново.",
        "uz": "{k} oʻquvchi uchun saqlanmadi: ular bu guruhda emas (ehtimol, koʻchirilgan). Shaklni qayta oching.",
    },
    "form_rejected": {
        "ru": "Форма не сохранена: {reason}",
        "uz": "Shakl saqlanmadi: {reason}",
    },
    "err_bad_data": {"ru": "данные повреждены.", "uz": "maʼlumotlar buzilgan."},
    "err_not_your_group": {"ru": "эта группа вам не назначена.", "uz": "bu guruh sizga biriktirilmagan."},
    "err_date": {
        "ru": "дата урока — не раньше чем 7 дней назад и не в будущем.",
        "uz": "dars sanasi — 7 kundan oldin emas va kelajakda emas.",
    },
    "err_week": {"ru": "можно заполнить только текущую или прошлую неделю.",
                 "uz": "faqat joriy yoki oʻtgan haftani toʻldirish mumkin."},
    "err_questions": {"ru": "вопросы недели изменились — откройте форму заново.",
                      "uz": "hafta savollari oʻzgardi — shaklni qayta oching."},
    "err_no_students": {"ru": "ни один ученик не из этой группы.", "uz": "birorta oʻquvchi bu guruhdan emas."},
    "btn_exam": {"ru": "🎓 Экзамен", "uz": "🎓 Imtihon"},
    "btn_cards": {"ru": "📤 Карточки для родителей", "uz": "📤 Ota-onalar uchun kartalar"},
    "saved_exam": {
        "ru": "Сохранено: экзамен {group}, {stage} — сдали {passed}, повтор {repeat}.",
        "uz": "Saqlandi: {group} imtihoni, {stage} — topshirdi {passed}, qayta {repeat}.",
    },
    "saved_decision": {
        "ru": "Сохранено: решение по станции {stage} ({group}) — переходят {passed}, остаются {repeat}.",
        "uz": "Saqlandi: {stage} bosqichi boʻyicha qaror ({group}) — oʻtadi {passed}, qoladi {repeat}.",
    },
    "group_advanced": {"ru": "Группа переходит на станцию {stage}.", "uz": "Guruh {stage} bosqichiga oʻtadi."},
    "repeat_names": {
        "ru": "Остаются на повтор: {names}. Владельцу стоит решить, в какую группу их перевести.",
        "uz": "Qayta oʻqiydi: {names}. Ularni qaysi guruhga oʻtkazishni markaz egasi hal qiladi.",
    },
    "fork_wait": {
        "ru": "Сдали, но путь не выбран: {names}. Выберите CEFR или IELTS (владелец: карточка ученика → Станция).",
        "uz": "Topshirdi, lekin yoʻl tanlanmagan: {names}. CEFR yoki IELTSni tanlang (markaz egasi orqali).",
    },
    "other_stage": {
        "ru": "Не учтены (стоят на другой станции): {names}.",
        "uz": "Hisobga olinmadi (boshqa bosqichda): {names}.",
    },
    "err_scores_unset": {
        "ru": "для этой станции владелец ещё не задал проходной и максимальный балл.",
        "uz": "bu bosqich uchun markaz egasi oʻtish va maksimal ballni hali kiritmagan.",
    },
    "err_reason": {
        "ru": "если решение отличается от балла, укажите причину.",
        "uz": "qaror balldan farq qilsa, sababini yozing.",
    },
    "err_stage": {"ru": "станция группы изменилась — откройте форму заново.",
                  "uz": "guruh bosqichi oʻzgardi — shaklni qayta oching."},
    "cards_none": {
        "ru": "Карточек нет: за неделю {week} ещё нет ни одного заполненного отчёта.",
        "uz": "Kartalar yoʻq: {week} haftasi uchun hali birorta hisobot toʻldirilmagan.",
    },
    "cards_caption": {"ru": "{name} — неделя {week}", "uz": "{name} — {week} haftasi"},
    "cards_done": {"ru": "Готово: карточек {n}. Перешлите каждую родителю.", "uz": "Tayyor: {n} ta karta. Har birini ota-onaga yuboring."},
    "cards_skipped": {"ru": "Без карточки:", "uz": "Kartasiz:"},
    "cards_no_report": {"ru": "нет отчёта за неделю", "uz": "hafta hisoboti yoʻq"},
    "cards_no_consent": {"ru": "нет отметки о согласии родителя", "uz": "ota-ona roziligi belgilanmagan"},
    "cards_wait": {"ru": "Рисую карточки: {n} шт…", "uz": "Kartalar tayyorlanmoqda: {n} ta…"},
    "choose_group_first": {"ru": "Сначала выберите группу: /start", "uz": "Avval guruhni tanlang: /start"},
    "reminder": {
        "ru": "⏰ Напоминание: нет недельного отчёта за неделю {week}.",
        "uz": "⏰ Eslatma: {week} haftasi uchun haftalik hisobot yoʻq.",
    },
    "reminder_group": {"ru": "{group}: {names} ({k} из {total})", "uz": "{group}: {names} ({total} tadan {k})"},
    "not_your_group": {
        "ru": "Эта группа вам не назначена.",
        "uz": "Bu guruh sizga biriktirilmagan.",
    },
    "btn_other_group": {"ru": "🔁 Другая группа", "uz": "🔁 Boshqa guruh"},
    "press_button": {
        "ru": "Нажмите /start, чтобы выбрать группу.",
        "uz": "Guruhni tanlash uchun /start bosing.",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    variants = TEXTS[key]
    text = variants.get(lang) or variants["ru"]
    return text.format(**kwargs) if kwargs else text


def all_variants(key: str) -> set[str]:
    return set(TEXTS[key].values())
