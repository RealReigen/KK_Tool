"""Repara el tamaño del pene de futas YA hechas. Nunca sobrescribe: guarda copias nuevas.

Salida: <out_root>/reparadas/<mismas subcarpetas que la entrada>/<nombre>.png
Solo toca el hueso del pene (cm_J_dan100_00); tras guardar relee la copia y comprueba que el tamaño
efectivo es el de referencia y que NADA más cambió respecto al original.
"""
from datetime import datetime
from pathlib import Path
from ..core.card_io import load_card, save_card
from ..editors.donor import card_name
from ..editors.futa import load_presets
from ..editors.penis_size import apply_penis_size, effective_size, needs_repair, reference, verify_penis_size
from ..readers.summary import ABM, PENIS_BONE, summarize, _fields
from .convert import _free_name, relative_parent

OUT_SUBDIR = "reparadas"


def _bones_without_penis(card):
    return {b[0]: b for b in (_fields(card["KKEx"].data, ABM).get("boneData") or []) if b[0] != PENIS_BONE}


def verify_repair(saved, original):
    """Problemas (lista vacía = solo cambió el hueso del pene). Igualdad lógica, no byte a byte."""
    bad = []
    if saved["Parameter"]["sex"] != original["Parameter"]["sex"]:
        bad.append("el sexo cambió")
    if card_name(saved) != card_name(original):
        bad.append("el nombre cambió")
    for k in original["Custom"]["body"].keys():
        if saved["Custom"]["body"][k] != original["Custom"]["body"][k]:
            bad.append(f"cuerpo: {k} cambió")
    if saved["Custom"]["face"] != original["Custom"]["face"]:
        bad.append("la cara cambió")
    s_kx, o_kx = saved["KKEx"].data, original["KKEx"].data
    for key in (set(s_kx) | set(o_kx)) - {ABM}:
        if s_kx.get(key) != o_kx.get(key):
            bad.append(f"plugin {key} cambió")
    if _bones_without_penis(saved) != _bones_without_penis(original):
        bad.append("otros huesos ABMX cambiaron")
    if summarize(saved)["tipo"] != "futa":
        bad.append(f"ya no es futa ({summarize(saved)['tipo']})")
    return bad


def repair_cards(paths, out_root, preset_name="futa_bp_sos", log=print, roots=None):
    """Devuelve (reparadas, omitidas, con_problemas)."""
    cfg = load_presets()[preset_name].get("pene")
    out_dir = Path(out_root) / OUT_SUBDIR
    lines, ok, skipped, failed = [], 0, 0, 0

    def say(msg):
        lines.append(msg)
        log(msg)

    say(f"Referencia del pene: tamaño efectivo {reference(cfg)} | salida: {out_dir}")
    for p in map(Path, paths):
        try:
            card = load_card(p)
            before = summarize(card)
            if before["tipo"] != "futa":
                why = ("no es futa completa: conviértela en «Female → Futa»"
                       if before["tipo"] == "futa incompleta" else f"es {before['tipo']}, no futa")
                say(f"OMITIDA ({why}): {p.name}")
                skipped += 1
                continue
            if not needs_repair(before, cfg):
                say(f"OMITIDA (el pene ya está bien: {before['pene_efectivo']}): {p.name}")
                skipped += 1
                continue
            original = load_card(p)               # copia intacta para verificar
            note = apply_penis_size(card, cfg)
            sub = relative_parent(p, roots)
            dest = save_card(card, _free_name(out_dir / sub, p.name))
            shown = (sub / dest.name).as_posix() if sub != Path(".") else dest.name
            saved = load_card(dest)
            problems = verify_penis_size(saved, cfg) + verify_repair(saved, original)
            if problems:
                say(f"AVISO: {p.name} -> {OUT_SUBDIR}/{shown} guardada pero la verificación falló:")
                for x in problems:
                    say(f"    - {x}")
                failed += 1
                continue
            say(f"OK: {p.name} -> {OUT_SUBDIR}/{shown} (verificada)")
            say(f"    {note}")
            say(f"    pene efectivo: {before['pene_efectivo']} -> {effective_size(saved)} | nada más cambió")
            ok += 1
        except Exception as e:
            say(f"ERROR: {p.name}: {type(e).__name__}: {e}")
            failed += 1

    say(f"\nResumen: {ok} reparadas, {skipped} omitidas, {failed} con problemas.")
    Path(out_root).mkdir(parents=True, exist_ok=True)
    with open(Path(out_root) / "log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} (reparar pene) ---\n" + "\n".join(lines) + "\n")
    return ok, skipped, failed
