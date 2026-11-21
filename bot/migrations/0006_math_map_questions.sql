-- Версия 2: карта математики, разделы и описания станций, новые вопросы недели,
-- «звезда недели», выключатель посещаемости.
-- Узбекские тексты — ЧЕРНОВИК на проверку владельцу.

-- ---------------------------------------------------------------- станции: разделы и описания
-- section — заголовок участка карты («1–4 класс»), about — что проходят на станции (до 60 знаков).
ALTER TABLE stages ADD COLUMN section_ru TEXT NOT NULL DEFAULT '';
ALTER TABLE stages ADD COLUMN section_uz TEXT NOT NULL DEFAULT '';
ALTER TABLE stages ADD COLUMN about_ru   TEXT NOT NULL DEFAULT '';
ALTER TABLE stages ADD COLUMN about_uz   TEXT NOT NULL DEFAULT '';

UPDATE stages SET section_ru = 'Для детей',          section_uz = 'Bolalar uchun'      WHERE subject = 'en' AND branch = 'kids';
UPDATE stages SET section_ru = 'Общий английский',   section_uz = 'Umumiy ingliz tili' WHERE subject = 'en' AND branch = 'main';
UPDATE stages SET section_ru = 'Экзамен CEFR',       section_uz = 'CEFR imtihoni'      WHERE subject = 'en' AND branch = 'cefr';
UPDATE stages SET section_ru = 'Экзамен IELTS',      section_uz = 'IELTS imtihoni'     WHERE subject = 'en' AND branch = 'ielts';

UPDATE stages SET about_ru = 'Буквы, звуки и первые слова',        about_uz = 'Harflar, tovushlar va ilk soʻzlar'      WHERE subject = 'en' AND code = 'starter';
UPDATE stages SET about_ru = 'Простые фразы и базовая грамматика', about_uz = 'Oddiy iboralar va asosiy grammatika'    WHERE subject = 'en' AND code = 'roundup1';
UPDATE stages SET about_ru = 'Времена Present и Past',             about_uz = 'Present va Past zamonlari'              WHERE subject = 'en' AND code = 'roundup2';
UPDATE stages SET about_ru = 'Future, сравнения, модальные глаголы', about_uz = 'Future, qiyoslash, modal feʼllar'     WHERE subject = 'en' AND code = 'roundup3';
UPDATE stages SET about_ru = 'Сложные времена и пассив',           about_uz = 'Murakkab zamonlar va majhul nisbat'     WHERE subject = 'en' AND code = 'roundup4';
UPDATE stages SET about_ru = 'Общение на простые темы',            about_uz = 'Oddiy mavzularda muloqot'               WHERE subject = 'en' AND code = 'a1';
UPDATE stages SET about_ru = 'Рассказ о себе, планы и опыт',       about_uz = 'Oʻzi, rejalari va tajribasi haqida'     WHERE subject = 'en' AND code = 'a2';
UPDATE stages SET about_ru = 'Свободный разговор на бытовые темы', about_uz = 'Maishiy mavzularda erkin suhbat'        WHERE subject = 'en' AND code = 'b1';
UPDATE stages SET about_ru = 'Уверенный английский, сложные тексты', about_uz = 'Ishonchli ingliz tili, murakkab matnlar' WHERE subject = 'en' AND code = 'b2';
UPDATE stages SET about_ru = 'Формат экзамена CEFR',               about_uz = 'CEFR imtihoni formati'                  WHERE subject = 'en' AND code = 'precefr';
UPDATE stages SET about_ru = 'Подготовка и сдача CEFR',            about_uz = 'CEFRga tayyorgarlik va topshirish'      WHERE subject = 'en' AND code = 'cefr';
UPDATE stages SET about_ru = 'Формат экзамена IELTS',              about_uz = 'IELTS imtihoni formati'                 WHERE subject = 'en' AND code = 'preielts';
UPDATE stages SET about_ru = 'Подготовка и сдача IELTS',           about_uz = 'IELTSga tayyorgarlik va topshirish'     WHERE subject = 'en' AND code = 'ielts';

-- ---------------------------------------------------------------- карта математики
-- 11 станций (по классам) в трёх разделах. Переход — по решению учителя (без экзамена и дат);
-- владелец может позже задать длительность и экзамены.
UPDATE subjects SET has_map = 1 WHERE code = 'math';

