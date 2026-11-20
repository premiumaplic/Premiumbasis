"""Тестовый бот этапа 0.

Проверяет то, от чего зависит вся схема:
  1) отправку формы (sendData) с кнопки под полем ввода на разных телефонах и ПК;
  2) какую длину ссылки в кнопке принимает Telegram и доносит до формы;
  3) доходят ли наши данные после # и после ? в ссылке;
  4) сколько байт реально уходит в отправке (предел 4096);
  5) приходят ли данные, отправленные, пока бот был выключен.
Пункт 6 (переносной Python) проверяет setup.bat и файл data\\check_outside.txt.

Все данные учеников здесь выдуманы. Запуск: probe.bat
"""

import asyncio
import json
import logging
import random
import string
import sys
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.exceptions import (TelegramAPIError, TelegramBadRequest,
                                TelegramUnauthorizedError)
from aiogram.filters import Command, CommandStart
from aiogram.types import (ChatMemberUpdated, KeyboardButton, Message,
                           ReplyKeyboardMarkup, WebAppInfo)

from bot import config as cfg
from bot import keepawake, logsetup
from bot.payload import SEND_DATA_LIMIT, byte_size, encode_param, to_json
from bot.probe_data import form_input
from bot.timefmt import human_duration, human_time

log = logging.getLogger("probe")

URL_TEST_LENGTHS = [1000, 2000, 4000, 8000, 16000, 32000]
OFFLINE_DELAY = 60  # секунд: если данные шли дольше — бот был выключен

PLATFORMS = {
    "android": "Android",
    "ios": "iPhone",
    "tdesktop": "Telegram Desktop",
    "macos": "Telegram для Mac",
    "weba": "Telegram Web A",
    "webk": "Telegram Web K",
}

BTN_FORM_HASH = "🧪 Форма (#)"
BTN_FORM_QUERY = "🧪 Форма (?)"
BTN_URL_HASH = "📏 Длина ссылки (#)"
BTN_URL_QUERY = "📏 Длина ссылки (?)"
BTN_REPORT = "📊 Итоги"
BTN_MYID = "🆔 Мой ID"
BTN_BACK = "⬅️ Назад"


# ---------------------------------------------------------------- ссылки

def form_url(base: str, variant: str, payload: dict) -> str:
    """variant: 'hash' — данные после #, 'query' — после ?"""
    separator = "#d=" if variant == "hash" else "?d="
    return f"{base}probe/{separator}{encode_param(payload)}"


def padded_url(base: str, variant: str, target: int, seed: int = 0) -> str:
    """Ссылка примерно заданной длины: в данные добавляется случайный «балласт»."""
    rnd = random.Random(seed or target)
    alphabet = string.ascii_letters + string.digits
    pad_len = max(0, target - 120)
    url = ""
    for _ in range(8):
        pad = "".join(rnd.choice(alphabet) for _ in range(pad_len))
        url = form_url(base, variant, {"v": 1, "k": variant, "L": target, "pad": pad})
        diff = target - len(url)
        if abs(diff) <= 4:
            break
        pad_len = max(0, pad_len + diff * 3 // 4)
    return url


def main_keyboard(conf: cfg.Config) -> ReplyKeyboardMarkup:
    data = form_input(20, with_questions=True)
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, keyboard=[
        [KeyboardButton(text=BTN_FORM_HASH, web_app=WebAppInfo(
            url=form_url(conf.forms_url, "hash", {**data, "k": "hash"}))),
         KeyboardButton(text=BTN_FORM_QUERY, web_app=WebAppInfo(
             url=form_url(conf.forms_url, "query", {**data, "k": "query"})))],
        [KeyboardButton(text=BTN_URL_HASH), KeyboardButton(text=BTN_URL_QUERY)],
        [KeyboardButton(text=BTN_REPORT), KeyboardButton(text=BTN_MYID)],
    ])


def url_keyboard(conf: cfg.Config, variant: str, lengths: list[int]) -> ReplyKeyboardMarkup:
    mark = "#" if variant == "hash" else "?"
    rows = [[KeyboardButton(text=f"📏 {length} ({mark})",
                            web_app=WebAppInfo(url=padded_url(conf.forms_url, variant, length)))]
            for length in lengths]
    rows.append([KeyboardButton(text=BTN_BACK)])
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=rows)


# ---------------------------------------------------------------- разбор отправки

