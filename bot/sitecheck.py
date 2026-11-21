"""Проверка сайта с формами (GitHub Pages): отвечает ли он и та же ли на нём версия, что у бота.

После обновления GitHub публикует сайт за 1–2 минуты, а его серверы могут ещё 5–10 минут
отдавать старую копию. В это время кнопка приложения может показать «404».
"""

import time

import aiohttp

from bot import __version__


async def check(forms_url: str) -> str | None:
    """None — всё в порядке, иначе понятный владельцу текст проблемы."""
    url = f"{forms_url}version.txt?t={int(time.time())}"  # параметр — чтобы не получить старую копию
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url) as resp:
                if resp.status == 404:
                    return ("Сайт с формами отвечает «404 — не найдено». Проверьте GitHub: Settings → Pages → "
                            "ветка с программой и папка /docs. Если программу только что обновили — подождите "
                            "10 минут и нажмите /status снова.")
                if resp.status != 200:
                    return f"Сайт с формами не отвечает как надо (код {resp.status}). Попробуйте позже."
                site = (await resp.text()).strip()
    except (aiohttp.ClientError, TimeoutError, OSError):
        return "Не удалось открыть сайт с формами (нет интернета или GitHub недоступен)."
    if site != __version__:
        return (f"На сайте с формами версия {site}, а у бота {__version__}. Сайт ещё обновляется — "
                "подождите 5–10 минут, потом нажмите у учителя «🔄 Обновить».")
    return None
