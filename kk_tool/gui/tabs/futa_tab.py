"""Pestaña 'Female → Futa': convierte las cards MARCADAS (casillas ☐/☑).

Las casillas son independientes de la selección: hacer clic en una fila para ver su portada no
desmarca las que ya tenías marcadas.
"""
from tkinter import messagebox, ttk

from ...batch.convert import convert_cards
from .base import CardListTab
from .out_mixin import OutDirMixin


class FutaTab(OutDirMixin, CardListTab):
    key = "futa"
    title = "Female → Futa"
    checkable = True

    def build_toolbar(self, bar):
        self.btn_conv = ttk.Button(bar, text="Convertir marcadas a futa",
                                   command=self.convert_selected, state="disabled")
        self.btn_conv.pack(side="left")
        for text, cmd in (("Marcar todas", self.panel.check_all), ("Ninguna", self.panel.check_none),
                          ("Marcar las seleccionadas", self.panel.check_selected)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Carpeta de salida…", command=self.choose_out).pack(side="left", padx=(12, 6))
        ttk.Button(bar, text="Abrir salida", command=self.open_out).pack(side="left")
        self.out_lbl = ttk.Label(bar)
        self.out_lbl.pack(side="left", padx=8)
        self._update_out_label()
        bar2 = ttk.Frame(bar.master)
        bar2.pack(fill="x", padx=8, pady=(0, 2), after=bar)
        self.info_lbl = ttk.Label(bar2)
        self.info_lbl.pack(side="left")
        ttk.Label(bar2, text="   (clic en ☐ o barra espaciadora sobre las filas seleccionadas)",
                  foreground="#555").pack(side="left")

    def update_buttons(self):
        n = len(self.panel.checked_paths())
        hid = self.panel.hidden_checked_count()
        self.info_lbl.configure(text=f"Marcadas: {n}"
                                + (f" ({hid} ocultas por el filtro, también se incluyen)" if hid else ""))
        self.btn_conv.configure(state="normal" if n and not self.busy else "disabled")

    def convert_selected(self):
        sel = self.panel.checked_paths()
        if not sel or self.busy:
            return
        if not messagebox.askyesno(
                "Convertir",
                f"¿Convertir {len(sel)} card(s) marcada(s) a futa?\nLos originales no se tocan; "
                f"las nuevas irán a:\n{self.out_dir / 'male'} (con las mismas subcarpetas que la entrada)"):
            return
        out, roots = self.out_dir, self.panel.folders
        self.run_in_background(
            lambda post: convert_cards(sel, out, log=lambda m: post(self.write, m), roots=roots))
