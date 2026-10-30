"""Diálogo para gestionar la lista de carpetas de una pestaña."""
import os
import tkinter as tk
from tkinter import filedialog, ttk


class FoldersDialog(tk.Toplevel):
    def __init__(self, master, folders, title="Carpetas de esta pestaña"):
        super().__init__(master)
        self.title(title)
        self.result = None  # None = cancelado
        self.transient(master.winfo_toplevel())
        self.geometry("640x320")

        self.lb = tk.Listbox(self, selectmode="extended")
        for f in folders:
            self.lb.insert("end", f)
        self.lb.pack(fill="both", expand=True, padx=8, pady=8)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bar, text="Añadir carpeta…", command=self._add).pack(side="left")
        ttk.Button(bar, text="Quitar seleccionadas", command=self._remove).pack(side="left", padx=6)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(bar, text="Aceptar", command=self._accept).pack(side="right", padx=6)

        self.wait_visibility()
        self.grab_set()

    def _add(self):
        folder = filedialog.askdirectory(parent=self, title="Añadir carpeta")
        if not folder:
            return
        folder = os.path.normpath(folder)
        if folder not in self.lb.get(0, "end"):
            self.lb.insert("end", folder)

    def _remove(self):
        for i in reversed(self.lb.curselection()):
            self.lb.delete(i)

    def _accept(self):
        self.result = list(self.lb.get(0, "end"))
        self.destroy()
