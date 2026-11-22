-- Версия 2.2: профиль ученика — рейтинг по критериям, выученные и непонятные темы; саппорт-учитель.

-- Роль учителя: 'teacher' — свои группы, 'support' — саппорт-учитель: видит все группы центра
-- и работает в любой из них как учитель. Значение проверяет код (repo.ROLES).
ALTER TABLE teachers ADD COLUMN role TEXT NOT NULL DEFAULT 'teacher';

-- Критерии рейтинга ученика (оценка 1–10). subjects: '*' или коды через запятую.
-- Узбекские названия — ЧЕРНОВИК, на проверку владельцу.
CREATE TABLE criteria (
    id       INTEGER PRIMARY KEY,
    subjects TEXT    NOT NULL,
    sort     INTEGER NOT NULL,
    name_ru  TEXT    NOT NULL,
    name_uz  TEXT    NOT NULL,
    active   INTEGER NOT NULL DEFAULT 1
);

INSERT INTO criteria (subjects, sort, name_ru, name_uz) VALUES
    ('en,ar,ru,ko', 10, 'Listening · Аудирование', 'Listening · Tinglab tushunish'),
    ('en,ar,ru,ko', 20, 'Reading · Чтение',        'Reading · Oʻqish'),
    ('en,ar,ru,ko', 30, 'Writing · Письмо',        'Writing · Yozish'),
    ('en,ar,ru,ko', 40, 'Speaking · Говорение',    'Speaking · Gapirish'),
    ('en,ar,ru,ko', 50, 'Grammar · Грамматика',    'Grammar · Grammatika'),
    ('en,ar,ru,ko', 60, 'Vocabulary · Словарный запас', 'Vocabulary · Soʻz boyligi'),
    ('math',        10, 'Устный счёт',             'Ogʻzaki hisob'),
    ('math',        20, 'Вычисления',              'Hisoblash'),
    ('math',        30, 'Текстовые задачи',        'Matnli masalalar'),
    ('math',        40, 'Геометрия',               'Geometriya'),
    ('math',        50, 'Логика',                  'Mantiq'),
    ('math',        60, 'Аккуратность',            'Tartiblilik');

-- Оценка ученика по критериям: одна на ученика и предмет в день (повторная в тот же день заменяет).
CREATE TABLE assessments (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject    TEXT    NOT NULL,
    group_id   INTEGER NOT NULL REFERENCES groups(id),
    rated_on   TEXT    NOT NULL,
    rated_by   INTEGER NOT NULL,          -- Telegram ID учителя
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (student_id, subject, rated_on)
);

CREATE TABLE assessment_values (
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    criterion_id  INTEGER NOT NULL REFERENCES criteria(id),
    value         INTEGER NOT NULL CHECK (value BETWEEN 1 AND 10),
    PRIMARY KEY (assessment_id, criterion_id)
);

-- Темы ученика: выучил ('learned') или не понял ('unclear'). Одна строка на тему.
CREATE TABLE student_topics (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject    TEXT    NOT NULL,
    title      TEXT    NOT NULL,
    status     TEXT    NOT NULL CHECK (status IN ('learned', 'unclear')),
    updated_on TEXT    NOT NULL,
    updated_by INTEGER NOT NULL,          -- Telegram ID учителя
    UNIQUE (student_id, subject, title)
);
CREATE INDEX student_topics_student ON student_topics (student_id, subject);

-- История тем уроков группы (из формы «Тема урока») — подсказки, какие темы отметить ученикам.
CREATE TABLE topic_log (
    id       INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    title    TEXT    NOT NULL,
    set_on   TEXT    NOT NULL
);
CREATE INDEX topic_log_group ON topic_log (group_id, id);

-- Текущие темы групп — первая запись истории
INSERT INTO topic_log (group_id, title, set_on)
    SELECT id, current_topic, date('now') FROM groups WHERE current_topic IS NOT NULL AND current_topic != '';

-- Подсказка «Повторите непонятные темы»: со скольких непонятных тем
INSERT INTO settings (key, value) VALUES ('hint_unclear_topics', '3');
