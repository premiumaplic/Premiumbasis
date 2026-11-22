"""Логотип центра в векторе: из него делаются SVG для приложений и значок на карточке родителю.

Координаты сняты с исходного макета 1024×1024 (assets/logo/). Три вложенных шестиугольника,
сдвинутых вправо и обрезанных справа (буква «С»), внутри — фигура в шапочке выпускника и с галстуком.
Внутренность «С» прозрачная, поэтому знак ложится на любой фон.

Цвета задаются схемой: outer — внешняя полоса, middle — средняя, figure — фигура, tie — галстук.
"""

import math

SIZE = 1024
CLIP_X = 796                     # правый срез шестиугольников
ORANGE, DARK, WHITE = "#F5660A", "#161616", "#FFFFFF"
SCHEMES = {
    "dark": {"bg": DARK, "outer": WHITE, "middle": ORANGE, "figure": WHITE, "tie": ORANGE},
    "light": {"bg": WHITE, "outer": DARK, "middle": ORANGE, "figure": DARK, "tie": ORANGE},
    "orange": {"bg": ORANGE, "outer": DARK, "middle": WHITE, "figure": DARK, "tie": WHITE},
}

# шестиугольники: центр по x (по y — 512) и радиус описанной окружности
HEX_OUTER, HEX_MIDDLE, HEX_INNER = (512, 328), (538, 300), (564, 272.5)

ARM_LEFT = [(436, 349), (466, 376), (430, 417), (521, 519), (510, 622), (462, 677), (479, 532), (375, 417)]
ARM_RIGHT = [(1128 - x, y) for x, y in ARM_LEFT]          # зеркально относительно x = 564
BOARD = [(564, 347), (633, 378), (564, 408), (495, 378)]   # доска шапочки
HEAD = [(518, 397), (564, 417), (610, 397), (610, 443), (564, 469), (518, 443)]
TASSEL_CORD = (630, 378, 636, 412)                          # x1, y1, x2, y2
TASSEL_END = (627, 408, 638, 431)
TIE_KNOT = [(552, 514), (576, 514), (573, 535), (555, 535)]
TIE = [(556, 540), (572, 540), (583, 657), (564, 693), (545, 657)]


def _hexagon(cx: float, r: float, cy: float = 512) -> list[tuple[float, float]]:
    h = r * math.sqrt(3) / 2
    return [(cx, cy - r), (cx + h, cy - r / 2), (cx + h, cy + r / 2), (cx, cy + r), (cx - h, cy + r / 2), (cx - h, cy - r / 2)]


def _clip_right(points: list[tuple[float, float]], limit: float = CLIP_X) -> list[tuple[float, float]]:
    """Оставляет часть многоугольника левее x = limit."""
    out = []
    for i, cur in enumerate(points):
        prev = points[i - 1]
        cur_in, prev_in = cur[0] <= limit, prev[0] <= limit
        if cur_in != prev_in:
            k = (limit - prev[0]) / (cur[0] - prev[0])
            out.append((limit, prev[1] + k * (cur[1] - prev[1])))
        if cur_in:
            out.append(cur)
    return out


def hexes() -> list[list[tuple[float, float]]]:
    return [_clip_right(_hexagon(cx, r)) for cx, r in (HEX_OUTER, HEX_MIDDLE, HEX_INNER)]


def _d(points) -> str:
    return "M" + "L".join(f"{x:g} {y:g}".replace(".0 ", " ") for x, y in ((round(x, 1), round(y, 1)) for x, y in points)) + "Z"


def paths() -> dict[str, str]:
    """Части знака как пути SVG (для анимации в приложении части нужны по отдельности)."""
    outer, middle, inner = hexes()
    x1, y1, x2, y2 = TASSEL_CORD
    e1, f1, e2, f2 = TASSEL_END
    return {
        "outer": _d(outer) + _d(middle),           # полоса = внешний минус средний (evenodd)
        "middle": _d(middle) + _d(inner),
        "arm-l": _d(ARM_LEFT),
        "arm-r": _d(ARM_RIGHT),
        "board": _d(BOARD),
        "head": _d(HEAD),
        "tassel": _d([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]) + _d([(e1, f1), (e2, f1), (e2, f2), (e1, f2)]),
        "tie": _d(TIE_KNOT) + _d(TIE),
    }


PART_COLOR = {"outer": "outer", "middle": "middle", "arm-l": "figure", "arm-r": "figure",
              "board": "figure", "head": "figure", "tassel": "figure", "tie": "tie"}


def svg(scheme: str = "light", background: bool = False, view: str = "162 162 700 700") -> str:
    """Готовый SVG-файл. view — рамка (по умолчанию квадрат вокруг знака)."""
    colors = SCHEMES[scheme]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}">']
    if background:
        parts.append(f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}" fill="{colors["bg"]}"/>')
    for name, d in paths().items():
        parts.append(f'<path fill-rule="evenodd" fill="{colors[PART_COLOR[name]]}" d="{d}"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def draw(img, x: int, y: int, size: int, scheme: str = "light", frame=(162, 162, 700)) -> None:
    """Рисует знак на картинке Pillow: (x, y) — левый верхний угол квадрата size×size."""
    from PIL import Image, ImageDraw

    colors = SCHEMES[scheme]
    k = 4                                   # рисуем крупнее и уменьшаем — края гладкие
    big = size * k
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    left, top, span = frame                 # по умолчанию та же рамка, что у svg()
    scale = big / span

    def pt(points):
        return [((px - left) * scale, (py - top) * scale) for px, py in points]

    outer, middle, inner = hexes()
    d.polygon(pt(outer), fill=colors["outer"])
    d.polygon(pt(middle), fill=colors["middle"])
    hole = Image.new("L", (big, big), 0)    # внутренность «С» — прозрачная
    ImageDraw.Draw(hole).polygon(pt(inner), fill=255)
    layer.paste((0, 0, 0, 0), mask=hole)
    for shape in (ARM_LEFT, ARM_RIGHT, BOARD, HEAD):
        d.polygon(pt(shape), fill=colors["figure"])
    for x1, y1, x2, y2 in (TASSEL_CORD, TASSEL_END):
        d.rectangle(pt([(x1, y1), (x2, y2)]), fill=colors["figure"])
    d.polygon(pt(TIE_KNOT), fill=colors["tie"])
    d.polygon(pt(TIE), fill=colors["tie"])
    small = layer.resize((size, size), Image.LANCZOS)
    img.paste(small, (x, y), small)
