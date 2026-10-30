"""Recorre archivos/carpetas y resume cada card. Un fallo no detiene el lote."""
from pathlib import Path
from ..core.card_io import load_card
from ..readers.attributes import derive, safe_defs
from ..readers.fileinfo import file_info
from ..readers.summary import summarize


def read_card_summary(path, defs=None):
    """Resumen de la card + datos del archivo + atributos derivados (lo que muestran las listas)."""
    s = summarize(load_card(path))
    s["archivo_info"] = file_info(path)
    s["attrs"] = derive(s, safe_defs() if defs is None else defs)
    return s


def find_cards(target):
    t = Path(target)
    return [t] if t.is_file() else sorted(t.rglob("*.png"))


def scan(target):
    rows, defs = [], safe_defs()
    for path in find_cards(target):
        try:
            rows.append((path, read_card_summary(path, defs), None))
        except Exception as e:  # card corrupta o no-KK
            rows.append((path, None, f"{type(e).__name__}: {e}"))
    return rows


def find_cards_multi(folders):
    """Busca cards en varias carpetas. Devuelve (cards_sin_duplicados, carpetas_inexistentes)."""
    cards, seen, missing = [], set(), []
    for folder in folders:
        if not Path(folder).exists():
            missing.append(str(folder))
            continue
        for p in find_cards(folder):
            key = p.resolve()
            if key not in seen:
                seen.add(key)
                cards.append(p)
    return cards, missing