def parse_probe(text: str, sent_at: datetime, now: datetime) -> dict:
    """Проверяет присланные формой данные и возвращает запись для журнала проверок."""
    size = byte_size(text)
    if size > SEND_DATA_LIMIT:
        raise ValueError(f"слишком большой пакет: {size} байт")
    try:
        data = json.loads(text)
    except ValueError:
        raise ValueError("данные повреждены") from None
    if not isinstance(data, dict) or data.get("t") != "probe":
        raise ValueError("это не данные тестовой формы")

    intact = data.get("n") == size
    rows = data.get("r")
    if data.get("m") == "weekly20":
        intact = intact and isinstance(rows, list) and len(rows) == 20 and all(
            isinstance(r, list) and len(r) == 4 and len(r[3]) == 80 for r in rows)

    return {
        "received": now.isoformat(timespec="seconds"),
        "sent": sent_at.isoformat(timespec="seconds"),
        "delay": int((now - sent_at).total_seconds()),
        "platform": str(data.get("p", "?"))[:20],
        "version": str(data.get("tv", ""))[:10],
        "mode": str(data.get("m", "?"))[:10],
        "variant": str(data.get("k", "?"))[:10],
        "hash_ok": bool(data.get("h")),
        "query_ok": bool(data.get("q")),
        "decoded": bool(data.get("ok")),
        "inflate": str(data.get("dm", ""))[:20],
        "native_inflate": bool(data.get("dn")),
        "url_len": int(data.get("ul") or 0),
        "url_test": int(data.get("L") or 0),
        "tz_min": int(data.get("tz") or 0),
        "bytes": size,
        "intact": intact,
    }


def platform_name(code: str) -> str:
    return PLATFORMS.get(code, code)


def describe(rec: dict, sent_at: datetime, now: datetime) -> str:
    """Короткий ответ владельцу на одну отправку."""
    yes, no = "✅", "❌"
    lines = [f"Получено с {platform_name(rec['platform'])}: {rec['bytes']} байт, "
             f"данные целы {yes if rec['intact'] else no}"]
    if rec["url_test"]:
        lines.append(f"Ссылка ≈{rec['url_test']} символов: "
                     f"{'дошла целиком ' + yes if rec['decoded'] else 'обрезана ' + no}")
    else:
        lines.append(f"Данные после #: {yes if rec['hash_ok'] else no}   после ?: {yes if rec['query_ok'] else '—'}")
        lines.append(f"Расшифровка: {yes if rec['decoded'] else no} (распаковка: {rec['inflate']})")
    if rec["delay"] > OFFLINE_DELAY:
        lines.append(f"Отправлено {human_time(sent_at, now)}, когда бот был выключен. "
                     f"Сохранено сейчас (через {human_duration(rec['delay'])}) {yes}")
    if rec["tz_min"] != 300:
        lines.append("⚠️ Часы телефона не в часовом поясе Ташкента — даты на нём могут отличаться.")
    return "\n".join(lines)


# ---------------------------------------------------------------- итоговый отчёт

