"""Panel reutilizable de cards: carpetas + lista (con casillas opcionales) + visor de portada.

Cada panel tiene su `key`: con ella recuerda en settings.json sus carpetas, el ancho de las
columnas y el ancho del visor (tabs.<key>.folders / col_widths / layout.preview_w).
Se usa en las pestañas normales (CardListTab) y dos veces en Donante → Receptores.
"""
import tkinter as tk
from tkinter import ttk

from ...batch.scan import find_cards_multi, read_card_summary
from ...core.listquery import Entry, SortOption, matches, natural_key, sort_entries, sort_options
from ...core.settings import ROOT_DIR
from ...readers.attributes import safe_defs
from ...readers.fileinfo import file_info, fmt_date
from .filter_bar import FilterBar
from .folders_dialog import FoldersDialog
from .preview import CardPreview
from .worker import Worker

MIN_COL_W = 30          # ancho mínimo de una columna al arrastrar su borde
CHECK_ON, CHECK_OFF = "☑", "☐"


def altura_txt(s):
    return f"{s['altura_slider']} / {s['altura_hueso']}"


# (clave, título, ancho, función(path, summary) -> texto)
BASE_COLUMNS = [
    ("archivo", "Archivo", 230, lambda p, s: p.name),
    ("nombre", "Nombre", 140, lambda p, s: s["nombre"]),
    ("tipo", "Tipo", 115, lambda p, s: s["tipo"]),
    ("altura", "Altura (slider / hueso)", 170, lambda p, s: altura_txt(s)),
    ("bulge", "Bulge", 55, lambda p, s: "—" if s["bulge"] is None else s["bulge"]),
    ("fecha", "Modificada", 120, lambda p, s: fmt_date(s["archivo_info"]["mtime"])),
]

# columna del tamaño efectivo del pene (Leer datos y Reparar pene): '1.02 (ok)'; vacía en female
PENE_COLUMN = ("pene", "Pene (efectivo)", 120,
               lambda p, s: "" if s["pene_estado"] is None else f"{s['pene_efectivo']:.2f} ({s['pene_estado']})")

# columna de la lista -> clave de orden (las demás ordenan por su texto: clave 'col:<columna>')
COLUMN_SORT = {"archivo": "archivo", "nombre": "nombre", "tipo": "attr:tipo", "altura": "attr:altura",
               "fecha": "modificada", "plugins": "plugins", "donante": "donante", "pene": "attr:pene"}


def attribute_columns(skip=("tipo",)):
    """Una columna por atributo de atributos.json (categoría y puntuación). Columna 'a_<clave>'."""
    def cell(key):
        def f(p, s):
            a = (s.get("attrs") or {}).get(key) or {}
            if a.get("cat") is None:
                return ""
            return a["cat"] if a.get("score") is None else f"{a['cat']} ({a['score']:+.2f})"
        return f
    return [(f"a_{d['clave']}", d["titulo"], 105, cell(d["clave"]))
            for d in safe_defs() if d["clave"] not in skip]


