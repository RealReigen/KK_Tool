"""Pestaña 'Donante → Receptores': crea copias de las receptoras con el cuerpo del donante.

Izquierda: un donante (selección única). Derecha: receptoras con casillas.
Los originales no se tocan; las copias van a <salida>/<nombre del donante>/female|male/.
"""
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ...batch.donate import donate_cards, donation_folder
from ...core.settings import ROOT_DIR
from ...editors import cover_text
from ...editors.donor import load_config
from ..widgets.card_panel import CardPanel, altura_txt
from ..widgets.split_pane import SplitPane
from ..widgets.worker import Worker
from .futa_tab import CHECK_HINT

DONOR_COLUMNS = [
    ("archivo", "Archivo", 150, lambda p, s: p.name),
    ("nombre", "Nombre", 110, lambda p, s: s["nombre"]),
    ("tipo", "Tipo", 80, lambda p, s: s["tipo"]),
]
RECEPTOR_COLUMNS = [
    ("archivo", "Archivo", 170, lambda p, s: p.name),
    ("nombre", "Nombre", 110, lambda p, s: s["nombre"]),
    ("tipo", "Tipo", 80, lambda p, s: s["tipo"]),
    ("altura", "Altura (slider / hueso)", 150, lambda p, s: altura_txt(s)),
    ("donante", "Cuerpo de", 110, lambda p, s: s["donante"] or ""),
]


