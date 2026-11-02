"""Huella de CONTENIDO de una card (solo lectura). No usa el nombre del archivo ni la portada.

Sirve para saber si dos cards son «la misma» aunque una sea la female y la otra su versión futa:
la huella ignora justo lo que cambia `editors/futa.py::apply_futa`, de modo que

    huella(female) == huella(apply_futa(female))

Entra en la huella: Custom (cara, cuerpo, pelo), Coordinate (ropa y accesorios), Parameter (menos sexo y
nombres) y los plugins de KKEx (menos los de futa y los huesos genitales / del pene de ABMX).
No entra: la portada, About, Status, el sexo, los nombres, ni nada de lo que toca la conversión a futa.
Los decimales se redondean a 4 cifras (los sliders se guardan como float de 32 bits).
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from .summary import ABM, BULGE, DONOR, MALEH, PENIS_BONE, TRAP, UNC

FP_VERSION = 1      # súbelo si cambia lo que entra en la huella: invalida la caché de huellas
SKIP_BLOCKS = {"About", "Status"}                         # datos de la card que no son «contenido»
SKIP_PARAMETER = {"sex", "lastname", "firstname", "nickname", "fullname"}
SKIP_PLUGINS = {TRAP, UNC, BULGE, MALEH, DONOR}           # los escribe la conversión a futa / la donación
_PRESETS = Path(__file__).resolve().parent.parent / "config" / "presets.json"
_FALLBACK_BONES = ("cf_d_kokan", "cf_j_kokan", "cf_d_ana", "cf_j_ana")


@lru_cache(maxsize=1)
def ignored_bones():
    """Huesos ABMX que la conversión a futa resetea o recalcula (presets.json + el hueso del pene)."""
    try:
        names = json.loads(_PRESETS.read_text(encoding="utf-8"))["futa_bp_sos"].get("reset_huesos") or []
    except Exception:
        names = _FALLBACK_BONES
    return frozenset(names) | {PENIS_BONE}


def _feed(h, o):
    """Añade `o` al hash de forma canónica (claves de dict ordenadas, floats redondeados)."""
    if o is None:
        h.update(b"N")
    elif isinstance(o, bool):
        h.update(b"T" if o else b"F")
    elif isinstance(o, int):
        h.update(b"i%d;" % o)
    elif isinstance(o, float):
        r = round(o, 4)
        h.update(b"f%.4f;" % (0.0 if r == 0 else r))      # -0.0 y 0.0 son lo mismo
    elif isinstance(o, str):
        b = o.encode("utf-8", "surrogatepass")
        h.update(b"s%d:" % len(b))
        h.update(b)
    elif isinstance(o, (bytes, bytearray, memoryview)):
        h.update(b"b%d:" % len(o))
        h.update(o)
    elif isinstance(o, dict):
        h.update(b"d%d{" % len(o))
        for k in sorted(o, key=lambda k: (type(k).__name__, str(k))):
            _feed(h, k)
            _feed(h, o[k])
        h.update(b"}")
    elif isinstance(o, (list, tuple)):
        h.update(b"l%d[" % len(o))
        for x in o:
            _feed(h, x)
        h.update(b"]")
    elif hasattr(o, "code") and hasattr(o, "data"):          # msgpack.ExtType
        h.update(b"x%d:" % o.code)
        _feed(h, o.data)
    else:
        h.update(b"o")
        h.update(repr(o).encode("utf-8", "replace"))


def _parameter(data):
    return {k: v for k, v in data.items() if k not in SKIP_PARAMETER} if isinstance(data, dict) else data


def _kkex(data):
    """Plugins sin los de futa; en ABMX, sin los huesos genitales/del pene. ABMX vacío = sin ABMX."""
    if not isinstance(data, dict):
        return data
    out = {k: v for k, v in data.items() if k not in SKIP_PLUGINS}
    entry = out.get(ABM)
    if entry is not None:
        if isinstance(entry, (list, tuple)) and len(entry) > 1 and isinstance(entry[1], dict):
            fields = dict(entry[1])
            skip = ignored_bones()
            bones = [b for b in (fields.get("boneData") or [])
                     if not (isinstance(b, (list, tuple)) and b and b[0] in skip)]
            bones.sort(key=lambda b: str(b[0]) if isinstance(b, (list, tuple)) and b else "")
            fields["boneData"] = bones
            if not bones and set(fields) == {"boneData"}:
                del out[ABM]
            else:
                out[ABM] = fields       # sin el número de versión: lo crea la conversión si la card no tenía ABMX
        # si ABMX no tiene la forma esperada (p. ej. un texto antiguo) se deja tal cual
    return out


def fingerprint(card):
    """Huella (sha256 hexadecimal) del contenido de una card ya cargada con core.card_io.load_card."""
    h = hashlib.sha256(b"kktool-fp%d|" % FP_VERSION)
    for name in sorted(n for n in card.blockdata if n not in SKIP_BLOCKS):
        data = getattr(card, name).data
        if name == "Parameter":
            data = _parameter(data)
        elif name == "KKEx":
            data = _kkex(data)
        h.update(b"#" + name.encode() + b":")
        _feed(h, data)
    return h.hexdigest()
