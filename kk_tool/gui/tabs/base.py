"""Base común de las pestañas con lista de cards + visor de portada + registro.
Una pestaña nueva = una clase que hereda de CardListTab en su propio archivo.
La lista, las carpetas y el visor viven en widgets/card_panel.py (CardPanel)."""
import tkinter as tk
from tkinter import messagebox, ttk

from ..widgets.card_panel import BASE_COLUMNS, CardPanel  # noqa: F401  (BASE_COLUMNS se reexporta)
from ..widgets.worker import Worker


class CardListTab(ttk.Frame):
    key = "base"          # clave en settings.json (única por pestaña)
    title = "Base"        # texto de la pestaña
    columns = BASE_COLUMNS
    checkable = False     # True = la lista lleva casillas ☐/☑ (marcar no depende de la selección del visor)

    def __init__(self, master, settings):
        super().__init__(master)
        self.settings = settings
        self.worker = Worker(self, on_state=lambda _b: self._sync_buttons(),
                             on_error=lambda e: self.write(f"ERROR: {type(e).__name__}: {e}"))

        # zona central redimensionable: (panel = carpetas + lista + visor) arriba, registro abajo
        self.outer = ttk.Panedwindow(self, orient="vertical")
        self.outer.pack(fill="both", expand=True)
        self.panel = CardPanel(self.outer, settings, self.key, self.title, self.columns,
                               log=self.write, on_change=self._sync_buttons,
                               default_folders=self.default_folders() or None,
                               filters_open=True, checkable=self.checkable)
        self.outer.add(self.panel, weight=1)
        logf = ttk.Frame(self.outer)
        self.log = tk.Text(logf, height=7, state="disabled")
        logsb = ttk.Scrollbar(logf, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=logsb.set)
        logsb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.outer.add(logf, weight=0)
        self.outer.bind("<ButtonRelease-1>", self._save_log_height)
        self._log_h_done = False

        # botón común de todas las pestañas + herramientas propias de la hija
        self.btn_delete = ttk.Button(self.panel.bar, text="Enviar a papelera",
                                     command=self.delete_selected, state="disabled")
        self.btn_delete.pack(side="left", before=self.panel.folders_lbl)
        self.tree.bind("<Delete>", self.delete_selected)
        self.build_toolbar(self.panel.extra_bar)

    # ---------- acceso cómodo al panel (lo usan las pestañas hijas) ----------
    @property
    def tree(self):
        return self.panel.tree

    @property
    def busy(self):
        return self.worker.busy or self.panel.busy

    def selection_paths(self):
        return self.panel.selected_paths()

    def run_in_background(self, fn):
        """fn(post) se ejecuta en un hilo; post(self.write, 'texto') para escribir en el registro."""
        self.worker.start(fn)

    # ---------- ganchos para las pestañas hijas ----------
    def build_toolbar(self, bar):
        pass

    def update_buttons(self):
        pass

    def default_folders(self):
        return []

    # ---------- botones y borrado ----------
    def _sync_buttons(self):
        ok = bool(self.tree.selection()) and not self.busy
        self.btn_delete.configure(state="normal" if ok else "disabled")
        self.update_buttons()

    def delete_selected(self, _event=None):
        """Envía las cards seleccionadas a la papelera de Windows (recuperables)."""
        sel = list(self.tree.selection())
        if not sel or self.busy:
            return
        try:
            from send2trash import send2trash
        except ImportError:
            messagebox.showerror(
                "Falta una librería",
                "Para usar la papelera hace falta «send2trash».\n"
                "Ejecuta instalar.bat otra vez (o: python -m pip install send2trash).")
            return
        names = [self.panel.paths[i].name for i in sel]
        lista = "\n".join(names[:8]) + (f"\n… y {len(names) - 8} más" if len(names) > 8 else "")
        if not messagebox.askyesno(
                "Enviar a la papelera",
                f"¿Enviar {len(sel)} card(s) a la papelera?\n\n{lista}\n\n"
                "Podrás recuperarlas desde la papelera de Windows.",
                icon="warning", default="no"):
            return
        first = self.tree.index(sel[0])
        ok = 0
        for iid in sel:
            path = self.panel.paths[iid]
            try:
                send2trash(str(path))
            except Exception as e:
                self.write(f"No se pudo enviar {path.name} a la papelera: {type(e).__name__}: {e}")
                continue
            self.panel.remove_row(iid)
            ok += 1
        if ok:
            self.write(f"{ok} card(s) enviada(s) a la papelera.")
        rest = self.tree.get_children()
        if rest:  # seleccionar la siguiente para poder seguir revisando sin tocar el ratón
            nxt = rest[min(first, len(rest) - 1)]
            self.tree.selection_set(nxt)
            self.tree.focus(nxt)
            self.tree.see(nxt)
        else:
            self.panel.preview.clear()
        self.panel._on_select()

    # ---------- registro y altura del registro ----------
    def write(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _save_log_height(self, _event=None):
        try:
            self.settings.set(f"tabs.{self.key}.layout.log_h",
                              self.outer.winfo_height() - self.outer.sashpos(0))
        except tk.TclError:
            pass

    def _try_restore_log_height(self):
        if self._log_h_done:
            return
        out_h = self.outer.winfo_height()
        if out_h < 250:
            return
        log_h = self.settings.get(f"tabs.{self.key}.layout.log_h")
        if isinstance(log_h, int) and 40 <= log_h <= out_h - 120:
            self.outer.sashpos(0, out_h - log_h)
        self._log_h_done = True

    # ---------- al entrar en la pestaña ----------
    def on_show(self):
        self.after(150, self._try_restore_log_height)
        self.panel.on_show()
