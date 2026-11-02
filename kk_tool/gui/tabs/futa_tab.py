"""Pestaña 'Female → Futa': convierte las cards MARCADAS (casillas ☐/☑).

Las casillas son independientes de la selección: hacer clic en una fila para ver su portada no
desmarca las que ya tenías marcadas.

Instalación de Koikatsu: con «Instalación de Koikatsu…» basta señalar la carpeta del juego; la entrada pasa a
ser UserData/chara/female y la salida UserData/chara/male (se pueden seguir cambiando con «Carpetas…» y
«Carpeta de salida…»).

Duplicados: al entrar en la pestaña se indexa la carpeta de salida por contenido (batch/futa_index.py).
TODAS las filas cuya futa ya está en la salida se pintan de amarillo pastel y la columna «Futa en la salida» lo
dice con texto (no hay que marcarlas ni recordar nada: se calcula del contenido de las cards que hay en disco).
Una fila MARCADA cuya futa aún no existe se pinta de azul pastel.
Al convertir, las que ya estaban van a <salida>/duplicados/ en vez de repetirse.
Además de la salida se comparan carpetas extra: KK_Tool/salida/male (donde iban las futas antes de la v0.6.0),
si existe, y las que añadas con «Comparar con…».
"""
import os
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ...batch.convert import ERR_SUBDIR, convert_cards
from ...batch.futa_index import DUP_SUBDIR, FutaIndex
from ...core.game_paths import resolve_install
from ...core.settings import ROOT_DIR
from .base import BASE_COLUMNS, CardListTab
from .out_mixin import OutDirMixin

CHECK_HINT = "   (☐ clic · Enter o espacio sobre las seleccionadas · Mayús+clic marca un rango)"
TAG_NEW, TAG_DONE = "futa_nueva", "futa_existe"
COLOR_NEW, COLOR_DONE = "#D4E6F9", "#FFF0B3"      # azul pastel / amarillo pastel
REPORT_DIR = ROOT_DIR / "salida"                  # registro (log.txt) y errores/ de las conversiones
LEGACY_OUT = REPORT_DIR / "male"                  # salida de las versiones anteriores a la 0.6.0