class CardPanel(ttk.Frame):
    def __init__(self, master, settings, key, title, columns, log, checkable=False,
                 selectmode="extended", on_change=None, default_folders=None, preview_size=(300, 420),
                 filters_open=False):
        """log(texto): dónde escribir avisos. on_change(): selección, casillas o carga cambiaron."""
        super().__init__(master)
        self.settings, self.key, self.title = settings, key, title
        self.columns, self.checkable = columns, checkable
        self._log, self.on_change = log, on_change
        self._default_folders = default_folders
        self.paths, self.summaries, self.checked = {}, {}, set()   # iid -> Path / resumen; iids marcados
        self.entries = {}      # iid -> Entry (todas las filas, también las ocultas por el filtro)
        self._seq = 0
        self.loaded = False
        self._layout_done = False
        self._resizing_col = False
        self.worker = Worker(self, on_state=lambda _b: self._changed(),
                             on_error=lambda e: self._log(f"ERROR: {type(e).__name__}: {e}"))

        # barra superior: carpetas / actualizar / estado. Las pestañas pueden añadir botones aquí.
        self.bar = ttk.Frame(self)
        self.bar.pack(fill="x", padx=8, pady=(8, 2))
        ttk.Button(self.bar, text="Carpetas…", command=self.edit_folders).pack(side="left")
        ttk.Button(self.bar, text="⟳ Actualizar", command=self.refresh).pack(side="left", padx=6)
        self.folders_lbl = ttk.Label(self.bar)
        self.folders_lbl.pack(side="left", padx=8)
        self.status_lbl = ttk.Label(self.bar)
        self.status_lbl.pack(side="right")
        # segunda barra: herramientas propias de cada pestaña (vacía = no ocupa sitio)
        self.extra_bar = ttk.Frame(self)
        self.extra_bar.pack(fill="x", padx=8, pady=2)

        # buscador / orden / filtros (los atributos salen de config/atributos.json)
        self._init_msgs = []        # avisos de arranque: el registro de la pestaña aún no existe
        self.defs = safe_defs(self._init_msgs.append)
        self.sort_opts = sort_options(self.defs)
        for k, t, *_ in columns:                      # las columnas sin orden propio ordenan por su texto
            if self._column_sort_key(k) == f"col:{k}":
                self.sort_opts.append(SortOption(f"col:{k}", f"Columna: {t}", self._column_value(k)))
        self.filterbar = FilterBar(self, settings, key, self.defs, self.sort_opts,
                                   on_change=self.apply_view, open_by_default=filters_open)
        self.filterbar.pack(fill="x", padx=8, pady=(2, 2))

        self.pw = ttk.Panedwindow(self, orient="horizontal")
        self.pw.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        left = ttk.Frame(self.pw)
        keys = ([("chk", "✓", 34)] if checkable else []) + [(k, t, w) for k, t, w, _ in columns]
        self.tree = ttk.Treeview(left, columns=[k for k, _, _ in keys], show="headings",
                                 selectmode=selectmode)
        saved = self.settings.get(f"tabs.{key}.col_widths", {})
        saved = saved if isinstance(saved, dict) else {}
        for k, t, width in keys:
            w = saved.get(k)
            if k == "chk" or not isinstance(w, int) or isinstance(w, bool) or w < MIN_COL_W:
                w = width
            self.tree.heading(k, text=t, command=(lambda k=k: self._header_click(k)) if k != "chk" else "")
            # stretch=False: el ancho lo decide el usuario, no se reparte solo al cambiar la ventana
            self.tree.column(k, width=w, minwidth=MIN_COL_W, stretch=False,
                             anchor="center" if k == "chk" else "w")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        sbx = ttk.Scrollbar(left, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb.set, xscrollcommand=sbx.set)
        sbx.pack(side="bottom", fill="x")
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.preview = CardPreview(self.pw, *preview_size)
        self.pw.add(left, weight=1)
        self.pw.add(self.preview, weight=0)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<ButtonPress-1>", self._press, add="+")
        self.tree.bind("<ButtonRelease-1>", self._release, add="+")
        if checkable:
            self.tree.bind("<space>", self._space)
        self.pw.bind("<ButtonRelease-1>", self._save_layout)
        self.tree.bind("<Control-f>", lambda _e: self.filterbar.focus_search())
        self._titles = {k: t for k, t, _w in keys}
        self._update_folders_label()
        self._update_headings()

    # ---------- estado ----------
    @property
    def busy(self):
        return self.worker.busy

    def write(self, msg):
        self._log(msg)

    def _changed(self):
        if self.on_change:
            self.on_change()

    def selected_paths(self):
        return [self.paths[i] for i in self.tree.selection()]

    def selected_path(self):
        """La card 'activa' (la del visor) o None."""
        sel = self.tree.selection()
        if not sel:
            return None
        iid = self.tree.focus() if self.tree.focus() in sel else sel[-1]
        return self.paths[iid]

    def summary_of(self, path):
        for iid, p in self.paths.items():
            if p == path:
                return self.summaries.get(iid)
        return None

    # ---------- casillas ----------
    def checked_paths(self):
        """Todas las marcadas: primero las visibles (en el orden mostrado), luego las que el filtro oculta."""
        shown = self.tree.get_children()
        seen = set(shown)
        return ([self.paths[i] for i in shown if i in self.checked]
                + [self.paths[i] for i in self.entries if i in self.checked and i not in seen])

    def hidden_checked_count(self):
        seen = set(self.tree.get_children())
        return sum(1 for i in self.checked if i not in seen)

    def _set_check(self, iid, on):
        (self.checked.add if on else self.checked.discard)(iid)
        self.tree.set(iid, "chk", CHECK_ON if on else CHECK_OFF)

    def check_all(self):
        for iid in self.tree.get_children():
            self._set_check(iid, True)
        self._changed()

    def check_none(self):
        for iid in list(self.checked):
            self._set_check(iid, False)
        self._changed()

    def check_selected(self):
        for iid in self.tree.selection():
            self._set_check(iid, True)
        self._changed()

    def _space(self, _event=None):
        sel = self.tree.selection()
        if sel:
            turn_on = not all(i in self.checked for i in sel)
            for iid in sel:
                self._set_check(iid, turn_on)
            self._changed()
        return "break"

    # ---------- ratón: arrastre de columnas y clic en casilla ----------
    def _press(self, event):
        self._resizing_col = self.tree.identify_region(event.x, event.y) == "separator"
        if self.checkable and self.tree.identify_region(event.x, event.y) == "cell" \
                and self.tree.identify_column(event.x) == "#1":
            iid = self.tree.identify_row(event.y)
            if iid:
                self._set_check(iid, iid not in self.checked)
                self._changed()

    def _release(self, _event):
        if self._resizing_col:
            self._resizing_col = False
            self.settings.set(f"tabs.{self.key}.col_widths",
                              {k: int(self.tree.column(k, "width")) for k, *_ in self.columns})

    # ---------- tamaño del visor ----------
    def _save_layout(self, _event=None):
        try:
            self.settings.set(f"tabs.{self.key}.layout.preview_w",
                              self.pw.winfo_width() - self.pw.sashpos(0))
        except tk.TclError:
            pass

    def try_restore_layout(self):
        """Aplica el ancho guardado del visor cuando la ventana ya tiene tamaño real."""
        if self._layout_done:
            return
        pw_w = self.pw.winfo_width()
        if pw_w < 300:
            return
        prev_w = self.settings.get(f"tabs.{self.key}.layout.preview_w")
        if isinstance(prev_w, int) and 100 <= prev_w <= pw_w - 150:
            self.pw.sashpos(0, pw_w - prev_w)
        self._layout_done = True

    # ---------- carpetas ----------
    def default_folders(self):
        if self._default_folders is not None:
            return self._default_folders
        d = ROOT_DIR / "cards_entrada"
        return [str(d)] if d.exists() else []

    @property
    def folders(self):
        return list(self.settings.get(f"tabs.{self.key}.folders", self.default_folders()))

    def _update_folders_label(self):
        f = self.folders
        self.folders_lbl.configure(
            text="Sin carpetas: pulsa «Carpetas…»" if not f
            else f[0] if len(f) == 1 else f"{len(f)} carpetas (primera: {f[0]})")

    def edit_folders(self):
        if self.busy:
            return
        dlg = FoldersDialog(self, self.folders, title=f"Carpetas — {self.title}")
        self.wait_window(dlg)
        if dlg.result is not None and dlg.result != self.folders:
            self.settings.set(f"tabs.{self.key}.folders", dlg.result)
            self._update_folders_label()
            self.refresh()

    # ---------- filas ----------
    def _clear(self):
        self.tree.delete(*self.entries)          # incluye las filas ocultas (desenganchadas)
        self.entries.clear()
        self.paths.clear()
        self.summaries.clear()
        self.checked.clear()
        self._seq = 0
        self.preview.clear()
        self.filterbar.set_counts(0, 0)

    def _add_row(self, path, s):
        if s is None:
            vals = [path.name, "", "ERROR al leer"] + [""] * (len(self.columns) - 3)
        else:
            vals = [c[3](path, s) for c in self.columns]
        if self.checkable:
            vals = [CHECK_OFF] + vals
        iid = self.tree.insert("", "end", values=vals)
        self.paths[iid] = path
        self.summaries[iid] = s
        self.entries[iid] = Entry(path, s, self._seq, (s or {}).get("archivo_info") or file_info(path), iid)
        self._seq += 1

    def remove_row(self, iid):
        self.tree.delete(iid)
        self.paths.pop(iid, None)
        self.summaries.pop(iid, None)
        self.entries.pop(iid, None)
        self.checked.discard(iid)
        self._update_counts()

    def _on_select(self, _event=None):
        path = self.selected_path()
        if path:
            s = self.summary_of(path)
            if s is None:
                cap = path.name
            else:
                head = f"{s['nombre']}  ({s['nickname']})\n" if s["nickname"] else f"{s['nombre']}\n"
                cap = head + f"{s['tipo']} · altura {altura_txt(s)}\n{path.name}"
                cats = [f"{d['titulo'].lower()}: {s['attrs'][d['clave']]['cat']}" for d in self.defs
                        if d["clave"] != "tipo" and (s.get("attrs", {}).get(d["clave"]) or {}).get("cat")]
                if cats:
                    cap += "\n" + " · ".join(cats)
                if s.get("donante"):
                    cap += f"\nCuerpo de: {s['donante']} ({s['modo_donacion']})"
            self.preview.show(path, cap)
        else:
            self.preview.clear()
        self._changed()

    # ---------- buscar / ordenar / filtrar ----------
    def _column_sort_key(self, col):
        if col.startswith("a_"):
            key = "attr:" + col[2:]
        else:
            key = COLUMN_SORT.get(col, f"col:{col}")
        return key if key in {o.key for o in self.sort_opts} or key.startswith("col:") else f"col:{col}"

    def _column_value(self, col):
        fn = next(c[3] for c in self.columns if c[0] == col)
        return lambda e: natural_key(fn(e.path, e.s)) if e.s else None

    def _header_click(self, col):
        """Clic en una cabecera: ordena por esa columna; otro clic invierte el sentido."""
        key = self._column_sort_key(col)
        cur, desc = self.filterbar.sort()
        self.filterbar.set_sort(key, (not desc) if cur.key == key else False)
        self.apply_view()

    def _update_headings(self):
        cur, desc = self.filterbar.sort()
        for k, title in self._titles.items():
            if k == "chk":
                continue
            mark = (" ▼" if desc else " ▲") if self._column_sort_key(k) == cur.key else ""
            self.tree.heading(k, text=title + mark)

    def _update_counts(self):
        self.filterbar.set_counts(len(self.tree.get_children()), len(self.entries))

    def apply_view(self):
        """Aplica búsqueda + filtros + orden: oculta (detach) las filas que no pasan y recoloca el resto.
        Las filas ocultas siguen existiendo: conservan sus casillas y vuelven al quitar el filtro."""
        state = self.filterbar.state()
        option, desc = self.filterbar.sort()
        entries = list(self.entries.values())
        shown = sort_entries([e for e in entries if matches(e, state)], option, desc)
        keep = {e.iid for e in shown}
        before = self.tree.selection()
        gone = [i for i in before if i not in keep]
        if gone:
            self.tree.selection_remove(*gone)
        for e in entries:
            if e.iid not in keep:
                self.tree.detach(e.iid)
        for pos, e in enumerate(shown):
            self.tree.move(e.iid, "", pos)
        self._update_counts()
        self._update_headings()
        if gone:
            self._on_select()
        else:
            self._changed()

    # ---------- carga ----------
    def on_show(self):
        """Se llama al entrar en la pestaña. Carga la primera vez; luego usa «Actualizar»."""
        self.after(150, self.try_restore_layout)
        while self._init_msgs:
            self._log(self._init_msgs.pop(0))
        if not self.loaded:
            self.refresh()

    def refresh(self):
        if self.busy:
            return
        self.loaded = True
        folders = self.folders
        self._update_folders_label()
        if not folders:
            self._clear()
            self._log(f"[{self.title}] Añade al menos una carpeta con «Carpetas…».")
            self._changed()
            return

        def work(post):
            post(self._clear)
            cards, missing = find_cards_multi(folders)
            for m in missing:
                post(self._log, f"Carpeta no encontrada (se ignora): {m}")
            n = len(cards)
            for i, p in enumerate(cards, 1):
                post(self.status_lbl.configure, text=f"Leyendo {i}/{n}…")
                try:
                    s = read_card_summary(p, self.defs)
                except Exception as e:
                    s = None
                    post(self._log, f"No se pudo leer {p.name}: {e}")
                post(self._add_row, p, s)
            post(self.status_lbl.configure, text="")
            post(self.apply_view)
            post(self._log, f"[{self.title}] Listo: {n} card(s).")

        self._log(f"[{self.title}] Leyendo: " + " | ".join(folders))
        self.worker.start(work)
