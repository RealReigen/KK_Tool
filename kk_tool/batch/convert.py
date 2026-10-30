"""Convierte varias cards a futa. Nunca sobrescribe originales ni salidas previas."""
from datetime import datetime
from pathlib import Path
from ..core.card_io import load_card, save_card
from ..readers.summary import summarize, _fields, ABM
from ..editors.futa import apply_futa, load_presets
from ..editors.penis_size import verify_penis_size


def _free_name(folder, name):
    dest = Path(folder) / name
    n = 1
    while dest.exists():
        dest = Path(folder) / f"{Path(name).stem}_{n}{Path(name).suffix}"
        n += 1
    return dest


def relative_parent(path, roots):
    """Subcarpetas de `path` respecto a la carpeta de entrada que la contiene (la más específica).
    Si no cuelga de ninguna (o roots está vacío) devuelve Path('.') = sin subcarpetas."""
    path = Path(path).resolve()
    best = None
    for r in roots or []:
        try:
            rel = path.parent.relative_to(Path(r).resolve())
        except ValueError:
            continue
        if best is None or len(rel.parts) < len(best.parts):   # carpeta de entrada más profunda
            best = rel
    return best if best is not None else Path(".")


def _alt(s):
    return f"slider {s['altura_slider']} / hueso {s['altura_hueso']}"


def convert_cards(paths, out_root, preset_name="futa_bp_sos", log=print, roots=None):
    """roots: carpetas de entrada; si se dan, la salida repite la estructura de subcarpetas:
    <entrada>/A/B/x.png -> <salida>/male/A/B/x.png"""
    preset = load_presets()[preset_name]
    out_male = Path(out_root) / "male"
    lines, ok, skipped, failed = [], 0, 0, 0

    def say(msg):
        lines.append(msg)
        log(msg)

    for p in map(Path, paths):
        try:
            card = load_card(p)
            before = summarize(card)
            if before["tipo"] == "futa":
                say(f"OMITIDA (ya es futa completa): {p.name}")
                skipped += 1
                continue
            reset, pene_txt = apply_futa(card, preset)
            sub = relative_parent(p, roots)
            dest = save_card(card, _free_name(out_male / sub, p.name))
            shown = (sub / dest.name).as_posix() if sub != Path(".") else dest.name
            after = summarize(load_card(dest))  # verificación releyendo lo guardado
            same_h = (before["altura_slider"], before["altura_hueso"]) == \
                     (after["altura_slider"], after["altura_hueso"])
            if after["tipo"] != "futa":
                say(f"AVISO: {p.name} guardada pero no queda como futa ({after['tipo']})")
                failed += 1
                continue
            saved = load_card(dest)
            pene_bad = verify_penis_size(saved, preset.get("pene"))
            if pene_bad:
                say(f"AVISO: {p.name}: {'; '.join(pene_bad)}")
                failed += 1
                continue
            left = [b[0] for b in (_fields(saved["KKEx"].data, ABM).get("boneData") or [])
                    if b[0] in set(preset.get("reset_huesos") or [])]
            if left:
                say(f"AVISO: {p.name}: tras guardar siguen estos huesos genitales: {left}")
                failed += 1
                continue
            say(f"OK: {p.name} [{before['tipo']} -> futa] -> male/{shown}")
            say("    genitales: " + ("reseteados a por defecto: " + ", ".join(reset) if reset
                                     else "ya estaban por defecto (nada que resetear)"))
            if pene_txt:
                say("    " + pene_txt)
            say(f"    altura antes: {_alt(before)} | despues: {_alt(after)} "
                f"{'(conservada)' if same_h else '(¡CAMBIÓ!)'}")
            ok += 1
        except Exception as e:
            say(f"ERROR: {p.name}: {type(e).__name__}: {e}")
            failed += 1

    say(f"\nResumen: {ok} convertidas, {skipped} omitidas, {failed} con problemas.")
    Path(out_root).mkdir(parents=True, exist_ok=True)
    with open(Path(out_root) / "log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n" + "\n".join(lines) + "\n")
    return ok, skipped, failed
