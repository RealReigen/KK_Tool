"""Franja de texto sobre la portada de una card (usa Pillow).

Único módulo de la app que modifica la portada. No toca archivos: cambia `card.image`
en memoria y `batch/donate.py` guarda la card. La franja es opaca, así que si la portada ya
traía una franja de una donación anterior, la nueva la tapa del todo.
"""
import io
import os
from pathlib import Path


class CoverError(Exception):
    pass


def pillow_available():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def _font_dirs():
    dirs = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts"]
    for base in ("/usr/share/fonts", "/usr/local/share/fonts", "/Library/Fonts", "/System/Library/Fonts"):
        b = Path(base)
        if b.exists():
            dirs += [b] + [d for d in b.rglob("*") if d.is_dir()]
    return dirs


def find_font(names):
    """Primera fuente de la lista que exista. Devuelve la ruta o None (se usará la de Pillow)."""
    dirs = _font_dirs()
    for name in names:
        cand = Path(name)
        if cand.is_absolute() and cand.exists():
            return str(cand)
        for d in dirs:
            if (d / name).exists():
                return str(d / name)
    return None


def _load_font(path, size):
    from PIL import ImageFont
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def _fit(draw, text, font_path, max_w, max_h, start):
    """Encoge la letra hasta que el texto quepa; si ni así, lo corta con '…'."""
    for size in range(start, 7, -1):
        font = _load_font(font_path, size)
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        if r - l <= max_w and b - t <= max_h:
            return font, text
    font = _load_font(font_path, 8)
    while len(text) > 1:
        text = text[:-1]
        l, t, r, b = draw.textbbox((0, 0), text + "…", font=font)
        if r - l <= max_w:
            break
    return font, text + "…"


def stamp_cover(card, text, style):
    """Pone la franja con `text` en la portada. Devuelve la fuente usada (para el log)."""
    from PIL import Image, ImageDraw
    if not card.image:
        raise CoverError("la card no tiene portada")
    img = Image.open(io.BytesIO(card.image))
    img = img.convert("RGBA" if "A" in img.mode else "RGB")
    w, h = img.size
    band = max(int(h * style["alto_franja_pct"] / 100), 18)
    y0 = h - band if style.get("posicion", "abajo") == "abajo" else 0
    fill = tuple(style["color_franja"]) + ((255,) if img.mode == "RGBA" else ())
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, y0, w, y0 + band), fill=fill)
    font_path = find_font(style["fuentes"])
    pad = 6
    font, shown = _fit(draw, text, font_path, w - 2 * pad, band - 4, start=band - 6)
    l, t, r, b = draw.textbbox((0, 0), shown, font=font)
    x = (w - (r - l)) // 2 - l
    y = y0 + (band - (b - t)) // 2 - t
    draw.text((x, y), shown, font=font, fill=tuple(style["color_texto"]) + ((255,) if img.mode == "RGBA" else ()))
    out = io.BytesIO()
    img.save(out, "PNG")
    card.image = out.getvalue()
    return os.path.basename(font_path) if font_path else "fuente por defecto de Pillow (sin japonés)"


def verify_stamp(saved, original, style):
    """Lista de problemas (vacía = bien): misma medida y franja con su color en la esquina."""
    from PIL import Image
    bad = []
    if not saved.image:
        return ["la card guardada no tiene portada"]
    a = Image.open(io.BytesIO(saved.image)).convert("RGB")
    b = Image.open(io.BytesIO(original.image)).convert("RGB")
    if a.size != b.size:
        return [f"la portada cambió de tamaño {b.size} -> {a.size}"]
    w, h = a.size
    band = max(int(h * style["alto_franja_pct"] / 100), 18)
    y = h - 2 if style.get("posicion", "abajo") == "abajo" else 1
    if a.getpixel((1, y)) != tuple(style["color_franja"]):
        bad.append(f"no se ve la franja en la portada guardada (píxel {a.getpixel((1, y))})")
    return bad
