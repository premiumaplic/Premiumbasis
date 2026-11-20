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
        "ru": "{header}\n\nКнопки внизу. Формы посещаемости и отчётов появятся на следующем этапе.",
        "uz": "{header}\n\nTugmalar pastda. Davomat va hisobot shakllari keyingi bosqichda paydo boʻladi.",
    },
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
