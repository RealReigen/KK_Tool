"""Dado el sitio donde está instalado Koikatsu, encuentra UserData/chara/female y /male. Lógica pura.

Acepta lo que sea más cómodo señalar: la carpeta de la instalación (la que tiene UserData dentro),
la propia UserData, la carpeta chara, o directamente female o male.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class GamePaths:
    install: Path      # carpeta de la instalación (la que contiene UserData)
    chara: Path        # <instalación>/UserData/chara
    female: Path
    male: Path


def _chara_candidates(p):
    yield p / "UserData" / "chara"
    if p.name.lower() == "userdata":
        yield p / "chara"
    if p.name.lower() == "chara":
        yield p
    if p.name.lower() in ("female", "male"):
        yield p.parent


def resolve_install(path) -> Optional[GamePaths]:
    """GamePaths si `path` es (o está dentro de) una instalación con UserData/chara/female; si no, None.
    La carpeta male no tiene por qué existir todavía (se crea al guardar la primera card)."""
    if not path:
        return None
    p = Path(path)
    for chara in _chara_candidates(p):
        if (chara / "female").is_dir():
            install = chara.parent.parent if chara.parent.name.lower() == "userdata" else chara.parent
            return GamePaths(install=install, chara=chara, female=chara / "female", male=chara / "male")
    return None
