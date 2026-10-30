"""Carpeta de salida compartida por las pestañas que crean cards nuevas (Female → Futa, Reparar pene)."""
import os
from pathlib import Path
from tkinter import filedialog

from ...core.settings import ROOT_DIR


class OutDirMixin:
    """Pide a la clase: self.settings, self.key, self.out_lbl (Label) y self.write(). Guarda tabs.<key>.out_dir."""

    @property
    def out_dir(self):
        return Path(self.settings.get(f"tabs.{self.key}.out_dir", str(ROOT_DIR / "salida")))

    def _update_out_label(self):
        self.out_lbl.configure(text=f"Salida: {self.out_dir}")

    def choose_out(self):
        d = filedialog.askdirectory(title="Carpeta de salida", initialdir=str(self.out_dir))
        if d:
            self.settings.set(f"tabs.{self.key}.out_dir", os.path.normpath(d))
            self._update_out_label()

    def open_out(self):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(self.out_dir)
        else:
            self.write(str(self.out_dir))
