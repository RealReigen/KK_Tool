"""Herramienta: donar el cuerpo de una card (donante) a otra (receptora). No toca archivos.

Reglas (acordadas con el usuario):
- Se SUSTITUYE, no se mezcla: los huesos ABMX de las categorías del modo que la receptora
  tenía y el donante no, se borran (en ABMX un hueso ausente = sin modificar).
- Solo se copian huesos 'cf_' (los 'cm_', p. ej. el pene, se quedan como estén).
- Cara, cabeza, cuello, piel, sexo y plugins de futa de la receptora no se tocan nunca.
- Female y futa se comportan igual (ambas usan el cuerpo 'cf_' y 44 sliders).
"""
import copy
import json
from functools import lru_cache
import re
from datetime import datetime
from pathlib import Path
from ..readers.summary import UNC, ABM, MALEH, DONOR as DONOR_KEY, summarize, _get, _fields

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "donaciones.json"
_OLD_TAG_LABEL = "cuerpo"     # etiqueta de la v0.4.0 ('[cuerpo: X]'): se sigue reconociendo
BODY_GUID_MODES = ("donante", "fijo")


class DonorError(Exception):
    """Combinación no válida (p. ej. una card male nativa)."""


def load_config():
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def classify_bone(name):
    """CARA / CABEZA / CUELLO / PECHO / ALTURA / CUERPO / OTRO (no cf_: no se copia)."""
    if not name.startswith("cf_"):
        return "OTRO"
    if name == "cf_n_height":
        return "ALTURA"
    if name.startswith("cf_J_"):          # J mayúscula = huesos de la cara
        return "CARA"
    if name in ("cf_s_head", "cf_hit_head"):
        return "CABEZA"
    if "neck" in name:
        return "CUELLO"
    if re.search(r"bust|bnip", name):
        return "PECHO"
    return "CUERPO"


def card_name(card, fallback=""):
    """Nombre como lo muestra el juego: apellido + nombre."""
    p = card["Parameter"]
    parts = [_get(p, "lastname", ""), _get(p, "firstname", "")]
    return " ".join(x for x in parts if x).strip() or fallback


@lru_cache(maxsize=1)
def _tag_re():
    """Etiqueta final '[<modo>: <donante>]' con cualquiera de las etiquetas de modo del JSON
    (y la antigua 'cuerpo'). Se construye una vez."""
    labels = {_OLD_TAG_LABEL} | {m["etiqueta"] for m in load_config()["modos"].values()}
    alt = "|".join(re.escape(x) for x in sorted(labels, key=len, reverse=True))
    return re.compile(rf"\s*\[(?:{alt}):[^\]]*\]\s*$")


def base_name(text):
    """Nombre original del personaje, sin la etiqueta ' [total: X]' (para no apilar etiquetas
    si se dona dos veces)."""
    return _tag_re().sub("", text or "").strip()


def name_suffix(cfg, mode_name, donor_label):
    """Sufijo del nombre: p. ej. ' [total: Otogi]'."""
    return cfg["nombre_sufijo"].format(modo=cfg["modos"][mode_name]["etiqueta"],
                                       donante=base_name(donor_label))


def tag_name(card, donor_label, cfg, mode_name):
    """Pone 'Nombre original [modo: Donante]' como nombre que muestra el juego (se reemplaza
    cualquier etiqueta anterior). Devuelve el texto del log."""
    p = card["Parameter"]
    suffix = name_suffix(cfg, mode_name, donor_label)
    field = "firstname" if _get(p, "firstname") else ("lastname" if _get(p, "lastname") else "firstname")
    old = card_name(card)
    p[field] = (base_name(_get(p, field, "")) + suffix).strip()
    return f"nombre: '{old}' -> '{card_name(card)}'"


def slider_ranges(indices):
    """[0,4,5,6,9] -> '0, 4-6, 9' (para no repetir 41 números en el log)."""
    out, idx = [], sorted(indices)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and idx[j + 1] == idx[j] + 1:
            j += 1
        out.append(str(idx[i]) if i == j else f"{idx[i]}-{idx[j]}")
        i = j + 1
    return ", ".join(out)


def check_compatible(card, label):
    """Acepta female y futa (también 'futa incompleta'); rechaza male nativa."""
    tipo = summarize(card)["tipo"]
    if tipo == "male":
        raise DonorError(f"{label} es una card male nativa: no se admite")
    if len(card["Custom"]["body"]["shapeValueBody"]) != 44:
        raise DonorError(f"{label}: shapeValueBody no tiene 44 valores")
    return tipo


