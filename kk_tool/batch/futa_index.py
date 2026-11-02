"""Índice de la carpeta de salida (male/) por huella de contenido: «¿esta futa ya está hecha?».

- Una card de male/ cuenta como «ya hecha» si su huella coincide (ver readers/fingerprint.py).
- Lo que está en male/duplicados/ se guarda aparte: NO cuenta como «ya hecha» (solo sirve para no
  amontonar más copias de lo mismo).
- La lectura usa la caché de huellas: la primera vez lee todas las cards; después solo las nuevas o cambiadas.
"""
from pathlib import Path

from ..core.card_io import load_card
from ..readers.fingerprint import fingerprint
from .fp_cache import FingerprintCache
from .scan import find_cards

DUP_SUBDIR = "duplicados"


class FutaIndex:
    def __init__(self, cache=None):
        self.cache = cache if cache is not None else FingerprintCache()
        self.folder = None
        self.by_fp = {}          # huella -> [(ruta, está_en_duplicados)]
        self.unreadable = 0

    def _rel(self, path):
        """Ruta relativa a la carpeta indexada (sin tocar el disco; con resolve() solo si hace falta)."""
        path = Path(path)
        try:
            return path.relative_to(self.folder)
        except (ValueError, TypeError):
            try:
                return path.resolve().relative_to(self.folder.resolve())
            except (ValueError, AttributeError, OSError):
                return None

    def add(self, fp, path):
        rel = self._rel(path)
        in_dups = rel is not None and DUP_SUBDIR in rel.parts[:-1]
        self.by_fp.setdefault(fp, []).append((Path(path), in_dups))

    def find_main(self, fp):
        """Ruta de una card de male/ (fuera de duplicados/) con esa huella, o None."""
        return next((p for p, dup in self.by_fp.get(fp, ()) if not dup), None)

    def find_dups(self, fp):
        """Ruta de una card de male/duplicados/ con esa huella, o None."""
        return next((p for p, dup in self.by_fp.get(fp, ()) if dup), None)

    def shown(self, path):
        """Ruta relativa a la carpeta indexada (para mostrarla)."""
        rel = self._rel(path)
        return rel.as_posix() if rel is not None else str(path)

    def __len__(self):
        return sum(len(v) for v in self.by_fp.values())

    def scan(self, folder, progress=None, log=print):
        """(Re)construye el índice de `folder`. progress(i, n) se llama por cada card.
        Una card que no se pueda leer se avisa y se ignora: no detiene el índice."""
        self.folder = Path(folder)
        self.by_fp, self.unreadable = {}, 0
        if not self.folder.is_dir():
            return
        cards = find_cards(self.folder)
        seen = set()
        for i, p in enumerate(cards, 1):
            if progress:
                progress(i, len(cards))
            seen.add(str(p.resolve()))
            fp = self.cache.get(p)
            if fp is None:
                try:
                    fp = fingerprint(load_card(p))
                    self.cache.put(p, fp)
                except Exception as e:
                    self.unreadable += 1
                    log(f"[índice] no se pudo leer {self.shown(p)}: {type(e).__name__}: {e}")
                    continue
            self.add(fp, p)
        self.cache.retain_under(self.folder, seen)
        try:
            self.cache.save()
        except OSError as e:
            log(f"[índice] no se pudo guardar la caché de huellas: {e}")
