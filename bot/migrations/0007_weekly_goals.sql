-- Версия 2.1: цель ученика на следующую неделю (выбирается в недельном отчёте, видна родителю на карточке).
-- Список целей — ЧЕРНОВИК, владелец поменяет в «📚 Тексты → 🎯 Цели на неделю».
-- subjects: '*' — для всех предметов, иначе список кодов через запятую.

CREATE TABLE goals (
    id       INTEGER PRIMARY KEY,
    subjects TEXT    NOT NULL DEFAULT '*',
    sort     INTEGER NOT NULL,
    text_ru  TEXT    NOT NULL,
    text_uz  TEXT    NOT NULL,
    active   INTEGER NOT NULL DEFAULT 1
);

INSERT INTO goals (subjects, sort, text_ru, text_uz) VALUES
    ('*',           10, 'Делать домашнее задание вовремя',  'Uy vazifasini oʻz vaqtida bajarish'),
    ('*',           20, 'Быть активнее на уроке',           'Darsda faolroq boʻlish'),
    ('*',           30, 'Аккуратно вести тетрадь',          'Daftarni tartibli yuritish'),
    ('en,ar,ru,ko', 40, 'Учить по 10 новых слов в день',    'Har kuni 10 ta yangi soʻz yodlash'),
    ('en,ar,ru,ko', 50, 'Читать по 15 минут в день',        'Har kuni 15 daqiqa oʻqish'),
    ('en,ar,ru,ko', 60, 'Слушать аудио на языке',           'Shu tilda audio tinglash'),
    ('en,ar,ru,ko', 70, 'Повторить грамматику темы',        'Mavzu grammatikasini takrorlash'),
    ('en,ar,ru,ko', 80, 'Больше говорить на уроке',         'Darsda koʻproq gapirish'),
    ('en,ar,ru,ko', 90, 'Писать короткий текст каждый день', 'Har kuni qisqa matn yozish'),
    ('math',        40, 'Повторить таблицу умножения',      'Karra jadvalini takrorlash'),
    ('math',        50, 'Решать по 5 задач в день',         'Har kuni 5 ta masala yechish'),
    ('math',        60, 'Тренировать устный счёт',          'Ogʻzaki hisobni mashq qilish'),
    ('math',        70, 'Повторить дроби',                  'Kasrlarni takrorlash'),
    ('math',        80, 'Проверять своё решение',           'Oʻz yechimini tekshirish');

-- 0 — цель не выбрана
ALTER TABLE weekly_reports ADD COLUMN goal_id INTEGER NOT NULL DEFAULT 0;
