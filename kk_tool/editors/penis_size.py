"""Herramienta: fijar el tamaño del pene de una card male/futa. No toca archivos.

Problema: el pene cuelga del cuerpo y hereda su escala. Si el cuerpo es pequeño (slider de altura bajo
y/o hueso ABMX `cf_n_height`), el pene se encoge igual y en las escenas H los personajes quedan lejos:
la female anima en el aire. Las animaciones están hechas para el tamaño de la male de referencia.

Medido: (1) hueso `cf_n_height` 0.5 + `cm_J_dan100_00` 2.0 en una card real (prueba del usuario);
(2) el slider de altura escala el cuerpo: pene medido en pantalla con slider 0.6 vs -0.7307 -> ratio 0.73-0.75;
modelo escala = 0.9 + 0.2 * slider (config/medidas.json).

Solución: escala del hueso del pene (`cm_J_dan100_00`) = tamaño_referencia / altura_total, con
altura_total = hueso de altura x escala del slider. tamaño_referencia por defecto = el pene de la male de
muestra (slider 0.6, sin huesos). Con altura igual a la de referencia no se escribe nada: hueso ausente =
valores por defecto en ABMX.
"""
from ..readers.measures import reference_size, slider_scale
from ..readers.summary import ABM, HEIGHT_BONE, PENIS_BONE, _bones_scale, _mean

EPS = 0.001       # por debajo de esta diferencia con 1.0 no se escribe el hueso
TOLERANCE = 0.01  # tolerancia al verificar el tamaño efectivo tras guardar


def _entry(card, create=False):
    kkex = card["KKEx"].data
    entry = kkex.get(ABM)
    if (not entry or len(entry) < 2 or not isinstance(entry[1], dict)) and create:
        entry = kkex[ABM] = [2, {"boneData": []}]
    return entry if entry and len(entry) > 1 and isinstance(entry[1], dict) else None


def height_factor(card):
    """Escala total del cuerpo: hueso `cf_n_height` (media xyz, 1.0 si no existe) x escala del slider de altura."""
    h = _bones_scale(card["KKEx"].data).get(HEIGHT_BONE)
    return round((_mean(h) if h else 1.0) * slider_scale(card["Custom"]["body"]["shapeValueBody"][0]), 4)


def reference(cfg):
    """Tamaño efectivo objetivo: cfg['tamano_referencia'] o, si no está, el de la male de muestra."""
    v = (cfg or {}).get("tamano_referencia")
    return float(v) if v else reference_size()


def apply_penis_size(card, cfg):
    """Pone el hueso del pene para que el tamaño efectivo sea el de referencia.
    cfg = preset['pene'] (o None = no hacer nada). Devuelve el texto para el log ('' si no hay config)."""
    if not cfg:
        return ""
    h = height_factor(card) if cfg.get("compensar_altura", True) else 1.0
    if h <= 0:
        return f"pene: altura {h} no válida, no se toca"
    ref = reference(cfg)
    target = round(ref / h, 4)
    entry = _entry(card, create=abs(target - 1.0) >= EPS)
    if entry is None:
        return f"pene: altura total {h} = la de referencia, nada que escribir"
    bones = entry[1].get("boneData") or []
    others = [b for b in bones if b[0] != PENIS_BONE]
    had = len(others) != len(bones)
    if abs(target - 1.0) < EPS:     # = por defecto: se quita el hueso (ausente = sin modificar)
        entry[1]["boneData"] = others
        return f"pene: altura total {h} -> tamaño de referencia" + (f", quitado {PENIS_BONE}" if had else ", nada que escribir")
    new = [PENIS_BONE, [[[target, target, target], 1.0, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]], 1]
    entry[1]["boneData"] = others + [new]
    return f"pene: altura total {h} -> {PENIS_BONE} escala {target} (tamaño efectivo {round(h * target, 4)})"


def effective_size(card):
    """Tamaño efectivo actual (pene x altura total), para verificar."""
    pen = _bones_scale(card["KKEx"].data).get(PENIS_BONE)
    return round((_mean(pen) if pen else 1.0) * height_factor(card), 4)


def verify_penis_size(card, cfg):
    """Lista de problemas (vacía = el tamaño efectivo es el de referencia)."""
    if not cfg or not cfg.get("compensar_altura", True):
        return []
    want, got = reference(cfg), effective_size(card)
    return [] if abs(got - want) <= TOLERANCE else [f"tamaño efectivo del pene {got} != {want}"]


def needs_repair(summary, cfg):
    """¿Esta futa (resumen de summarize) tiene el pene fuera del tamaño de referencia?
    Solo las futas completas: las female y las incompletas se tratan al convertirlas."""
    return (bool(cfg) and cfg.get("compensar_altura", True) and summary["tipo"] == "futa"
            and abs(summary["pene_efectivo"] - reference(cfg)) > TOLERANCE)
