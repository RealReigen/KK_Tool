"""Cargar y guardar cards. Único sitio que toca kkloader y el archivo en disco."""
from pathlib import Path
from kkloader import KoikatuCharaData
from kkloader.KoikatuCharaData import KKEx


def load_card(path):
    KKEx.LZ4_UNPACK = True  # imprescindible ANTES de load()
    return KoikatuCharaData.load(str(path))


def save_card(card, out_path):
    """Guarda la card. Nunca sobrescribe el archivo original."""
    out = Path(out_path).resolve()
    orig = getattr(card, "original_file_path", None)
    if orig and Path(orig).resolve() == out:
        raise ValueError(f"No se sobrescribe el original: {out}")
    if out.exists():
        raise ValueError(f"El destino ya existe, no se sobrescribe: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    KKEx.LZ4_UNPACK = True
    card.save(str(out))
    return out
