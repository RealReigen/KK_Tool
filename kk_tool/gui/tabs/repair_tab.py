"""Pestaña 'Reparar pene': corrige el tamaño del pene de futas YA hechas (copias nuevas, nunca sobrescribe)."""
from tkinter import messagebox, ttk

from ...batch.repair import OUT_SUBDIR, repair_cards
from ...editors.futa import load_presets
from ...editors.penis_size import needs_repair
from .base import BASE_COLUMNS, CardListTab
from ..widgets.card_panel import PENE_COLUMN
from .out_mixin import OutDirMixin


class RepairTab(OutDirMixin, CardListTab):
    key = "reparar"
    title = "Reparar pene (futas)"
    columns = BASE_COLUMNS + [PENE_COLUMN]

    def build_toolbar(self, bar):
        ttk.Button(bar, text="Seleccionar las que lo necesitan", command=self.select_needed).pack(side="left")
        self.btn_fix = ttk.Button(bar, text="Reparar seleccionadas", command=self.repair_selected, state="disabled")
        self.btn_fix.pack(side="left", padx=6)
        ttk.Button(bar, text="Carpeta de salida…", command=self.choose_out).pack(side="left")
        ttk.Button(bar, text="Abrir salida", command=self.open_out).pack(side="left", padx=6)
        self.out_lbl = ttk.Label(bar)
        self.out_lbl.pack(side="left", padx=8)
        self._update_out_label()

    def update_buttons(self):
        self.btn_fix.configure(state="normal" if self.tree.selection() and not self.busy else "disabled")

    def _cfg(self):
        return load_presets()["futa_bp_sos"].get("pene")

    def select_needed(self):
        """Selecciona, entre las filas visibles (respeta búsqueda y filtros), las futas con el pene fuera de referencia."""
        cfg = self._cfg()
        todo = [i for i in self.tree.get_children()
                if self.panel.summaries.get(i) and needs_repair(self.panel.summaries[i], cfg)]
        self.tree.selection_set(todo)
        if todo:
            self.tree.see(todo[0])
        self.write(f"{len(todo)} futa(s) con el pene fuera de referencia seleccionada(s)"
                   f" (de {len(self.tree.get_children())} visibles).")
        self.panel._on_select()

    def repair_selected(self):
        sel = self.selection_paths()
        if not sel or self.busy:
            return
        if not messagebox.askyesno(
                "Reparar pene",
                f"¿Reparar el pene de {len(sel)} card(s)?\nLos originales no se tocan; las copias irán a:\n"
                f"{self.out_dir / OUT_SUBDIR} (con las mismas subcarpetas que la entrada).\n"
                "Las que no son futa completa o ya están bien se omiten."):
            return
        out, roots = self.out_dir, self.panel.folders
        self.run_in_background(
            lambda post: repair_cards(sel, out, log=lambda m: post(self.write, m), roots=roots))
