-- Начальные данные: предметы, станции карты английского, вопросы недели, настройки.
-- Узбекские тексты — ЧЕРНОВИК на проверку владельцу (questions.uz_checked = 0).

INSERT INTO subjects (code, name_ru, name_uz, has_map, sort) VALUES
    ('en',   'Английский',  'Ingliz tili',  1, 1),
    ('ar',   'Арабский',    'Arab tili',    0, 2),
    ('ru',   'Русский',     'Rus tili',     0, 3),
    ('ko',   'Корейский',   'Koreys tili',  0, 4),
    ('math', 'Математика',  'Matematika',   0, 5);

-- Карта английского. Проходной и максимальный балл задаёт владелец (сейчас пусто).
-- exam_transition у Pre-CEFR, CEFR, Pre-IELTS, IELTS — уточнить у владельца.
INSERT INTO stages (subject, code, name_ru, name_uz, sort, months, months_max, branch, exam_transition) VALUES
    ('en', 'starter',   'Starter',        'Starter',        10, NULL, NULL, 'kids',  0),
    ('en', 'roundup1',  'Roundup 1',      'Roundup 1',      20, NULL, NULL, 'kids',  0),
    ('en', 'roundup2',  'Roundup 2',      'Roundup 2',      30, NULL, NULL, 'kids',  0),
    ('en', 'roundup3',  'Roundup 3',      'Roundup 3',      40, NULL, NULL, 'kids',  0),
    ('en', 'roundup4',  'Roundup 4',      'Roundup 4',      50, NULL, NULL, 'kids',  0),
    ('en', 'a1',        'Курс A1',        'A1 kursi',       60, 2,    NULL, 'main',  1),
    ('en', 'a2',        'Курс A2',        'A2 kursi',       70, 2,    NULL, 'main',  1),
    ('en', 'b1',        'Курс B1',        'B1 kursi',       80, 2,    NULL, 'main',  1),
    ('en', 'b2',        'Курс B2',        'B2 kursi',       90, 2,    NULL, 'main',  1),
    ('en', 'precefr',   'Pre-CEFR',       'Pre-CEFR',      100, 2,    NULL, 'cefr',  0),
    ('en', 'cefr',      'CEFR',           'CEFR',          110, 3,    5,    'cefr',  0),
    ('en', 'preielts',  'Pre-IELTS',      'Pre-IELTS',     100, 2,    NULL, 'ielts', 0),
    ('en', 'ielts',     'IELTS',          'IELTS',         110, 3,    5,    'ielts', 0);

-- Вопросы недели. Порядок sort: языки 1–6, математика 1, 2, 7, 6.
INSERT INTO questions (subjects, sort,
    text_ru, opt0_ru, opt1_ru, opt2_ru, opt3_ru,
    text_uz, opt0_uz, opt1_uz, opt2_uz, opt3_uz) VALUES
('*', 10,
 'Домашнее задание', 'не сделано', 'частично', 'сделано с ошибками', 'сделано хорошо',
 'Uy vazifasi', 'bajarilmagan', 'qisman bajarilgan', 'xatolar bilan bajarilgan', 'yaxshi bajarilgan'),
('*', 20,
 'Работа на уроке', 'пассивен', 'отвечает, когда спросят', 'активно участвует', 'помогает другим',
 'Darsdagi faollik', 'passiv', 'soʻralganda javob beradi', 'faol qatnashadi', 'boshqalarga yordam beradi'),
('en,ar,ru,ko', 30,
 'Новые слова', 'не выучены', 'выучена часть', 'выучено большинство', 'выучены все',
 'Yangi soʻzlar', 'yodlanmagan', 'bir qismi yodlangan', 'koʻpchiligi yodlangan', 'hammasi yodlangan'),
('en,ar,ru,ko', 40,
 'Грамматика темы', 'не понял', 'понимает с подсказкой', 'применяет с ошибками', 'применяет уверенно',
 'Mavzu grammatikasi', 'tushunmagan', 'yordam bilan tushunadi', 'xatolar bilan qoʻllaydi', 'ishonch bilan qoʻllaydi'),
('en,ar,ru,ko', 50,
 'Говорение', 'молчит', 'отдельные слова', 'простые фразы', 'свободно для своего уровня',
 'Gapirish', 'jim turadi', 'alohida soʻzlar', 'oddiy iboralar', 'oʻz darajasida erkin'),
('math', 55,
 'Понимание темы', 'не понял', 'понимает с подсказкой', 'решает с ошибками', 'решает уверенно',
 'Mavzuni tushunish', 'tushunmagan', 'yordam bilan tushunadi', 'xatolar bilan yechadi', 'ishonch bilan yechadi'),
('*', 60,
 'Дисциплина', 'мешал', 'отвлекался', 'нормально', 'образцово',
 'Intizom', 'xalaqit bergan', 'chalgʻigan', 'yaxshi', 'namunali');

-- Настройки. Пороги подсказок — стартовые предположения, владелец подстроит через месяц.
INSERT INTO settings (key, value) VALUES
    ('center_name',          ''),
    ('reminder_day',         '6'),      -- 1 = понедельник ... 6 = суббота, 7 = воскресенье
    ('reminder_time',        '18:00'),  -- не позже 21:00
    ('backup_time',          '21:30'),
    ('rate_limit_per_min',   '30'),
    ('url_safe_length',      '1800'),
    ('hint_absent_streak',   '2'),
    ('hint_absent_month',    '3'),
    ('hint_late_2weeks',     '3'),
    ('hint_homework_weeks',  '2'),
    ('hint_drop_steps',      '2'),
    ('hint_exam_weeks',      '3'),
    ('hint_growth_weeks',    '3');