def summarize(records: list[dict], url_server: dict, outside_text: str | None) -> str:
    yes, no = "✅", "❌"
    platforms = sorted({r["platform"] for r in records}, key=lambda p: list(PLATFORMS).index(p)
                       if p in PLATFORMS else 99)
    out = ["Итоги проверки (этап 0)", ""]

    out.append("1. Отправка формы кнопкой под полем ввода:")
    for code in ("android", "ios", "tdesktop"):
        got = any(r["platform"] == code for r in records)
        out.append(f"   {platform_name(code)}: {'работает ' + yes if got else 'ещё не проверяли'}")
    for code in platforms:
        if code not in ("android", "ios", "tdesktop"):
            out.append(f"   {platform_name(code)}: работает {yes}")

    out.append("")
    out.append("2. Длина ссылки в кнопке:")
    for variant, mark in (("hash", "#"), ("query", "?")):
        info = url_server.get(variant)
        if info:
            accepted = info.get("accepted") or [0]
            out.append(f"   ({mark}) сервер Telegram принял до {max(accepted)} символов"
                       + (f", отказал на {min(int(k) for k in info['rejected'])}" if info.get("rejected") else ""))
    for code in platforms:
        tests = [r for r in records if r["platform"] == code and r["url_test"]]
        good = [r["url_test"] for r in tests if r["decoded"]]
        bad = [r["url_test"] for r in tests if not r["decoded"]]
        if tests:
            out.append(f"   {platform_name(code)}: дошло целиком до {max(good) if good else 0}"
                       + (f", обрезано на {min(bad)}" if bad else ""))
    needed = len(form_url("https://premiumaplic.github.io/Premiumbasis/", "hash",
                          form_input(20, with_questions=True)))
    out.append(f"   Нужно нам: ≈{needed} символов (20 учеников, ответы прошлой недели, тексты вопросов)")

    out.append("")
    out.append("3. Где передавать данные в ссылке:")
    for code in platforms:
        main = [r for r in records if r["platform"] == code and not r["url_test"]]
        if main:
            hash_ok = any(r["variant"] == "hash" and r["hash_ok"] and r["decoded"] for r in main)
            query_ok = any(r["variant"] == "query" and r["query_ok"] and r["decoded"] for r in main)
            tried_hash = any(r["variant"] == "hash" for r in main)
            tried_query = any(r["variant"] == "query" for r in main)
            out.append(f"   {platform_name(code)}: после # "
                       f"{(yes if hash_ok else no) if tried_hash else 'не проверяли'}, после ? "
                       f"{(yes if query_ok else no) if tried_query else 'не проверяли'}; распаковка: "
                       f"{', '.join(sorted({r['inflate'] for r in main if r['decoded']})) or '—'}")

    out.append("")
    out.append(f"4. Размер отправки (предел {SEND_DATA_LIMIT} байт):")
    for code in platforms:
        mine = [r for r in records if r["platform"] == code]
        weekly = [r for r in mine if r["mode"] == "weekly20"]
        biggest = max((r["bytes"] for r in mine if r["intact"]), default=0)
        line = f"   {platform_name(code)}: самая большая целая отправка {biggest} байт"
        if weekly:
            line += f"; недельный отчёт 20 учеников × 80 букв = {weekly[-1]['bytes']} байт " + \
                    (yes if weekly[-1]["intact"] else no)
        out.append(line)

    out.append("")
    out.append("5. Отправка при выключенном боте:")
    delayed = [r for r in records if r["delay"] > OFFLINE_DELAY]
    if delayed:
        for r in delayed[-3:]:
            out.append(f"   {platform_name(r['platform'])}: пришло после запуска, задержка "
                       f"{human_duration(r['delay'])} {yes}")
    else:
        out.append("   ещё не проверяли")

    out.append("")
    out.append("6. Переносной Python:")
    out.append("   " + (outside_text.strip().splitlines()[0] if outside_text else
                        "нет файла data\\check_outside.txt — запустите check.bat"))
    return "\n".join(out)


# ---------------------------------------------------------------- хранение результатов

class ProbeStore:
    def __init__(self, folder: Path):
        self.results = folder / "probe_results.jsonl"
        self.url_file = folder / "probe_url.json"
        self.outside = folder / "check_outside.txt"

    def add(self, record: dict) -> None:
        with self.results.open("a", encoding="utf-8") as f:
            f.write(to_json(record) + "\n")

    def records(self) -> list[dict]:
        if not self.results.exists():
            return []
        out = []
        for line in self.results.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out

    def url_info(self) -> dict:
        if not self.url_file.exists():
            return {}
        return json.loads(self.url_file.read_text(encoding="utf-8"))

    def save_url_info(self, variant: str, info: dict) -> None:
        data = self.url_info()
        data[variant] = info
        self.url_file.write_text(to_json(data), encoding="utf-8")

    def outside_text(self) -> str | None:
        if not self.outside.exists():
            return None
        return self.outside.read_text(encoding="utf-8-sig", errors="replace")


# ---------------------------------------------------------------- бот

