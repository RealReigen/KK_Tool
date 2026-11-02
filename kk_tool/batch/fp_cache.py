"""Caché de huellas en disco (huellas_cache.json junto a settings.json). Sin GUI.

Leer una card entera es lo caro (algunas pesan MB). Con la caché, indexar male/ solo relee las cards
nuevas o cambiadas: la entrada vale mientras coincidan fecha de modificación, tamaño y versión de la huella.
Un archivo dañado se ignora (se empieza limpio); borrarlo es siempre seguro.
"""
import json
import os
from pathlib import Path

from ..core.settings import ROOT_DIR
from ..readers.fingerprint import FP_VERSION

CACHE_FILE = ROOT_DIR / "huellas_cache.json"


def _key(path):
    return str(Path(path).resolve())


class FingerprintCache:
    def __init__(self, path=CACHE_FILE):
        self.path = Path(path)
        self.data = {}          # ruta -> [mtime_ns, tamaño, versión, huella]
        self.dirty = False
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                self.data = d
        except Exception:
            self.data = {}

    def get(self, path):
        """Huella guardada si el archivo no cambió desde entonces; si no, None."""
        try:
            st = os.stat(path)
        except OSError:
            return None
        e = self.data.get(_key(path))
        if (isinstance(e, list) and len(e) == 4 and e[0] == st.st_mtime_ns
                and e[1] == st.st_size and e[2] == FP_VERSION):
            return e[3]
        return None

    def put(self, path, fp):
        st = os.stat(path)
        self.data[_key(path)] = [st.st_mtime_ns, st.st_size, FP_VERSION, fp]
        self.dirty = True

    def retain_under(self, folder, seen_keys):
        """Quita las entradas de `folder` que ya no existen (no están en seen_keys)."""
        root = _key(folder)
        stale = [k for k in self.data
                 if (k.startswith(root + os.sep) or k.startswith(root + "/")) and k not in seen_keys]
        for k in stale:
            del self.data[k]
        if stale:
            self.dirty = True

    def save(self):
        if not self.dirty:
            return
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)        # escritura atómica, como settings.json
        self.dirty = False