def _slider_indices(cfg, mode):
    idx = []
    for g in mode["sliders"]:
        idx += cfg["grupos_sliders"][g]
    return sorted(set(idx))


def _bones(card):
    return _fields(card["KKEx"].data, ABM).get("boneData") or []


def _set_bones(card, bones):
    kkex = card["KKEx"].data
    entry = kkex.get(ABM)
    if not entry or not isinstance(entry[1], dict):
        if not bones:
            return
        kkex[ABM] = [2, {"boneData": bones}]
    else:
        entry[1]["boneData"] = bones


def apply_donor(receptor, donor, mode_name, body_guid="fijo", donor_label="", cfg=None):
    """Modifica `receptor` en memoria. Devuelve la lista de cambios (para el log).
    body_guid: 'donante' (copia el BodyGUID del donante) o 'fijo' (siempre el de config)."""
    cfg = cfg or load_config()
    mode = cfg["modos"][mode_name]
    if body_guid not in BODY_GUID_MODES:
        raise DonorError(f"body_guid debe ser uno de {BODY_GUID_MODES}")
    check_compatible(donor, "El donante")
    check_compatible(receptor, "La receptora")
    changes = []

    # 1) Sliders
    r_sv = receptor["Custom"]["body"]["shapeValueBody"]
    d_sv = donor["Custom"]["body"]["shapeValueBody"]
    changed = []
    for i in _slider_indices(cfg, mode):
        if r_sv[i] != d_sv[i]:
            changed.append(i)
        r_sv[i] = d_sv[i]
    changes.append(f"sliders {slider_ranges(_slider_indices(cfg, mode))}: "
                   f"{len(changed)} valores distintos copiados")

    # 2) Campos sueltos del cuerpo
    for f in mode["campos_cuerpo"]:
        receptor["Custom"]["body"][f] = donor["Custom"]["body"][f]
    changes.append("campos: " + ", ".join(mode["campos_cuerpo"]))

    # 3) Huesos ABMX: sustituir las categorías del modo
    cats = set(mode["huesos"])
    d_bones = [copy.deepcopy(b) for b in _bones(donor) if classify_bone(b[0]) in cats]
    r_all = _bones(receptor)
    r_keep = [b for b in r_all if classify_bone(b[0]) not in cats]
    removed = len(r_all) - len(r_keep)
    _set_bones(receptor, r_keep + d_bones)
    changes.append(f"huesos {'/'.join(mode['huesos'])}: {removed} de la receptora quitados, "
                   f"{len(d_bones)} del donante puestos")

    # 4) Plugins de cuerpo: copiar o, si el donante no lo tiene, quitar (= sin datos)
    r_kx, d_kx = receptor["KKEx"].data, donor["KKEx"].data
    for key in mode["plugins"]:
        if key in d_kx:
            r_kx[key] = copy.deepcopy(d_kx[key])
            changes.append(f"plugin {key}: copiado del donante")
        elif key in r_kx:
            del r_kx[key]
            changes.append(f"plugin {key}: quitado (el donante no lo tiene)")

    # 5) BodyGUID (modelo de cuerpo del uncensor)
    if mode["aplica_body_guid"]:
        new = cfg["body_guid_fijo"] if body_guid == "fijo" else _fields(d_kx, UNC).get("BodyGUID")
        unc = r_kx.get(UNC)
        if not unc or not isinstance(unc[1], dict):
            unc = r_kx[UNC] = [2, {"BodyGUID": None, "PenisGUID": None, "BallsGUID": None,
                                   "DisplayPenis": False, "DisplayBalls": False}]
        old = unc[1].get("BodyGUID")
        unc[1]["BodyGUID"] = new
        changes.append(f"BodyGUID: {old} -> {new} (modo '{body_guid}')")

    # 6) Altura efectiva en receptoras male: que el juego respete la altura donada
    if mode["asegurar_altura_male"] and receptor["Parameter"]["sex"] == 0:
        if _fields(r_kx, MALEH).get("MaleHeightEnabled") is not True:
            r_kx[MALEH] = [1, {"MaleHeightEnabled": True}]
            changes.append("MaleHeightEnabled puesto a True (la receptora es male)")

    # 7) Nombre de la card y entrada oculta propia
    label = base_name(donor_label or card_name(donor))
    changes.append(tag_name(receptor, label, cfg, mode_name))
    r_kx[DONOR_KEY] = [1, {"Donante": label, "Modo": mode_name,
                           "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]
    changes.append(f"entrada oculta {DONOR_KEY} escrita")
    return changes




def read_donation_info(card):
    """(donante, modo) si la card ya tiene la entrada oculta; si no, (None, None)."""
    f = _fields(card["KKEx"].data, DONOR_KEY)
    return f.get("Donante"), f.get("Modo")


def verify_donation(saved, donor, original, mode_name, body_guid="fijo", cfg=None, drop_bones=(),
                    ignore_bones=()):
    """Compara la card guardada y releída con el donante y con la receptora original.
    Devuelve lista de problemas (vacía = todo correcto). Igualdad lógica, no byte a byte.
    drop_bones: huesos que deben haber desaparecido. ignore_bones: huesos que se recalculan a propósito
    (el del pene) y se comprueban aparte; se excluyen de la comparación."""
    cfg = cfg or load_config()
    mode = cfg["modos"][mode_name]
    bad = []
    s_sv = saved["Custom"]["body"]["shapeValueBody"]
    d_sv = donor["Custom"]["body"]["shapeValueBody"]
    o_sv = original["Custom"]["body"]["shapeValueBody"]
    don_idx = set(_slider_indices(cfg, mode))
    for i in range(44):
        want = d_sv[i] if i in don_idx else o_sv[i]
        if s_sv[i] != want:
            bad.append(f"slider {i}: {s_sv[i]} != {want}")
    for f in mode["campos_cuerpo"]:
        if saved["Custom"]["body"][f] != donor["Custom"]["body"][f]:
            bad.append(f"campo {f} no coincide con el donante")
    cats = set(mode["huesos"])
    s_b = {b[0]: b for b in _bones(saved)}
    want_b = {b[0]: b for b in _bones(donor) if classify_bone(b[0]) in cats}
    want_b.update({b[0]: b for b in _bones(original) if classify_bone(b[0]) not in cats})
    for n in drop_bones:      # huesos genitales que se resetean en futa/male
        want_b.pop(n, None)
    for n in ignore_bones:
        s_b.pop(n, None)
        want_b.pop(n, None)
    if s_b != want_b:
        diff = set(s_b) ^ set(want_b)
        diff |= {n for n in set(s_b) & set(want_b) if s_b[n] != want_b[n]}
        bad.append(f"huesos distintos: {sorted(diff)[:8]}")
    # Todo lo demás de la receptora debe seguir igual
    special = set(mode["plugins"]) | {DONOR_KEY, ABM}
    if mode["aplica_body_guid"]:
        special.add(UNC)
    if mode["asegurar_altura_male"]:
        special.add(MALEH)
    s_kx, o_kx = saved["KKEx"].data, original["KKEx"].data
    for key in (set(s_kx) | set(o_kx)) - special:
        if s_kx.get(key) != o_kx.get(key):
            bad.append(f"plugin {key} cambió y no debía")
    if mode["aplica_body_guid"]:
        s_u, o_u = dict(_fields(s_kx, UNC)), dict(_fields(o_kx, UNC))
        s_g = s_u.pop("BodyGUID", None); o_u.pop("BodyGUID", None)
        want_g = cfg["body_guid_fijo"] if body_guid == "fijo" else _fields(donor["KKEx"].data, UNC).get("BodyGUID")
        if s_g != want_g:
            bad.append(f"BodyGUID {s_g} != {want_g}")
        if s_u != o_u:
            bad.append("uncensor: cambió algo más que BodyGUID")
    for key in mode["plugins"]:
        want = donor["KKEx"].data.get(key)
        if s_kx.get(key) != want:
            bad.append(f"plugin {key} no coincide con el donante")
    donor_lbl = _fields(saved["KKEx"].data, DONOR_KEY).get("Donante", "")
    want_name = base_name(card_name(original)) + name_suffix(cfg, mode_name, donor_lbl)
    if card_name(saved) != want_name:
        bad.append(f"nombre '{card_name(saved)}' != '{want_name}'")
    if saved["Parameter"]["sex"] != original["Parameter"]["sex"]:
        bad.append("el sexo cambió")
    if (summarize(saved)["tipo"] != summarize(original)["tipo"]):
        bad.append("el tipo (female/futa) cambió")
    # Lo que no debe cambiar jamás: piel y cara
    for f in ("skinMainColor", "skinSubColor", "skinId"):
        if saved["Custom"]["body"][f] != original["Custom"]["body"][f]:
            bad.append(f"{f} cambió")
    if saved["Custom"]["face"] != original["Custom"]["face"]:
        bad.append("la cara cambió")
    return bad
