"""Dona el cuerpo de un donante a varias receptoras. Nunca sobrescribe nada.

Salida: <out_root>/<nombre del donante>/<female|male>/<nombre del personaje receptor>_<modo>.png
Con make_futa=True la receptora se convierte a futa en la misma operación (queda en male/).
"""
import re
from datetime import datetime
from pathlib import Path
from ..core.card_io import load_card, save_card
from ..editors import cover_text
from ..editors.donor import (apply_donor, verify_donation, check_compatible, card_name, base_name,
                             load_config, DonorError)
from ..editors.futa import apply_futa, load_presets, reset_genital_bones
from ..editors.penis_size import apply_penis_size, verify_penis_size
from ..readers.summary import PENIS_BONE
from ..readers.summary import summarize
from .convert import _free_name

_BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(text, fallback="sin_nombre"):
    """Quita los caracteres que Windows no admite (y puntos/espacios finales)."""
    s = _BAD.sub("", text or "").strip().rstrip(". ")
    return s or fallback


def donation_folder(donor_path, out_root):
    """Carpeta de salida de un donante: <salida>/<nombre del donante>."""
    donor_path = Path(donor_path)
    name = base_name(card_name(load_card(donor_path), donor_path.stem))
    return Path(out_root) / safe_name(name, donor_path.stem)


def donate_cards(donor_path, receptor_paths, mode_name, out_root, body_guid="fijo",
                 log=print, with_cover=None, make_futa=False, futa_preset="futa_bp_sos"):
    """Crea una copia de cada receptora con el cuerpo del donante. Devuelve (ok, omitidas, fallidas).
    with_cover: None = lo que diga config['portada']['activa']; True/False = forzar.
    make_futa: además de donar el cuerpo, convierte la receptora a futa (perfil `futa_preset`).
               Las female/futa incompleta se convierten; las futa ya completas se donan tal cual;
               las male nativas se omiten.
    Si la franja está activa y falta Pillow, falla ANTES de crear nada."""
    cfg = load_config()
    mode = cfg["modos"][mode_name]
    style = cfg["portada"]
    use_cover = style["activa"] if with_cover is None else with_cover
    if use_cover and not cover_text.pillow_available():
        raise DonorError("Falta la librería Pillow (necesaria para la franja de la portada). "
                         "Ejecuta instalar.bat otra vez, o: python -m pip install pillow")
    donor_path = Path(donor_path)
    preset = load_presets()[futa_preset]     # perfil futa y lista de huesos genitales a resetear
    genital = list(preset.get("reset_huesos") or [])
    pene_cfg = preset.get("pene")
    changes_height = "ALTURA" in mode["huesos"]    # el modo copia la altura del donante
    lines, ok, skipped, failed = [], 0, 0, 0

    def say(msg):
        lines.append(msg)
        log(msg)

    donor = load_card(donor_path)
    check_compatible(donor, "El donante")
    donor_name = base_name(card_name(donor, donor_path.stem))
    folder = donation_folder(donor_path, out_root)
    say(f"Donante: {donor_name} ({donor_path.name}) | modo: {mode_name} | "
        f"BodyGUID: {body_guid} | futa: {'sí (' + futa_preset + ')' if make_futa else 'no'} | salida: {folder}")

    for p in map(Path, receptor_paths):
        try:
            if p.resolve() == donor_path.resolve():
                say(f"OMITIDA (es el propio donante): {p.name}")
                skipped += 1
                continue
            card = load_card(p)
            original = load_card(p)     # copia intacta para verificar después
            changes = []
            fixed_penis = False          # ¿hay que fijar/verificar el tamaño del pene en esta card?
            if make_futa:
                # 1º futa, 2º cuerpo: el cuerpo se dona sobre una futa (camino ya verificado).
                # `original` pasa a ser "la receptora ya futa" para que la verificación compare bien.
                check_compatible(card, "La receptora")          # rechaza male nativa
                tipo0 = summarize(card)["tipo"]
                if tipo0 == "futa":
                    changes.append("futa: la receptora ya era futa completa (no se toca)")
                else:
                    reset0, _pene0 = apply_futa(card, preset)
                    apply_futa(original, preset)
                    fixed_penis = True
                    changes.append(f"futa: {tipo0} -> futa (perfil {futa_preset}: sex=0, IsTrap, "
                                   f"pene, Bulge desactivado, MaleHeightEnabled)")
                    if reset0:
                        changes.append("genitales de la receptora reseteados: " + ", ".join(reset0))
            changes += apply_donor(card, donor, mode_name, body_guid, donor_label=donor_name, cfg=cfg)
            if card["Parameter"]["sex"] == 0:
                # futa/male: el cuerpo donado trae los huesos genitales de una female; se resetean
                # para que el pene no quede deformado (en female no se tocan).
                rm = reset_genital_bones(card, genital)
                if rm:
                    changes.append("genitales (huesos del donante) reseteados a por defecto: " + ", ".join(rm))
                # la altura acaba de cambiar (modo con altura) o la receptora acaba de hacerse futa:
                # el tamaño del pene se recalcula con la altura FINAL
                if fixed_penis or changes_height:
                    changes.append(apply_penis_size(card, pene_cfg))
                    fixed_penis = True
            if use_cover:
                font = cover_text.stamp_cover(card, style["texto"].format(donante=donor_name), style)
                changes.append(f"portada: franja '{style['texto'].format(donante=donor_name)}' (fuente: {font})")
            sub = "female" if card["Parameter"]["sex"] == 1 else "male"
            # el archivo se llama como el personaje ORIGINAL (sin la etiqueta [cuerpo: …] del nombre)
            fname = f"{safe_name(base_name(card_name(original, p.stem)), p.stem)}{mode['sufijo']}.png"
            dest = save_card(card, _free_name(folder / sub, fname))
            saved = load_card(dest)
            problems = verify_donation(saved, donor, original, mode_name, body_guid, cfg,
                                       drop_bones=genital if saved["Parameter"]["sex"] == 0 else (),
                                       ignore_bones=(PENIS_BONE,) if fixed_penis else ())
            if fixed_penis:
                problems += verify_penis_size(saved, pene_cfg)
            if make_futa and summarize(saved)["tipo"] != "futa":
                problems.append(f"no queda como futa ({summarize(saved)['tipo']})")
            if use_cover:
                problems += cover_text.verify_stamp(saved, original, style)
            if problems:
                say(f"AVISO: {p.name} -> {dest.name} guardada pero la verificación falló:")
                for x in problems:
                    say(f"    - {x}")
                failed += 1
                continue
            say(f"OK: {p.name} [{sub}] -> {sub}/{dest.name} (verificada)")
            for c in changes:
                say(f"    · {c}")
            ok += 1
        except DonorError as e:
            say(f"OMITIDA: {p.name}: {e}")
            skipped += 1
        except Exception as e:
            say(f"ERROR: {p.name}: {type(e).__name__}: {e}")
            failed += 1

    say(f"\nResumen: {ok} creadas, {skipped} omitidas, {failed} con problemas.")
    Path(out_root).mkdir(parents=True, exist_ok=True)
    with open(Path(out_root) / "log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} (donacion) ---\n" + "\n".join(lines) + "\n")
    return ok, skipped, failed
