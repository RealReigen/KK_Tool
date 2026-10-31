"""Barra de búsqueda / orden / filtros de una lista de cards. Solo interfaz: la lógica está en
core/listquery.py y los atributos en config/atributos.json (un grupo de casillas por atributo).

Uso: FilterBar(master, settings, key, defs, sort_options, on_change); en on_change() el dueño
lee .state() y .sort(). Recuerda en settings.json: tabs.<key>.sort y tabs.<key>.filters_open.
"""
import tkinter as tk
from tkinter import ttk

from ...core.listquery import FilterState
from ...readers.attributes import categories

DEBOUNCE_MS = 200


class FilterBar(ttk.Frame):
    def __init__(self, master, settings, key, defs, sort_options, on_change, open_by_default=False):
        super().__init__(master)
        self.settings, self.key, self.defs = settings, key, defs
        self.options = {o.key: o for o in sort_options}
        self.on_change = on_change
        self._after = None

        # --- fila 1: buscador + contador ---
        row1 = ttk.Frame(self)
        row1.pack(fill="x")
        ttk.Label(row1, text="Buscar:").pack(side="left")
        self.text_var = tk.StringVar()
        self.entry = ttk.Entry(row1, textvariable=self.text_var, width=24)
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 2))
        ttk.Button(row1, text="✕", width=2, command=self.clear_text).pack(side="left")
        self.count_lbl = ttk.Label(row1, foreground="#555")
        self.count_lbl.pack(side="right", padx=(8, 0))
        self.text_var.trace_add("write", self._text_changed)
        self.entry.bind("<Escape>", lambda _e: self.clear_text())

        # --- fila 2: orden + filtros ---
        row2 = ttk.Frame(self)
        row2.pack(fill="x", pady=(3, 0))
        ttk.Label(row2, text="Ordenar:").pack(side="left")
        self.labels = {o.label: o.key for o in sort_options}
        self.sort_cb = ttk.Combobox(row2, state="readonly", width=28, values=list(self.labels))
        self.sort_cb.pack(side="left", padx=4)
        self.sort_cb.bind("<<ComboboxSelected>>", lambda _e: self._sort_changed())
        self.desc = False
        self.dir_btn = ttk.Button(row2, width=3, command=self.toggle_dir)
        self.dir_btn.pack(side="left")
        self.open = bool(settings.get(f"tabs.{key}.filters_open", open_by_default)) and bool(defs)
        self.toggle_btn = ttk.Button(row2, command=self.toggle_open)
        if defs:
            self.toggle_btn.pack(side="left", padx=(10, 4))
        ttk.Button(row2, text="Limpiar", command=self.clear).pack(side="left")

        # --- grupos de filtros (uno por atributo) ---
        self.groups_frame = ttk.Frame(self)
        self.vars = {}      # clave de atributo -> {categoría: BooleanVar}
        for d in defs:
            line = ttk.Frame(self.groups_frame)
            line.pack(fill="x", pady=1)
            ttk.Label(line, text=f"{d['titulo']}:", width=8, font=("TkDefaultFont", 9, "bold")).pack(side="left")
            self.vars[d["clave"]] = {}
            for cat in categories(d):
                v = tk.BooleanVar(value=False)
                ttk.Checkbutton(line, text=cat, variable=v, command=self._filter_changed).pack(side="left", padx=(0, 8))
                self.vars[d["clave"]][cat] = v

        self._load_sort()
        self._refresh_texts()
        if self.open:
            self.groups_frame.pack(fill="x", pady=(3, 0))

    # ---------- estado que lee el panel ----------
    def state(self):
        return FilterState(self.text_var.get(), {k: {c for c, v in cs.items() if v.get()}
                                                  for k, cs in self.vars.items()})

    def sort(self):
        return self.options[self.sort_key], self.desc

    def set_sort(self, key, desc):
        if key in self.options:
            self.sort_key, self.desc = key, desc
            self._refresh_texts()
            self._save_sort()

    def set_counts(self, shown, total):
        self.count_lbl.configure(text=f"{total} cards" if shown == total else f"{shown} de {total}")

    def focus_search(self):
        self.entry.focus_set()
        self.entry.selection_range(0, "end")

    # ---------- acciones ----------
    def clear_text(self):
        self.text_var.set("")

    def clear(self):
        """Quita el texto y todas las casillas (el orden se conserva)."""
        for cs in self.vars.values():
            for v in cs.values():
                v.set(False)
        self.text_var.set("")
        self._fire()
        self._refresh_texts()

    def toggle_dir(self):
        self.set_sort(self.sort_key, not self.desc)
        self._fire()

    def toggle_open(self):
        self.open = not self.open
        if self.open:
            self.groups_frame.pack(fill="x", pady=(3, 0))
        else:
            self.groups_frame.pack_forget()
        self.settings.set(f"tabs.{self.key}.filters_open", self.open)
        self._refresh_texts()

    # ---------- internos ----------
    def _load_sort(self):
        saved = self.settings.get(f"tabs.{self.key}.sort")
        key, desc = "orden", False
        if isinstance(saved, dict) and saved.get("key") in self.options:
            key, desc = saved["key"], bool(saved.get("desc"))
        self.sort_key, self.desc = key, desc

    def _save_sort(self):
        self.settings.set(f"tabs.{self.key}.sort", {"key": self.sort_key, "desc": self.desc})

    def _refresh_texts(self):
        self.sort_cb.set(self.options[self.sort_key].label)
        self.dir_btn.configure(text="▼" if self.desc else "▲")
        n = len(self.state().active_groups())
        self.toggle_btn.configure(text=f"Filtros{f' ({n})' if n else ''} {'▾' if self.open else '▸'}")

    def _sort_changed(self):
        self.sort_key = self.labels[self.sort_cb.get()]
        self._save_sort()
        self._fire()

    def _filter_changed(self):
        self._refresh_texts()
        self._fire()

    def _text_changed(self, *_):
        if self._after:
            self.after_cancel(self._after)
        self._after = self.after(DEBOUNCE_MS, self._fire)

    def _fire(self):
        if self._after:
            self.after_cancel(self._after)
        self._after = None
        if self.on_change:
            self.on_change()