class FutaTab(OutDirMixin, CardListTab):
    key = "futa"
    title = "Female → Futa"
    checkable = True
    with_fingerprint = True
    out_setting = "out_male"        # aquí «salida» es la propia carpeta male/ (no una carpeta que la contiene)
    columns = BASE_COLUMNS + [("futa", "Futa en la salida", 200, lambda p, s: s.get("futa_txt", ""))]

    # ---------- carpetas por defecto (instalación de Koikatsu) ----------
    def _game(self):
        return resolve_install(self.settings.get("game.install_dir"))

    def default_folders(self):
        g = self._game()
        return [str(g.female)] if g else []

    def default_out(self):
        g = self._game()
        return g.male if g else REPORT_DIR / "male"

    def _update_out_label(self):
        chosen = self.settings.get(f"tabs.{self.key}.{self.out_setting}") is not None
        warn = "" if (chosen or self._game()) else \
            "    ⚠ no has elegido la instalación de Koikatsu: se usa la carpeta de KK_Tool (pulsa «Instalación de Koikatsu…»)"
        self.out_lbl.configure(text=f"Salida: {self.out_dir}{warn}", foreground="#B00020" if warn else "")

    # ---------- barra de herramientas ----------
    def build_toolbar(self, bar):
        self.index = FutaIndex()
        self.index_ready = False
        self.btn_conv = ttk.Button(bar, text="Convertir marcadas a futa",
                                   command=self.convert_selected, state="disabled")
        self.btn_conv.pack(side="left")
        for text, cmd in (("Marcar todas", self.panel.check_all), ("Ninguna", self.panel.check_none),
                          ("Marcar las seleccionadas", self.panel.check_selected)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Instalación de Koikatsu…", command=self.choose_install).pack(side="left", padx=(12, 0))
        ttk.Button(bar, text="Carpeta de salida…", command=self.choose_out).pack(side="left", padx=(6, 6))
        ttk.Button(bar, text="Abrir salida", command=self.open_out).pack(side="left")
        ttk.Button(bar, text="Comparar con…", command=self.add_compare_folder).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Marcar las que faltan", command=self.check_missing).pack(side="left", padx=(12, 0))
        bar2 = ttk.Frame(bar.master)
        bar2.pack(fill="x", padx=8, pady=(0, 0), after=bar)
        self.info_lbl = ttk.Label(bar2)
        self.info_lbl.pack(side="left")
        ttk.Label(bar2, text=CHECK_HINT, foreground="#555").pack(side="left")
        bar3 = ttk.Frame(bar.master)       # la ruta de salida es larga: va en su propia línea
        bar3.pack(fill="x", padx=8, pady=(0, 2), after=bar2)
        self.out_lbl = ttk.Label(bar3)
        self.out_lbl.pack(side="left")
        self.idx_lbl = ttk.Label(bar3, foreground="#555")
        self.idx_lbl.pack(side="right")
        self._update_out_label()

        # colores de las filas marcadas + avisos del visor + índice al terminar de leer la lista
        self.tree.tag_configure(TAG_NEW, background=COLOR_NEW)
        self.tree.tag_configure(TAG_DONE, background=COLOR_DONE)
        self.panel.check_tag = self._check_tag
        self.panel.caption_extra = self._caption_extra
        self.panel.on_loaded = self.start_index

    # ---------- instalación de Koikatsu ----------
    def _busy_msg(self):
        """True (y avisa en el registro) si hay una lectura o indexado en marcha: antes los botones no decían nada."""
        if not self.busy:
            return False
        self.write("Espera: la app sigue leyendo las cards o indexando la salida (mira «Leyendo…» arriba a la derecha "
                   "o «Indexando…» abajo). Cuando termine, vuelve a pulsar.")
        return True

    def choose_install(self):
        if self._busy_msg():
            return
        self.write("Elige la carpeta de la instalación de Koikatsu en la ventana que se abre "
                   "(si no la ves, mira detrás de esta ventana)…")
        cur = self._game()
        d = filedialog.askdirectory(parent=self.winfo_toplevel(), title="Carpeta de la instalación de Koikatsu",
                                    initialdir=str(cur.install) if cur else "")
        if not d:
            self.write("Instalación: no se eligió ninguna carpeta.")
            return
        g = resolve_install(d)
        if g is None:
            messagebox.showerror(
                "Instalación de Koikatsu",
                f"No encuentro UserData\\chara\\female dentro de:\n{d}\n\n"
                "Elige la carpeta donde está instalado el juego (la que contiene UserData).")
            return
        self.settings.set("game.install_dir", os.path.normpath(str(g.install)))
        self.settings.set(f"tabs.{self.key}.folders", [os.path.normpath(str(g.female))])
        self.settings.set(f"tabs.{self.key}.{self.out_setting}", os.path.normpath(str(g.male)))
        self._update_out_label()
        self.write(f"Instalación: {g.install}\n    entrada: {g.female}\n    salida:  {g.male}"
                   + ("" if g.male.is_dir() else "   (aún no existe: se creará al guardar la primera card)"))
        self.panel.refresh()        # al terminar de leer la lista se reindexa la salida

    def choose_out(self):
        old = self.out_dir
        super().choose_out()
        if self.out_dir != old:
            self.start_index()

    # ---------- carpetas con las que también se compara ----------
    def compare_folders(self):
        saved = self.settings.get(f"tabs.{self.key}.compare_folders", [])
        extra = [Path(x) for x in saved] if isinstance(saved, list) else []
        if LEGACY_OUT.is_dir():
            extra.append(LEGACY_OUT)
        return extra

    def add_compare_folder(self):
        if self._busy_msg():
            return
        d = filedialog.askdirectory(parent=self.winfo_toplevel(), title="Carpeta con futas ya hechas (para no repetirlas)")
        if not d:
            return
        saved = self.settings.get(f"tabs.{self.key}.compare_folders", [])
        saved = list(saved) if isinstance(saved, list) else []
        d = os.path.normpath(d)
        if d not in saved:
            saved.append(d)
            self.settings.set(f"tabs.{self.key}.compare_folders", saved)
        self.start_index()

    def check_missing(self):
        """Marca las filas visibles cuya futa aún no existe (las que sí conviene convertir)."""
        if not self.index_ready:
            self.write("Espera a que termine de indexarse la salida.")
            return
        for iid in self.tree.get_children():
            if not (self.panel.summaries.get(iid) or {}).get("huella"):
                continue                       # sin huella: no se sabe, no se marca
            if not self._existing(iid):
                self.panel._set_check(iid, True)
        self.panel._changed()

    # ---------- índice de la carpeta de salida ----------
    def start_index(self):
        """(Re)indexa la carpeta de salida por contenido, en segundo plano. Convertir espera a que acabe."""
        if self.worker.busy:
            return
        self.index_ready = False
        out = self.out_dir
        self.idx_lbl.configure(text="Indexando la salida…")
        extra = self.compare_folders()
        self.refresh_marks()

        def work(post):
            self.index.scan(out, extra=extra, log=lambda m: post(self.write, m),
                            progress=lambda i, n: post(self.idx_lbl.configure,
                                                       text=f"Indexando {out.name}/ {i}/{n}…"))
            post(self._index_done)

        self.run_in_background(work)

    def _index_done(self):
        self.index_ready = True
        n, bad = len(self.index), self.index.unreadable
        self.idx_lbl.configure(text=f"{self.index.folder.name}/: {n} card(s) indexadas"
                               + (f" ({bad} ilegibles)" if bad else ""))
        nofp = [(i, s) for i, s in self.panel.summaries.items() if s is not None and not s.get("huella")]
        if nofp:
            self.write(f"AVISO: no se pudo calcular la huella de {len(nofp)} card(s) de la lista (no se pueden "
                       f"comparar). Primer error: {nofp[0][1].get('huella_error', '?')}")
        self.refresh_marks()
        self._sync_buttons()

    # ---------- colores y avisos ----------
    def _existing(self, iid):
        """Ruta de la futa ya hecha en la salida para esta fila, o None (también si aún no se sabe)."""
        if not self.index_ready:
            return None
        fp = (self.panel.summaries.get(iid) or {}).get("huella")
        return self.index.find_main(fp) if fp else None

    def _check_tag(self, iid, checked):
        """Amarillo: su futa ya existe (siempre). Azul: marcada y aún sin futa. Sin color: el resto."""
        if not self.index_ready or not (self.panel.summaries.get(iid) or {}).get("huella"):
            return None
        if self._existing(iid):
            return TAG_DONE
        return TAG_NEW if checked else None

    def _futa_text(self, s):
        if s is None:
            return ""
        if not self.index_ready:
            return "(indexando…)"
        fp = s.get("huella")
        if not fp:
            return "(sin huella)"
        found = self.index.find_main(fp)
        return f"SÍ · {self.index.shown(found)}" if found else "no"

    def refresh_marks(self):
        """Recalcula la columna «Futa en la salida» y el color de TODAS las filas."""
        for iid, s in self.panel.summaries.items():
            txt = self._futa_text(s)
            if s is not None:
                s["futa_txt"] = txt
            if "futa" in self.tree["columns"]:
                self.tree.set(iid, "futa", txt)
        self.panel.repaint()

    def _caption_extra(self, path):
        iid = next((i for i, p in self.panel.paths.items() if p == path), None)
        found = self._existing(iid) if iid else None
        return f"Ya hay una futa igual en {self.index.shown(found)}" if found else ""

    # ---------- botones ----------
    def update_buttons(self):
        n = len(self.panel.checked_paths())
        hid = self.panel.hidden_checked_count()
        dup = sum(1 for i in self.panel.checked if self._existing(i))
        done = sum(1 for i in self.panel.paths if self._existing(i)) if self.index_ready else 0
        self.info_lbl.configure(
            text=(f"{done} de {len(self.panel.paths)} ya tienen futa (amarillo)   ·   " if self.index_ready else "")
            + f"Marcadas: {n}"
            + (f" ({dup} ya tienen su futa en la salida)" if dup else "")
            + (f" ({hid} ocultas por el filtro, también se incluyen)" if hid else ""))
        ready = self.index_ready and not self.busy
        self.btn_conv.configure(state="normal" if n and ready else "disabled")

    def convert_selected(self):
        sel = self.panel.checked_paths()
        if not sel or self.busy or not self.index_ready:
            return
        dup = sum(1 for i in self.panel.checked if self._existing(i))
        out = self.out_dir
        msg = (f"¿Convertir {len(sel)} card(s) marcada(s) a futa?\nLos originales no se tocan; "
               f"las nuevas irán a:\n{out} (con las mismas subcarpetas que la entrada)\n")
        if dup:
            msg += (f"\n{dup} de ellas ya tienen su futa en esa carpeta: se guardarán en\n"
                    f"{out / DUP_SUBDIR}\n")
        msg += f"\nLas que fallen se copiarán a:\n{REPORT_DIR / ERR_SUBDIR}"
        if not messagebox.askyesno("Convertir", msg):
            return
        roots, index = self.panel.folders, self.index

        def work(post):
            convert_cards(sel, out, REPORT_DIR, log=lambda m: post(self.write, m), roots=roots, index=index)
            post(self._after_convert)

        self.run_in_background(work)

    def _after_convert(self):
        self.idx_lbl.configure(text=f"{self.index.folder.name}/: {len(self.index)} card(s) indexadas")
        self.refresh_marks()
        self._sync_buttons()