INSERT INTO stages (subject, code, name_ru, name_uz, sort, months, months_max, branch, exam_transition,
                    section_ru, section_uz, about_ru, about_uz) VALUES
    ('math', 'g1',  '1 класс',  '1-sinf',  10, NULL, NULL, 'main', 0, '1–4 класс', '1–4-sinflar',
     'Счёт до 100, сложение и вычитание',        '100 gacha sanash, qoʻshish va ayirish'),
    ('math', 'g2',  '2 класс',  '2-sinf',  20, NULL, NULL, 'main', 0, '1–4 класс', '1–4-sinflar',
     'Сложение и вычитание в столбик, начало умножения', 'Ustun usulida qoʻshish va ayirish, koʻpaytirish boshlanishi'),
    ('math', 'g3',  '3 класс',  '3-sinf',  30, NULL, NULL, 'main', 0, '1–4 класс', '1–4-sinflar',
     'Таблица умножения и деление',              'Karra jadvali va boʻlish'),
    ('math', 'g4',  '4 класс',  '4-sinf',  40, NULL, NULL, 'main', 0, '1–4 класс', '1–4-sinflar',
     'Многозначные числа, действия в столбик',   'Koʻp xonali sonlar, ustun usulidagi amallar'),
    ('math', 'g5',  '5 класс',  '5-sinf',  50, NULL, NULL, 'main', 0, '5–8 класс', '5–8-sinflar',
     'Натуральные числа, обыкновенные дроби',    'Natural sonlar, oddiy kasrlar'),
    ('math', 'g6',  '6 класс',  '6-sinf',  60, NULL, NULL, 'main', 0, '5–8 класс', '5–8-sinflar',
     'Десятичные дроби, проценты, пропорции',    'Oʻnli kasrlar, foizlar, proporsiyalar'),
    ('math', 'g7',  '7 класс',  '7-sinf',  70, NULL, NULL, 'main', 0, '5–8 класс', '5–8-sinflar',
     'Отрицательные числа, выражения, уравнения', 'Manfiy sonlar, ifodalar, tenglamalar'),
    ('math', 'g8',  '8 класс',  '8-sinf',  80, NULL, NULL, 'main', 0, '5–8 класс', '5–8-sinflar',
     'Степени, корни, квадратные уравнения',     'Darajalar, ildizlar, kvadrat tenglamalar'),
    ('math', 'g9',  '9 класс',  '9-sinf',  90, NULL, NULL, 'main', 0, '9–11 класс', '9–11-sinflar',
     'Функции, неравенства, прогрессии',         'Funksiyalar, tengsizliklar, progressiyalar'),
    ('math', 'g10', '10 класс', '10-sinf', 100, NULL, NULL, 'main', 0, '9–11 класс', '9–11-sinflar',
     'Тригонометрия, степени и логарифмы',       'Trigonometriya, darajalar va logarifmlar'),
    ('math', 'g11', '11 класс', '11-sinf', 110, NULL, NULL, 'main', 0, '9–11 класс', '9–11-sinflar',
     'Производная, интеграл, подготовка к экзаменам', 'Hosila, integral, imtihonlarga tayyorgarlik');

-- ---------------------------------------------------------------- вопросы недели
-- optional = 1: учитель может пропустить вопрос («не оценивал на этой неделе»).
ALTER TABLE questions ADD COLUMN optional INTEGER NOT NULL DEFAULT 0;

INSERT INTO questions (subjects, sort, code, optional,
    text_ru, opt0_ru, opt1_ru, opt2_ru, opt3_ru,
    text_uz, opt0_uz, opt1_uz, opt2_uz, opt3_uz) VALUES
('en,ar,ru,ko', 52, 'listening', 1,
 'Аудирование', 'не понимает на слух', 'понимает отдельные слова', 'понимает основное', 'понимает почти всё',
 'Tinglab tushunish', 'eshitib tushunmaydi', 'alohida soʻzlarni tushunadi', 'asosiy mazmunni tushunadi', 'deyarli hammasini tushunadi'),
('en,ar,ru,ko', 53, 'reading', 1,
 'Чтение', 'не читает', 'читает с трудом', 'читает с ошибками', 'читает бегло и понимает',
 'Oʻqish', 'oʻqimaydi', 'qiynalib oʻqiydi', 'xatolar bilan oʻqiydi', 'ravon oʻqiydi va tushunadi'),
('en,ar,ru,ko', 54, 'writing', 1,
 'Письмо', 'не пишет', 'много ошибок', 'небольшие ошибки', 'пишет грамотно',
 'Yozish', 'yozmaydi', 'koʻp xato qiladi', 'kichik xatolar bor', 'savodli yozadi'),
('math', 56, 'mental', 1,
 'Устный счёт', 'считает с большим трудом', 'медленно, с ошибками', 'уверенно, иногда ошибается', 'быстро и точно',
 'Ogʻzaki hisob', 'juda qiynaladi', 'sekin, xatolar bilan', 'ishonchli, baʼzan xato qiladi', 'tez va aniq'),
('math', 57, 'problems', 1,
 'Решение задач', 'не может начать', 'решает с помощью', 'решает с ошибками', 'решает самостоятельно',
 'Masala yechish', 'boshlay olmaydi', 'yordam bilan yechadi', 'xatolar bilan yechadi', 'mustaqil yechadi'),
('math', 58, 'neatness', 1,
 'Оформление тетради', 'небрежно', 'есть помарки', 'аккуратно', 'образцово',
 'Daftar yuritish', 'beparvo', 'chizilgan joylar bor', 'toza', 'namunali');

-- ---------------------------------------------------------------- звезда недели
-- Учитель может отметить ученика «звездой недели» — на карточке появится значок.
ALTER TABLE weekly_reports ADD COLUMN star INTEGER NOT NULL DEFAULT 0;

-- ---------------------------------------------------------------- настройки
-- Посещаемость ведётся на другом сайте центра: по умолчанию выключена
-- (не видна учителям, на карточке и в сводке). Владелец включит в «Настройках».
INSERT INTO settings (key, value) VALUES ('attendance_on', '0');
