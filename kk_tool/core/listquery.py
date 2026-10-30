"""Buscar, filtrar y ordenar las filas de una lista de cards. Lógica pura: sin GUI ni disco.

Piezas (para ampliar, tocar SOLO la pieza que toque):
- Entry:        una fila (ruta + resumen + datos del archivo).
- FilterState:  lo que el usuario ha pedido: texto + categorías aceptadas por atributo.
- matches():    ¿la fila pasa el filtro?  Texto: todas las palabras; entre atributos: Y; dentro de uno: O.
- SortOption:   una forma de ordenar (clave, etiqueta, función fila -> valor). Las filas sin valor van al final.
- sort_options(): opciones base + una por atributo de config/atributos.json.
Nuevo criterio de orden = una línea en _BASE_SORTS. Nuevo atributo filtrable = un bloque en atributos.json.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


# ---------- texto ----------
def fold(text):
    """Minúsculas y sin tildes latinas (café = cafe). No toca el japonés (が sigue siendo が)."""
    out = []
    for ch in unicodedata.normalize("NFD", str(text or "")):
        if unicodedata.category(ch) == "Mn" and out and ord(out[-1]) < 0x250:
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out)).casefold()


def natural_key(text):
    """Orden 'de Windows': sin mayúsculas y con los números por su valor (card2 < card10)."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", fold(text))]


# ---------- filas ----------
@dataclass
class Entry:
    path: Path
    s: Optional[dict]           # resumen (con 'attrs' y 'archivo_info'); None = no se pudo leer
    seq: int = 0                # posición original de carga
    info: dict = field(default_factory=dict)   # mtime / ctime / size del archivo
    iid: str = ""               # id de la fila en el Treeview (lo pone la GUI)

    def __post_init__(self):
        s = self.s or {}
        self.haystack = fold(" ".join(str(x) for x in (
            self.path.name, s.get("nombre"), s.get("nickname"), s.get("donante")) if x))

    def attr(self, key):
        return ((self.s or {}).get("attrs") or {}).get(key) or {}

    def category(self, key):
        return self.attr(key).get("cat")

    def score(self, key):
        return self.attr(key).get("score")


# ---------- filtro ----------
@dataclass
class FilterState:
    text: str = ""
    groups: dict = field(default_factory=dict)   # clave de atributo -> {categorías aceptadas}

    def active_groups(self):
        return {k: v for k, v in self.groups.items() if v}

    def is_empty(self):
        return not self.text.strip() and not self.active_groups()


def matches(entry, state):
    for word in fold(state.text).split():
        if word not in entry.haystack:
            return False
    for key, cats in state.active_groups().items():
        if entry.category(key) not in cats:
            return False
    return True


# ---------- orden ----------
@dataclass
class SortOption:
    key: str
    label: str
    func: Callable      # Entry -> valor comparable | None (sin valor = al final)


def _name(e):
    return natural_key(e.s["nombre"]) if e.s and e.s.get("nombre") else None


def _txt(field_name):
    return lambda e: natural_key(e.s[field_name]) if e.s and e.s.get(field_name) else None


# (clave, etiqueta, función). La primera es el orden original de carga (el de la carpeta).
_BASE_SORTS = [
    ("orden", "Orden de carga (carpeta)", lambda e: e.seq),
    ("archivo", "Nombre de archivo (como Windows)", lambda e: natural_key(e.path.name)),
    ("nombre", "Nombre de la card", _name),
    ("modificada", "Fecha de modificación", lambda e: e.info.get("mtime")),
    ("creada", "Fecha de creación", lambda e: e.info.get("ctime")),
    ("tamano", "Tamaño del archivo", lambda e: e.info.get("size")),
    ("plugins", "Nº de plugins", lambda e: e.s["n_plugins"] if e.s else None),
    ("donante", "Cuerpo de (donante)", _txt("donante")),
]


def sort_options(defs):
    """Opciones base + una por atributo (puntuación numérica o categoría)."""
    opts = [SortOption(k, label, fn) for k, label, fn in _BASE_SORTS]
    for d in defs:
        if d["origen"] == "puntuacion" or d.get("numero"):
            opts.append(SortOption(f"attr:{d['clave']}", f"{d['titulo']} (valor)" if d.get("numero") else f"{d['titulo']} (puntuación)",
                                   lambda e, k=d["clave"]: e.score(k)))
        else:
            opts.append(SortOption(f"attr:{d['clave']}", d["titulo"],
                                   lambda e, k=d["clave"]: (e.category(k) or None)))
    return opts


def sort_entries(entries, option, descending=False):
    """Ordena sin perder estabilidad; las filas sin valor quedan siempre al final."""
    valued = [(option.func(e), e) for e in entries]
    have = [x for x in valued if x[0] is not None]
    have.sort(key=lambda x: x[0], reverse=descending)
    return [e for _, e in have] + [e for v, e in valued if v is None]
