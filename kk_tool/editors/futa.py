"""Herramienta: convertir una card (ya cargada) a futa. No toca archivos."""
import json
from pathlib import Path
from ..readers.summary import UNC, TRAP, BULGE, MALEH, ABM
from .penis_size import apply_penis_size

PRESETS_FILE = Path(__file__).resolve().parent.parent / "config" / "presets.json"


def load_presets():
    return json.loads(PRESETS_FILE.read_text(encoding="utf-8"))


def reset_genital_bones(card, names):
    """Quita de boneData (ABMX) los huesos de la zona genital indicados: en ABMX un hueso
    ausente = sin modificar = valores por defecto. Devuelve lista de textos con lo quitado.
    Si la card no tiene alguno de esos huesos, no pasa nada."""
    entry = card["KKEx"].data.get(ABM)
    if not names or not entry or len(entry) < 2 or not isinstance(entry[1], dict):
        return []
    bones = entry[1].get("boneData") or []
    names = set(names)
    removed = []
    for b in bones:
        if b[0] in names:
            try:
                sc = [round(float(v), 3) for v in b[1][0][0]]
            except (IndexError, TypeError):
                sc = "?"
            removed.append(f"{b[0]} (escala {sc})")
    if removed:
        entry[1]["boneData"] = [b for b in bones if b[0] not in names]
    return removed


def apply_futa(card, preset):
    """Aplica TODO el perfil futa de una vez (atómico). Modifica la card en memoria.
    No toca los sliders de altura ni el resto de huesos: la altura se conserva.
    Sí resetea los huesos de la zona genital (preset['reset_huesos']) para que el pene no
    salga deformado, y fija el tamaño del pene (preset['pene'], ver editors/penis_size.py).
    Devuelve (huesos_reseteados, texto_del_pene) para el log."""
    kkex = card["KKEx"].data
    card["Parameter"]["sex"] = 0

    kkex[TRAP] = [1, {"IsTrap": bool(preset["is_trap"]), "IdleAnimation": None}]

    unc = kkex.get(UNC)
    if not unc or not isinstance(unc[1], dict):
        unc = kkex[UNC] = [2, {}]
    unc[1].update({
        "BodyGUID": preset["body"],
        "PenisGUID": preset["penis"],
        "BallsGUID": preset["balls"],
        "DisplayPenis": bool(preset["display_penis"]),
        "DisplayBalls": bool(preset["display_balls"]),
    })

    if preset.get("enable_bulge") is not None:
        bulge = kkex.get(BULGE)
        if bulge and isinstance(bulge[1], dict):
            bulge[1]["EnableBulge"] = preset["enable_bulge"]
        else:
            kkex[BULGE] = [1, {"EnableBulge": preset["enable_bulge"], "BulgeSize": 0.5}]

    if preset.get("male_height_enabled"):
        kkex[MALEH] = [1, {"MaleHeightEnabled": True}]
    reset = reset_genital_bones(card, preset.get("reset_huesos"))
    return reset, apply_penis_size(card, preset.get("pene"))
