"""Ограничение частоты сообщений."""

from bot.access import RateLimiter


def test_rate_limiter():
    rl = RateLimiter(window=60)
    assert all(rl.allow(1, 3, now=t) for t in (0, 1, 2))
    assert not rl.allow(1, 3, now=3)
    assert rl.allow(2, 3, now=3)          # другой человек не страдает
    assert rl.allow(1, 3, now=61)         # через минуту снова можно


def test_single_instance_lock(tmp_path):
    import subprocess
    import sys
    from bot import single
    lock = tmp_path / "bot.lock"
    assert single.acquire(lock)
    code = "import sys; from pathlib import Path; from bot import single; sys.exit(0 if single.acquire(Path(sys.argv[1])) else 3)"
    other = subprocess.run([sys.executable, "-c", code, str(lock)])
    assert other.returncode == 3  # второй экземпляр не запускается
