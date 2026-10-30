"""Atributos derivados de una card (altura, pecho, tipo…). Solo lectura, sin GUI.

Las definiciones viven en config/atributos.json (ver su '_ayuda'). Este módulo las carga,
las valida y calcula, para el resumen de una card, la categoría y la puntuación de cada una.
"""
import json
from functools import lru_cache
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "atributos.json"
_AXES = {"x": 0, "y": 1, "z": 2}


class AttributeConfigError(Exception):
    """atributos.json mal escrito (el mensaje dice qué atributo y qué falla)."""


def _validate(defn):
    where = f"atributo '{defn.get('clave', '?')}'"
    for k in ("clave", "titulo", "origen"):
        if not defn.get(k):
            raise AttributeConfigError(f"{where}: falta '{k}'")
    if defn["origen"] == "campo":
        if not defn.get("campo") or not defn.get("categorias"):
            raise AttributeConfigError(f"{where}: origen 'campo' necesita 'campo' y 'categorias'")
    elif defn["origen"] == "puntuacion":
        if not defn.get("terminos"):
            raise AttributeConfigError(f"{where}: falta 'terminos'")
        cortes = defn.get("cortes") or []
        if len(cortes) < 2 or any("hasta" not in c for c in cortes[:-1]):
            raise AttributeConfigError(f"{where}: 'cortes' necesita 2 o más; todos menos el último con 'hasta'")
        hastas = [c["hasta"] for c in cortes[:-1]]
        if hastas != sorted(hastas):
            raise AttributeConfigError(f"{where}: los 'hasta' de 'cortes' deben ir de menor a mayor")
        for t in defn["terminos"]:
            kind = str(t.get("medida", "")).split(":")[0]
            if kind not in ("slider", "hueso") or "neutro" not in t:
                raise AttributeConfigError(f"{where}: término no válido {t}")
    else:
        raise AttributeConfigError(f"{where}: origen desconocido '{defn['origen']}'")


@lru_cache(maxsize=1)
def load_defs():
    """Lista de definiciones. Lanza AttributeConfigError si el JSON no es válido."""
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        defs = data["atributos"]
    except Exception as e:
        raise AttributeConfigError(f"no se pudo leer {CONFIG_FILE.name}: {e}") from e
    keys = set()
    for d in defs:
        _validate(d)
        if d["clave"] in keys:
            raise AttributeConfigError(f"clave repetida: {d['clave']}")
        keys.add(d["clave"])
    return defs


def safe_defs(log=None):
    """Como load_defs pero nunca falla: si el JSON está mal, avisa y devuelve [] (sin filtros)."""
    try:
        return load_defs()
    except AttributeConfigError as e:
        if log:
            log(f"AVISO: atributos desactivados, {e}")
        return []


def categories(defn):
    """Nombres de categoría de un atributo, en orden."""
    if defn["origen"] == "campo":
        return list(defn["categorias"])
    return [c["nombre"] for c in defn["cortes"]]


def measure(s, ref):
    """Valor de una medida ('slider:4', 'hueso:cf_n_height:y') o None si la card no la tiene."""
    parts = ref.split(":")
    if parts[0] == "slider":
        sl, i = s.get("sliders") or [], int(parts[1])
        return sl[i] if i < len(sl) else None
    bone = (s.get("bones_scale") or {}).get(parts[1])
    return bone[_AXES[parts[2] if len(parts) > 2 else "y"]] if bone else None


def score(s, defn):
    """Puntuación numérica (0 = neutro). Un hueso ausente cuenta como neutro; un slider
    ausente deja la puntuación en None."""
    total = 0.0
    for t in defn["terminos"]:
        v = measure(s, t["medida"])
        if v is None:
            if t["medida"].startswith("slider"):
                return None
            continue
        total += t.get("peso", 1.0) * (v - t["neutro"])
    return round(total, 4)


def derive(s, defs=None):
    """{clave: {'cat': categoría|None, 'score': número|None}} para el resumen s."""
    out = {}
    for d in (load_defs() if defs is None else defs):
        if d["origen"] == "campo":
            num = s.get(d["numero"]) if d.get("numero") else None   # campo numérico opcional (para ordenar)
            out[d["clave"]] = {"cat": s.get(d["campo"]), "score": num}
            continue
        sc = score(s, d)
        cat = None
        if sc is not None:
            cat = d["cortes"][-1]["nombre"]
            for c in d["cortes"][:-1]:
                if sc < c["hasta"]:
                    cat = c["nombre"]
                    break
        out[d["clave"]] = {"cat": cat, "score": sc}
    return out