class DonorTab(ttk.Frame):
    key = "donar"
    title = "Donante → Receptores"

    def __init__(self, master, settings):
        super().__init__(master)
        self.settings = settings
        self.cfg = load_config()
        self.worker = Worker(self, on_state=lambda _b: self._sync(),
                             on_error=lambda e: self.write(f"ERROR: {type(e).__name__}: {e}"))

        # --- barra de herramientas ---
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=(8, 2))
        ttk.Label(bar, text="Modo:").pack(side="left")
        self.mode_var = ttk.Combobox(bar, state="readonly", width=11, values=list(self.cfg["modos"]))
        saved = settings.get(f"tabs.{self.key}.modo", "total")
        self.mode_var.set(saved if saved in self.cfg["modos"] else "total")
        self.mode_var.pack(side="left", padx=(4, 12))
        self.mode_var.bind("<<ComboboxSelected>>", self._mode_changed)
        ttk.Label(bar, text="BodyGUID:").pack(side="left")
        self.guid_var = ttk.Combobox(bar, state="readonly", width=8, values=["fijo", "donante"])
        saved = settings.get(f"tabs.{self.key}.body_guid", "fijo")
        self.guid_var.set(saved if saved in ("fijo", "donante") else "fijo")
        self.guid_var.pack(side="left", padx=(4, 12))
        self.guid_var.bind("<<ComboboxSelected>>",
                           lambda _e: settings.set(f"tabs.{self.key}.body_guid", self.guid_var.get()))
        self.futa_var = tk.BooleanVar(value=bool(settings.get(f"tabs.{self.key}.hacer_futa", False)))
        ttk.Checkbutton(bar, text="Convertir también a futa", variable=self.futa_var,
                        command=lambda: settings.set(f"tabs.{self.key}.hacer_futa", bool(self.futa_var.get()))
                        ).pack(side="left", padx=(0, 12))
        ttk.Button(bar, text="Carpeta de salida…", command=self.choose_out).pack(side="left")
        ttk.Button(bar, text="Abrir salida", command=self.open_out).pack(side="left", padx=6)
        self.out_lbl = ttk.Label(bar)
        self.out_lbl.pack(side="left", padx=8)

        bar2 = ttk.Frame(self)
        bar2.pack(fill="x", padx=8, pady=2)
        self.btn_create = ttk.Button(bar2, text="Crear cards con el cuerpo del donante",
                                     command=self.create, state="disabled")
        self.btn_create.pack(side="left")
        self.info_lbl = ttk.Label(bar2)
        self.info_lbl.pack(side="left", padx=10)
        self.desc_lbl = ttk.Label(self, foreground="#555", wraplength=1000, justify="left")
        self.desc_lbl.pack(fill="x", padx=10, pady=(0, 2))

        # --- centro: dos paneles arriba, registro abajo ---
        self.outer = SplitPane(self, orient="vertical")
        self.outer.pack(fill="both", expand=True, padx=0, pady=(2, 0))
        self.split = SplitPane(self.outer, orient="horizontal")
        self.donor = CardPanel(self.split, settings, "donar_donante", "Donante", DONOR_COLUMNS,
                               log=self.write, selectmode="browse", on_change=self._sync,
                               preview_size=(260, 360))
        self.receptors = CardPanel(self.split, settings, "donar_receptoras", "Receptoras",
                                   RECEPTOR_COLUMNS, log=self.write, checkable=True,
                                   on_change=self._sync, preview_size=(260, 360))
        self.split.add(self.donor, weight=1)
        self.split.add(self.receptors, weight=2)
        self.outer.add(self.split, weight=1)
        logf = ttk.Frame(self.outer)
        self.log = tk.Text(logf, height=7, state="disabled")
        sb = ttk.Scrollbar(logf, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.outer.add(logf, weight=0)

        ttk.Label(self.donor.extra_bar, text="Elige UNA card (su cuerpo se copiará).").pack(side="left")
        for text, cmd in (("Marcar todas", self.receptors.check_all), ("Ninguna", self.receptors.check_none),
                          ("Marcar las seleccionadas", self.receptors.check_selected)):
            ttk.Button(self.receptors.extra_bar, text=text, command=cmd).pack(side="left", padx=(0, 6))
        ttk.Label(self.receptors.extra_bar, text=CHECK_HINT.strip()).pack(side="left")

        self.split.bind("<ButtonRelease-1>", self._save_split)
        self.outer.bind("<ButtonRelease-1>", self._save_log_h)
        self._layout_done = False
        self._update_out_label()
        self._mode_changed()

    # ---------- ajustes ----------
    @property
    def out_dir(self):
        return Path(self.settings.get(f"tabs.{self.key}.out_dir", str(ROOT_DIR / "salida_donaciones")))

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

    def _mode_changed(self, _e=None):
        mode = self.mode_var.get()
        self.settings.set(f"tabs.{self.key}.modo", mode)
        self.desc_lbl.configure(text=self.cfg["modos"][mode]["descripcion"])

    # ---------- registro ----------
    def write(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ---------- estado de botones ----------
    @property
    def busy(self):
        return self.worker.busy or self.donor.busy or self.receptors.busy

    def _sync(self):
        donor = self.donor.selected_path()
        n = len(self.receptors.checked_paths())
        hid = self.receptors.hidden_checked_count()
        self.info_lbl.configure(text=f"Donante: {'—' if not donor else donor.name}   ·   "
                                     f"Receptoras marcadas: {n}"
                                     + (f" ({hid} ocultas por el filtro, también se incluyen)" if hid else ""))
        self.btn_create.configure(state="normal" if donor and n and not self.busy else "disabled")

    # ---------- crear ----------
    def create(self):
        donor = self.donor.selected_path()
        recs = self.receptors.checked_paths()
        if not donor or not recs or self.busy:
            return
        mode, guid, futa = self.mode_var.get(), self.guid_var.get(), bool(self.futa_var.get())
        if self.cfg["portada"]["activa"] and not cover_text.pillow_available():
            messagebox.showerror("Falta una librería",
                                 "Para dibujar la franja en la portada hace falta «Pillow».\n"
                                 "Ejecuta instalar.bat otra vez (o: python -m pip install pillow).\n"
                                 "No se ha creado nada.")
            return
        ds = self.donor.summary_of(donor)
        if ds is None or ds["tipo"] == "male":
            messagebox.showerror("Donante no válido",
                                 "El donante no se puede leer o es una card male nativa (no admitida).")
            return
        omit = []
        for p in recs:
            s = self.receptors.summary_of(p)
            if p.resolve() == donor.resolve():
                omit.append(f"{p.name} (es el propio donante)")
            elif s is None or s["tipo"] == "male":
                omit.append(f"{p.name} (male nativa o ilegible)")
        n_ok = len(recs) - len(omit)
        if n_ok == 0:
            messagebox.showinfo("Nada que crear", "Todas las receptoras marcadas se omitirían:\n\n" + "\n".join(omit))
            return
        folder = donation_folder(donor, self.out_dir)
        extra = f"\n\nSe omitirán {len(omit)}:\n" + "\n".join(omit[:8]) if omit else ""
        if not messagebox.askyesno(
                "Crear donaciones",
                f"Se crearán {n_ok} card(s) nueva(s).\n\nDonante: {ds['nombre']}\nModo: {mode}\n"
                f"BodyGUID: {guid}\nConvertir a futa: {'SÍ (quedan en male)' if futa else 'no'}\n"
                f"Carpeta: {folder}\\female | male{extra}\n\n"
                "Los originales no se tocan. ¿Continuar?"):
            return
        out = self.out_dir
        self.write(f"--- Donación: {donor.name} -> {n_ok} receptora(s), modo {mode}"
                   f"{', + futa' if futa else ''} ---")
        self.worker.start(lambda post: donate_cards(
            donor, recs, mode, out, guid, log=lambda m: post(self.write, m), make_futa=futa))

    # ---------- tamaños ----------
    def _save_split(self, _e=None):
        try:
            self.settings.set(f"tabs.{self.key}.layout.split", self.split.sashpos(0))
        except Exception:
            pass

    def _save_log_h(self, _e=None):
        try:
            self.settings.set(f"tabs.{self.key}.layout.log_h",
                              self.outer.winfo_height() - self.outer.sashpos(0))
        except Exception:
            pass

    def _restore_layout(self):
        if self._layout_done:
            return
        w, h = self.split.winfo_width(), self.outer.winfo_height()
        if w < 400 or h < 250:
            return
        split = self.settings.get(f"tabs.{self.key}.layout.split")
        if isinstance(split, int) and 150 <= split <= w - 200:
            self.split.sashpos(0, split)
        log_h = self.settings.get(f"tabs.{self.key}.layout.log_h")
        if isinstance(log_h, int) and 40 <= log_h <= h - 120:
            self.outer.sashpos(0, h - log_h)
        self._layout_done = True

    def on_show(self):
        self.after(150, self._restore_layout)
        self.donor.on_show()
        self.receptors.on_show()
