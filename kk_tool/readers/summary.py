"""Lectura de solo consulta: resumen de una card. No modifica nada."""
from .measures import pene_ok, slider_scale

UNC = "com.deathweasel.bepinex.uncensorselector"
TRAP = "marco.becometrap"
BULGE = "Bulge"
MALEH = "kokaiinum.KKExpandMaleMaker"
ABM = "KKABMPlugin.ABMData"
HEIGHT_BONE = "cf_n_height"      # altura total (también en cards male: verificado)
PENIS_BONE = "cm_J_dan100_00"    # raíz del pene en ABMX (verificado con una card male de muestra)
DONOR = "kktool.donor"          # entrada oculta propia (la escribe editors/donor.py)


def _get(obj, key, default=None):
    """Lectura segura: los objetos de kkloader admiten [] pero no .get()."""
    try:
        return obj[key]
    except (KeyError, IndexError, TypeError):
        return default


def _fields(kkex, key):
    """Devuelve el dict de campos de un plugin, o {} si no existe."""
    entry = kkex.get(key)
    if not entry or len(entry) < 2 or not isinstance(entry[1], dict):
        return {}
    return entry[1]


def _bone_height(kkex):
    """Escala del hueso cf_n_height (lista xyz) o None si no existe."""
    for bone in _fields(kkex, ABM).get("boneData") or []:
        if bone[0] == "cf_n_height":
            try:
                return [round(float(v), 4) for v in bone[1][0][0]]
            except (IndexError, TypeError):
                return None
    return None


def _bones_scale(kkex):
    """{nombre_hueso: [x, y, z]} con la escala de cada hueso ABMX (solo lectura).
    Un hueso que no aparece = sin modificar (valores por defecto)."""
    out = {}
    for bone in _fields(kkex, ABM).get("boneData") or []:
        try:
            out[bone[0]] = [round(float(v), 4) for v in bone[1][0][0]]
        except (IndexError, TypeError, ValueError):
            pass
    return out


def _mean(vec):
    return round(sum(vec) / len(vec), 4)


def penis_size(bones_scale, slider0=None):
    """(escala_hueso_pene | None, escala_altura_total, tamaño efectivo).
    El pene cuelga del cuerpo y hereda su escala: efectivo = hueso del pene x hueso de altura x escala del
    slider de altura (config/medidas.json). 1.0 = male con slider 0.5 y sin huesos."""
    pen, hei = bones_scale.get(PENIS_BONE), bones_scale.get(HEIGHT_BONE)
    pen = _mean(pen) if pen else None
    height = round((_mean(hei) if hei else 1.0) * slider_scale(slider0), 4)
    return pen, height, round((pen if pen is not None else 1.0) * height, 4)


def classify(sex, is_trap, has_penis, display_penis):
    """female / male / futa / futa incompleta."""
    indicators = [is_trap, has_penis, display_penis]
    if sex == 0 and all(indicators):
        return "futa"
    if any(indicators):
        return "futa incompleta"
    return "male" if sex == 0 else "female"


def summarize(card):
    kkex = card["KKEx"].data
    p = card["Parameter"]
    bones_scale = _bones_scale(kkex)
    pene_bone, _h, pene_ef = penis_size(bones_scale, card["Custom"]["body"]["shapeValueBody"][0])
    unc = _fields(kkex, UNC)
    trap = _fields(kkex, TRAP)
    bulge = _fields(kkex, BULGE)
    maleh = _fields(kkex, MALEH)
    sex = p["sex"]
    is_trap = bool(trap.get("IsTrap", False))
    has_penis = unc.get("PenisGUID") is not None
    display_penis = bool(unc.get("DisplayPenis", False))
    tipo = classify(sex, is_trap, has_penis, display_penis)
    return {
        "nombre": " ".join(x for x in (_get(p, "firstname"), _get(p, "lastname")) if x),
        "nickname": _get(p, "nickname", ""),
        "sex": sex,
        "tipo": tipo,
        "pene_estado": (None if tipo == "female" else
                        "corto" if pene_ef < pene_ok()[0] else "largo" if pene_ef > pene_ok()[1] else "ok"),
        "is_trap": is_trap,
        "body_guid": unc.get("BodyGUID"),
        "penis_guid": unc.get("PenisGUID"),
        "display_penis": display_penis,
        "display_balls": bool(unc.get("DisplayBalls", False)),
        "bulge": bulge.get("EnableBulge"),  # None = sin entrada; 2 = desactivado
        "male_height_enabled": maleh.get("MaleHeightEnabled"),
        "altura_slider": round(card["Custom"]["body"]["shapeValueBody"][0], 4),
        "altura_hueso": _bone_height(kkex),
        # medidas en bruto: de aquí leen los atributos de config/atributos.json
        "sliders": [round(float(v), 4) for v in card["Custom"]["body"]["shapeValueBody"]],
        "bones_scale": bones_scale,
        "pene_escala": pene_bone,        # escala del hueso del pene (None = sin tocar)
        "pene_efectivo": pene_ef,        # pene x altura (1.0 = tamaño de fábrica)
        "n_plugins": len(kkex),
        "donante": _fields(kkex, DONOR).get("Donante"),   # None = no es una card donada
        "modo_donacion": _fields(kkex, DONOR).get("Modo"),
    }