def build_router(conf: cfg.Config, store: ProbeStore) -> Router:
    router = Router()
    router.message.filter(F.chat.type == "private")
    allowed = {i for i in [conf.owner_id, *conf.testers] if i}

    def has_access(message: Message) -> bool:
        return bool(message.from_user) and message.from_user.id in allowed

    async def deny(message: Message) -> None:
        await message.answer(f"Нет доступа.\nВаш Telegram ID: {message.from_user.id}\n"
                             "Передайте этот номер владельцу центра.")

    @router.my_chat_member()
    async def left_group(event: ChatMemberUpdated, bot: Bot) -> None:
        # Бот работает только в личных чатах: из групп сразу выходит
        if event.chat.type in ("group", "supergroup"):
            log.info("Добавили в группу %s — выхожу", event.chat.id)
            await bot.leave_chat(event.chat.id)

    @router.message(Command("myid"))
    @router.message(F.text == BTN_MYID)
    async def my_id(message: Message) -> None:
        await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

    @router.message(CommandStart())
    @router.message(F.text == BTN_BACK)
    async def start(message: Message) -> None:
        if not has_access(message):
            return await deny(message)
        await message.answer(
            "Тестовый бот этапа 0.\n\n"
            f"{BTN_FORM_HASH} и {BTN_FORM_QUERY} — открыть пробную форму (данные в ссылке после # или после ?).\n"
            f"{BTN_URL_HASH} / {BTN_URL_QUERY} — проверить, какую длину ссылки выдерживает Telegram.\n"
            f"{BTN_REPORT} — итоговый отчёт, его нужно переслать разработчику.",
            reply_markup=main_keyboard(conf))

    @router.message(F.text.in_({BTN_URL_HASH, BTN_URL_QUERY}))
    async def url_test(message: Message) -> None:
        if not has_access(message):
            return await deny(message)
        variant = "hash" if message.text == BTN_URL_HASH else "query"
        accepted, rejected = [], {}
        for length in URL_TEST_LENGTHS:
            try:
                probe = await message.answer(f"Проверяю ссылку ≈{length} символов…",
                                             reply_markup=url_keyboard(conf, variant, [length]))
                accepted.append(length)
                try:
                    await probe.delete()
                except TelegramAPIError:
                    pass
            except TelegramBadRequest as e:
                rejected[str(length)] = str(e.message)[:80]
        store.save_url_info(variant, {"accepted": accepted, "rejected": rejected})

        lengths = list(accepted)
        while lengths:
            try:
                await message.answer(
                    f"Сервер Telegram принял ссылки до {max(lengths)} символов"
                    + (f", отказал на {min(int(k) for k in rejected)}" if rejected else "") + ".\n\n"
                    "Теперь нажимайте по очереди кнопки «📏 …» внизу и в каждой форме — «Отправить». "
                    "Если форма пишет «данные повреждены или обрезаны», значит, ссылку такой длины "
                    "это приложение обрезает — тоже нажмите «Отправить», это важный результат.",
                    reply_markup=url_keyboard(conf, variant, lengths))
                return
            except TelegramBadRequest:
                lengths.pop()  # вся клавиатура не поместилась — убираем самую длинную
        await message.answer("Сервер Telegram не принял ни одной ссылки — сообщите разработчику.",
                             reply_markup=main_keyboard(conf))

    @router.message(F.text == BTN_REPORT)
    @router.message(Command("report"))
    async def report(message: Message) -> None:
        if not has_access(message):
            return await deny(message)
        await message.answer(summarize(store.records(), store.url_info(), store.outside_text()))

    @router.message(F.web_app_data)
    async def got_form(message: Message) -> None:
        if not has_access(message):
            return await deny(message)
        now = datetime.now(timezone.utc)
        try:
            record = parse_probe(message.web_app_data.data, message.date, now)
        except (ValueError, TypeError) as e:
            log.warning("Ошибочная отправка от %s: %s", message.from_user.id, e)
            return await message.answer(f"Данные формы не прошли проверку: {e}")
        record["user"] = message.from_user.id
        store.add(record)
        log.info("Проверка: %s", {k: v for k, v in record.items() if k != "user"})
        await message.answer(describe(record, message.date, now), reply_markup=main_keyboard(conf))

    @router.message()
    async def other(message: Message) -> None:
        if not has_access(message):
            return await deny(message)
        await message.answer("Нажмите кнопку внизу или /start", reply_markup=main_keyboard(conf))

    return router


async def run(conf: cfg.Config) -> None:
    store = ProbeStore(cfg.data_dir())
    bot = Bot(conf.token)
    dp = Dispatcher()
    dp.include_router(build_router(conf, store))

    me = await bot.get_me()
    log.info("Тестовый бот @%s запущен", me.username)
    if keepawake.prevent_sleep():
        log.info("Компьютер не уйдёт в сон, пока открыто это окно")
    if not conf.owner_id:
        print("\n>>> В config.ini не вписан owner_id. Напишите боту /myid, впишите номер "
              "в config.ini и перезапустите probe.bat\n")
    else:
        try:
            await bot.send_message(conf.owner_id, "Тестовый бот запущен. Нажмите /start")
        except TelegramAPIError:
            log.info("Не смог написать владельцу — откройте бота в Telegram и нажмите Start")

    # Важно: старые обновления НЕ сбрасываются — так проверяется пункт 5
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def main() -> int:
    try:
        conf = cfg.load()
    except cfg.ConfigError as e:
        print(f"\nОШИБКА НАСТРОЕК: {e}\n")
        return 2
    logsetup.setup(cfg.data_dir() / "logs", "probe", [conf.token, conf.backup_password])
    try:
        asyncio.run(run(conf))
    except TelegramUnauthorizedError:
        print("\nОШИБКА НАСТРОЕК: Telegram не принял токен. Проверьте строку token в config.ini "
              "(скопируйте токен из @BotFather заново).\n")
        return 2
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
