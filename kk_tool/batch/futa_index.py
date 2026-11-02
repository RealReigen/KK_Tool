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
        self.folder = None       # carpeta principal (la salida)
        self.roots = []          # principal + carpetas extra con las que también se compara
        self.by_fp = {}          # huella -> [(ruta, está_en_duplicados)]
        self.unreadable = 0

    def _locate(self, path):
        """(carpeta_indexada, ruta_relativa) de `path`, o (None, None) si no cuelga de ninguna."""
        path = Path(path)
        for root in self.roots:
            try:
                return root, path.relative_to(root)
            except (ValueError, TypeError):
                pass
        for root in self.roots:
            try:
                return root, path.resolve().relative_to(root.resolve())
            except (ValueError, AttributeError, OSError):
                pass
        return None, None

    def add(self, fp, path):
        root, rel = self._locate(path)
        in_dups = rel is not None and DUP_SUBDIR in rel.parts[:-1]
        self.by_fp.setdefault(fp, []).append((Path(path), in_dups))

    def find_main(self, fp):
        """Ruta de una card (fuera de duplicados/) con esa huella, o None."""
        return next((p for p, dup in self.by_fp.get(fp, ()) if not dup), None)

    def find_dups(self, fp):
        """Ruta de una card de duplicados/ con esa huella, o None."""
        return next((p for p, dup in self.by_fp.get(fp, ()) if dup), None)

    def shown(self, path):
        """Texto para mostrar: relativo a la carpeta principal; si está en una carpeta extra, ruta completa."""
        root, rel = self._locate(path)
        if rel is None:
            return str(path)
        return rel.as_posix() if root == self.folder else str(path)

    def __len__(self):
        return sum(len(v) for v in self.by_fp.values())

    def scan(self, folder, progress=None, log=print, extra=()):
        """(Re)construye el índice de `folder` (+ las carpetas `extra`). progress(i, n) por cada card.
        Una card que no se pueda leer se avisa y se ignora: no detiene el índice."""
        self.folder = Path(folder)
        self.roots = [self.folder]
        for e in extra:
            e = Path(e)
            if e.is_dir() and all(e.resolve() != r.resolve() for r in self.roots):
                self.roots.append(e)
        self.by_fp, self.unreadable = {}, 0
        cards = []
        for root in self.roots:
            if root.is_dir():
                cards += find_cards(root)
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
        for root in self.roots:
            self.cache.retain_under(root, seen)
        try:
            self.cache.save()
        except OSError as e:
            log(f"[índice] no se pudo guardar la caché de huellas: {e}")
