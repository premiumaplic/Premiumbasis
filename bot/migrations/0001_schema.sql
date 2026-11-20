-- Основная схема базы. Менять только новыми пронумерованными файлами миграций.

CREATE TABLE teachers (
    id         INTEGER PRIMARY KEY,
    tg_id      INTEGER NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    lang       TEXT    NOT NULL DEFAULT 'ru' CHECK (lang IN ('ru', 'uz')),
    active     INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE subjects (
    code    TEXT PRIMARY KEY,
    name_ru TEXT    NOT NULL,
    name_uz TEXT    NOT NULL,
    has_map INTEGER NOT NULL DEFAULT 0,
    sort    INTEGER NOT NULL DEFAULT 0
);

-- Станции карты. Длительность может быть пустой (переход по решению учителя).
CREATE TABLE stages (
    id              INTEGER PRIMARY KEY,
    subject         TEXT    NOT NULL REFERENCES subjects(code),
    code            TEXT    NOT NULL,
    name_ru         TEXT    NOT NULL,
    name_uz         TEXT    NOT NULL,
    sort            INTEGER NOT NULL,
    months          INTEGER,            -- длительность, мес. (или нижняя граница диапазона)
    months_max      INTEGER,            -- верхняя граница диапазона (CEFR, IELTS: 3–5)
    branch          TEXT    NOT NULL CHECK (branch IN ('kids', 'main', 'cefr', 'ielts')),
    exam_transition INTEGER NOT NULL DEFAULT 0,  -- 1: переход решает экзамен
    pass_score      REAL,               -- проходной балл (задаёт владелец)
    max_score       REAL,               -- максимальный балл (задаёт владелец)
    UNIQUE (subject, code)
);

CREATE TABLE groups (
    id            INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    subject       TEXT    NOT NULL REFERENCES subjects(code),
    teacher_id    INTEGER REFERENCES teachers(id),
    stage_id      INTEGER REFERENCES stages(id),
    start_date    TEXT    NOT NULL,     -- ГГГГ-ММ-ДД
    weekdays      TEXT    NOT NULL DEFAULT '',  -- '1,3,5' (1 = понедельник)
    lesson_time   TEXT    NOT NULL DEFAULT '',  -- '15:00'
    current_topic TEXT    NOT NULL DEFAULT '',
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX groups_teacher ON groups(teacher_id, active);

-- Только то, что нужно для отчётов. Никаких телефонов, адресов, дат рождения.
CREATE TABLE students (
    id         INTEGER PRIMARY KEY,
    full_name  TEXT    NOT NULL,
    card_lang  TEXT    NOT NULL DEFAULT 'ru' CHECK (card_lang IN ('ru', 'uz')),
    consent    INTEGER NOT NULL DEFAULT 0,  -- согласие родителя (бумага в центре)
    active     INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- История учёбы в группах: при переводе старая запись закрывается датой.
CREATE TABLE enrollments (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    group_id   INTEGER NOT NULL REFERENCES groups(id),
    date_from  TEXT    NOT NULL,
    date_to    TEXT
);
CREATE INDEX enrollments_group ON enrollments(group_id, date_to);
CREATE INDEX enrollments_student ON enrollments(student_id, date_to);

-- Где ученик на карте. Текущая станция — запись со status = 'current'.
CREATE TABLE student_stage (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject    TEXT    NOT NULL REFERENCES subjects(code),
    stage_id   INTEGER NOT NULL REFERENCES stages(id),
    date_from  TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'current' CHECK (status IN ('current', 'done', 'left')),
    path       TEXT    CHECK (path IN ('cefr', 'ielts'))
);
CREATE INDEX student_stage_cur ON student_stage(student_id, subject, status);

CREATE TABLE attendance (
    id          INTEGER PRIMARY KEY,
    student_id  INTEGER NOT NULL REFERENCES students(id),
    group_id    INTEGER NOT NULL REFERENCES groups(id),
    lesson_date TEXT    NOT NULL,
    status      TEXT    NOT NULL CHECK (status IN ('present', 'late', 'absent', 'excused')),
    marked_by   INTEGER NOT NULL,       -- Telegram ID
    marked_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (student_id, group_id, lesson_date)
);

CREATE TABLE questions (
    id        INTEGER PRIMARY KEY,
    subjects  TEXT    NOT NULL DEFAULT '*',  -- '*' = все предметы, иначе 'en,ar,ru,ko'
    sort      INTEGER NOT NULL,
    text_ru   TEXT NOT NULL, opt0_ru TEXT NOT NULL, opt1_ru TEXT NOT NULL, opt2_ru TEXT NOT NULL, opt3_ru TEXT NOT NULL,
    text_uz   TEXT NOT NULL, opt0_uz TEXT NOT NULL, opt1_uz TEXT NOT NULL, opt2_uz TEXT NOT NULL, opt3_uz TEXT NOT NULL,
    uz_checked INTEGER NOT NULL DEFAULT 0,  -- 0: узбекский текст — черновик, на проверку владельцу
    active    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE weekly_reports (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    group_id   INTEGER NOT NULL REFERENCES groups(id),
    week_start TEXT    NOT NULL,        -- понедельник недели
    comment    TEXT    NOT NULL DEFAULT '',
    phrases    TEXT    NOT NULL DEFAULT '',
    created_by INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (student_id, group_id, week_start)
);

CREATE TABLE weekly_answers (
    report_id   INTEGER NOT NULL REFERENCES weekly_reports(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    value       INTEGER NOT NULL CHECK (value BETWEEN 0 AND 3),
    PRIMARY KEY (report_id, question_id)
);

CREATE TABLE exams (
    id         INTEGER PRIMARY KEY,
    group_id   INTEGER NOT NULL REFERENCES groups(id),
    stage_id   INTEGER NOT NULL REFERENCES stages(id),
    exam_date  TEXT    NOT NULL,
    pass_score REAL    NOT NULL,
    max_score  REAL    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE exam_results (
    id         INTEGER PRIMARY KEY,
    exam_id    INTEGER NOT NULL REFERENCES exams(id),
    student_id INTEGER NOT NULL REFERENCES students(id),
    score      REAL    NOT NULL,
    decision   TEXT    NOT NULL CHECK (decision IN ('pass', 'repeat', 'teacher')),
    reason     TEXT    NOT NULL DEFAULT '',
    decided_by INTEGER NOT NULL,
    UNIQUE (exam_id, student_id)
);

CREATE TABLE topics (
    id       INTEGER PRIMARY KEY,
    stage_id INTEGER NOT NULL REFERENCES stages(id),
    unit_no  INTEGER NOT NULL,
    title    TEXT    NOT NULL,
    UNIQUE (stage_id, unit_no)
);

CREATE TABLE hints (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    group_id   INTEGER NOT NULL REFERENCES groups(id),
    rule       TEXT    NOT NULL,
    details    TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    closed_at  TEXT
);

-- Защита от повторной отправки одной и той же формы
CREATE TABLE submissions (
    uuid        TEXT PRIMARY KEY,
    tg_id       INTEGER NOT NULL,
    kind        TEXT    NOT NULL,
    received_at TEXT    NOT NULL DEFAULT (datetime('now')),
    status      TEXT    NOT NULL
);

CREATE TABLE audit_log (
    id         INTEGER PRIMARY KEY,
    tg_id      INTEGER NOT NULL,
    action     TEXT    NOT NULL,
    object     TEXT    NOT NULL DEFAULT '',
    details    TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
