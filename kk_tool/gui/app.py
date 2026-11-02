"""Ventana principal: solo monta las pestañas y recuerda tamaño/pestaña."""
import tkinter as tk
from tkinter import ttk

from ..core.settings import Settings
from .tabs import TABS
from .widgets.key_router import KeyRouter


def _fix_treeview_tag_colors():
    """Tk 8.6.9 (el de Python 3.10 en Windows) ignora el color de fondo de las filas con tag en un Treeview.
    Arreglo habitual: quitar del estilo la entrada que lo anula. En otras versiones no hace nada."""
    style = ttk.Style()

    def fixed(option):
        return [e for e in style.map("Treeview", query_opt=option) if e[:2] != ("!disabled", "!selected")]

    style.map("Treeview", foreground=fixed("foreground"), background=fixed("background"))


class App(tk.Tk):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.title("KK Tool")
        self.geometry(settings.get("window.size", "1150x680"))
        KeyRouter(self)     # antes de crear las pestañas: cada lista se registra al crearse
        _fix_treeview_tag_colors()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.tabs = []
        for cls in TABS:
            tab = cls(self.nb, settings)
            self.nb.add(tab, text=cls.title)
            self.tabs.append(tab)
        idx = settings.get("window.tab", 0)
        if isinstance(idx, int) and 0 <= idx < len(self.tabs):
            self.nb.select(idx)
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab)
        self.after(50, self._on_tab)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _on_tab(self, _event=None):
        self.nametowidget(self.nb.select()).on_show()

    def _close(self):
        self.settings.set("window.size", f"{self.winfo_width()}x{self.winfo_height()}")
        self.settings.set("window.tab", self.nb.index(self.nb.select()))
        self.destroy()


def run():
    App(Settings()).mainloop()
