"""Convierte varias cards a futa. Nunca sobrescribe originales ni salidas previas.

Las futas nuevas van a la carpeta de salida (la male/ del juego). Si el contenido de una card ya está
en esa carpeta (comparación por huella de contenido, ver readers/fingerprint.py), la futa se guarda en
<salida>/duplicados/ en vez de repetirla.
Las cards que fallan se copian (el original) a <report_dir>/errores/ con un .txt con el motivo;
el registro (log.txt) también va a <report_dir>.
"""
import shutil
from datetime import datetime
from pathlib import Path
from ..core.card_io import load_card, save_card
from ..readers.fingerprint import fingerprint
from ..readers.summary import summarize, _fields, ABM
from ..editors.futa import apply_futa, load_presets
from ..editors.penis_size import verify_penis_size
from .futa_index import DUP_SUBDIR

ERR_SUBDIR = "errores"


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


def copy_to_errors(path, report_dir, roots, reason):
    """Copia el ORIGINAL a <report_dir>/errores/<subcarpetas>/ y escribe <nombre>.txt con el motivo.
    Devuelve la ruta mostrada (relativa a errores/). Nunca sobrescribe."""
    sub = relative_parent(path, roots)
    folder = Path(report_dir) / ERR_SUBDIR / sub
    folder.mkdir(parents=True, exist_ok=True)
    dest = _free_name(folder, Path(path).name)
    shutil.copy2(path, dest)
    dest.with_suffix(".txt").write_text(
        f"Archivo original: {path}\nFecha: {datetime.now():%Y-%m-%d %H:%M:%S}\nMotivo: {reason}\n",
        encoding="utf-8")
    return (sub / dest.name).as_posix() if sub != Path(".") else dest.name


def _alt(s):
    return f"slider {s['altura_slider']} / hueso {s['altura_hueso']}"


def convert_cards(paths, out_male, report_dir, preset_name="futa_bp_sos", log=print, roots=None, index=None):
    """Convierte `paths` a futa y las guarda en `out_male` (la carpeta male/ del juego).
    roots: carpetas de entrada; si se dan, la salida repite la estructura de subcarpetas:
           <entrada>/A/B/x.png -> <out_male>/A/B/x.png (y, si falla, <report_dir>/errores/A/B/x.png).
    index: FutaIndex ya construido sobre out_male. Con él, una card cuyo contenido ya está en out_male
           se guarda en <out_male>/duplicados/ (y si ya estaba también ahí, se omite). Sin él no se
           comprueba nada. El índice se actualiza con cada card guardada.
    Devuelve (convertidas, omitidas, con_problemas, duplicadas)."""
    preset = load_presets()[preset_name]
    out_male = Path(out_male)
    report_dir = Path(report_dir)
    lines, ok, skipped, failed, dups = [], 0, 0, 0, 0

    def say(msg):
        lines.append(msg)
        log(msg)

    def fail(p, reason):
        """Copia el original a errores/ (un fallo al copiar no detiene el lote)."""
        try:
            shown = copy_to_errors(p, report_dir, roots, reason)
            say(f"    -> original copiado a {ERR_SUBDIR}/{shown}")
        except Exception as e2:
            say(f"    (no se pudo copiar a {ERR_SUBDIR}/: {type(e2).__name__}: {e2})")

    for p in map(Path, paths):
        try:
            card = load_card(p)
            before = summarize(card)
            if before["tipo"] == "futa":
                say(f"OMITIDA (ya es futa completa): {p.name}")
                skipped += 1
                continue
            fp = fingerprint(card) if index is not None else None      # antes de tocar nada
            dup_of = index.find_main(fp) if fp else None
            if dup_of is not None and index.find_dups(fp):
                say(f"OMITIDA (duplicada: ya está en {out_male.name}/{index.shown(dup_of)} "
                    f"y también en {DUP_SUBDIR}/): {p.name}")
                skipped += 1
                continue
            reset, pene_txt = apply_futa(card, preset)
            sub = relative_parent(p, roots)
            dest_root = out_male / DUP_SUBDIR if dup_of is not None else out_male
            dest = save_card(card, _free_name(dest_root / sub, p.name))
            shown = (sub / dest.name).as_posix() if sub != Path(".") else dest.name
            if dup_of is not None:
                shown = f"{DUP_SUBDIR}/{shown}"
            after = summarize(load_card(dest))  # verificación releyendo lo guardado
            same_h = (before["altura_slider"], before["altura_hueso"]) == \
                     (after["altura_slider"], after["altura_hueso"])
            if after["tipo"] != "futa":
                reason = f"guardada pero no queda como futa ({after['tipo']})"
                say(f"AVISO: {p.name} {reason}")
                fail(p, reason)
                failed += 1
                continue
            saved = load_card(dest)
            pene_bad = verify_penis_size(saved, preset.get("pene"))
            if pene_bad:
                reason = "; ".join(pene_bad)
                say(f"AVISO: {p.name}: {reason}")
                fail(p, reason)
                failed += 1
                continue
            left = [b[0] for b in (_fields(saved["KKEx"].data, ABM).get("boneData") or [])
                    if b[0] in set(preset.get("reset_huesos") or [])]
            if left:
                reason = f"tras guardar siguen estos huesos genitales: {left}"
                say(f"AVISO: {p.name}: {reason}")
                fail(p, reason)
                failed += 1
                continue
            fp_saved = fingerprint(saved) if fp else None
            if fp and fp_saved != fp:
                say(f"AVISO: {p.name}: la huella de contenido de la copia no coincide con la del original; "
                    "esta card no se reconocerá como duplicada en el futuro (avísame si ves este mensaje)")
            if dup_of is not None:
                say(f"DUPLICADA: {p.name} ya estaba en {out_male.name}/{index.shown(dup_of)} "
                    f"-> guardada en {out_male.name}/{shown}")
                dups += 1
            else:
                say(f"OK: {p.name} [{before['tipo']} -> futa] -> {out_male.name}/{shown}")
            if fp_saved:
                index.add(fp_saved, dest)       # lo que vería un nuevo escaneo de la carpeta
            say("    genitales: " + ("reseteados a por defecto: " + ", ".join(reset) if reset
                                     else "ya estaban por defecto (nada que resetear)"))
            if pene_txt:
                say("    " + pene_txt)
            say(f"    altura antes: {_alt(before)} | despues: {_alt(after)} "
                f"{'(conservada)' if same_h else '(¡CAMBIÓ!)'}")
            ok += 1 if dup_of is None else 0
        except Exception as e:
            say(f"ERROR: {p.name}: {type(e).__name__}: {e}")
            fail(p, f"{type(e).__name__}: {e}")
            failed += 1

    say(f"\nResumen: {ok} convertidas, {dups} duplicadas (en {DUP_SUBDIR}/), {skipped} omitidas, "
        f"{failed} con problemas" + (f" (originales en {report_dir / ERR_SUBDIR})." if failed else "."))
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n" + "\n".join(lines) + "\n")
    return ok, skipped, failed, dups
