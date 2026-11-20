-- Этап 2: готовые фразы для комментария и последняя выбранная группа учителя.

-- Готовые фразы — ЧЕРНОВИК, владелец поменяет. Фраза вставляется в комментарий
-- на языке карточки ученика, поэтому каждая хранится на двух языках.
CREATE TABLE phrases (
    id      INTEGER PRIMARY KEY,
    sort    INTEGER NOT NULL,
    text_ru TEXT    NOT NULL,
    text_uz TEXT    NOT NULL,
    active  INTEGER NOT NULL DEFAULT 1
);

INSERT INTO phrases (sort, text_ru, text_uz) VALUES
    (10, 'Молодец!',                  'Barakalla!'),
    (20, 'Старается на уроке.',       'Darsda harakat qiladi.'),
    (30, 'Нужно повторять слова.',    'Soʻzlarni takrorlash kerak.'),
    (40, 'Больше читать дома.',       'Uyda koʻproq oʻqish kerak.'),
    (50, 'Сдавать домашку вовремя.',  'Uy vazifasini oʻz vaqtida topshirish.'),
    (60, 'Заметный прогресс.',        'Sezilarli oʻsish bor.');

ALTER TABLE teachers ADD COLUMN current_group_id INTEGER REFERENCES groups(id);

-- Неделя, за которую последний раз отправлено напоминание учителям
INSERT INTO settings (key, value) VALUES ('reminder_last_week', '');
