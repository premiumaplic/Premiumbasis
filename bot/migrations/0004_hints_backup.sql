-- Этап 4: коды вопросов для правил подсказок, состояние подсказок, настройки бэкапа и сводки.

ALTER TABLE questions ADD COLUMN code TEXT NOT NULL DEFAULT '';
UPDATE questions SET code = 'homework'   WHERE sort = 10;
UPDATE questions SET code = 'classwork'  WHERE sort = 20;
UPDATE questions SET code = 'words'      WHERE sort = 30;
UPDATE questions SET code = 'grammar'    WHERE sort = 40;
UPDATE questions SET code = 'speaking'   WHERE sort = 50;
UPDATE questions SET code = 'understand' WHERE sort = 55;
UPDATE questions SET code = 'discipline' WHERE sort = 60;

-- cleared = 1: условие подсказки исчезло; после этого та же подсказка может появиться снова
ALTER TABLE hints ADD COLUMN cleared INTEGER NOT NULL DEFAULT 0;
CREATE INDEX hints_open ON hints(group_id, closed_at);
CREATE INDEX hints_rule ON hints(student_id, group_id, rule);

INSERT INTO settings (key, value) VALUES
    ('backup_last', ''),          -- когда сделан последний ежедневный бэкап
    ('summary_time', '20:00'),    -- сводка владельцу: в день напоминаний, в это время
    ('summary_last_week', '');
