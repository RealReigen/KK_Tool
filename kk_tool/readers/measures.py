"""Medidas calibradas del juego (config/medidas.json): altura por slider y tamaño de referencia del pene."""
import json
from functools import lru_cache
from pathlib import Path

MEASURES_FILE = Path(__file__).resolve().parent.parent / "config" / "medidas.json"
_DEFAULT = {"altura_slider": {"base": 0.9, "pendiente": 0.2}, "referencia_slider": 0.6, "pene_ok": [0.95, 1.05]}


@lru_cache(maxsize=1)
def load():
    """Medidas del JSON; si falta o está roto se usan las de fábrica (nunca falla)."""
    try:
        d = json.loads(MEASURES_FILE.read_text(encoding="utf-8"))
        h = d["altura_slider"]
        float(h["base"]), float(h["pendiente"]), float(d["referencia_slider"])
        lo, hi = d["pene_ok"]
        float(lo), float(hi)
        return d
    except Exception:
        return _DEFAULT


def slider_scale(slider0):
    """Escala del cuerpo que da el slider de altura (1.0 = slider 0.5). None -> 1.0."""
    if slider0 is None:
        return 1.0
    h = load()["altura_slider"]
    return h["base"] + h["pendiente"] * float(slider0)


def reference_size():
    """Tamaño absoluto del pene de la card male de muestra (su altura de slider, sin huesos)."""
    return round(slider_scale(load()["referencia_slider"]), 4)


def pene_ok():
    lo, hi = load()["pene_ok"]
    return float(lo), float(hi)
