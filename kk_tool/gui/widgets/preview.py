"""Visor de portada de card. Reutilizable: se puede colocar en cualquier pestaña/distribución.

La imagen se ajusta SIEMPRE al hueco disponible (se reescala cada vez que cambia el tamaño del
visor, sin cortarse ni pedir ajuste manual). Con Pillow se reescala suave (hasta ×2); sin Pillow
queda el reescalado entero de Tk.
"""
import base64
import io
import math
import tkinter as tk
from tkinter import ttk

from ...core.cover import read_cover_png

MAX_ZOOM = 2.0      # cuánto se amplía como máximo si sobra sitio
MIN_SIDE = 20       # por debajo de este tamaño de hueco no se dibuja


class CardPreview(ttk.Frame):
    def __init__(self, master, max_w=300, max_h=420):
        # tamaño inicial pedido fijo: lo que se ve lo decide el divisor, no el contenido
        super().__init__(master, padding=6, width=max_w + 12, height=max_h + 60)
        self.pack_propagate(False)
        self._src = None            # imagen original (PIL) o bytes PNG si no hay Pillow
        self._img = None            # referencia obligatoria: si no, Tk borra la imagen
        self._last = None           # (ancho, alto, id de imagen) de lo último dibujado
        self._after = None
        self._gen = 0               # cambia con cada imagen nueva (para saber si hay que redibujar)
        bg = ttk.Style().lookup("TFrame", "background") or self.winfo_toplevel().cget("bg")
        # el pie se empaqueta primero para que siempre quepa; la imagen usa lo que sobra
        self.caption = ttk.Label(self, justify="left", anchor="nw", wraplength=max_w)
        self.caption.pack(side="bottom", fill="x", pady=(8, 0))
        self.canvas = tk.Canvas(self, width=1, height=1, bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._schedule)
        self.bind("<Configure>", lambda e: self.caption.configure(wraplength=max(60, e.width - 16)))
        self.clear()

    def clear(self):
        self._src = None
        self._gen += 1
        self._set_caption("Selecciona una card para verla aquí.")
        self._render()

    def show(self, path, caption=""):
        self._gen += 1
        try:
            data = read_cover_png(path)
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(data))
                img.load()
                self._src = img if img.mode in ("RGB", "RGBA") else img.convert("RGBA")
            except ImportError:
                self._src = data
            text = caption
        except Exception as e:
            self._src = None
            text = f"(no se pudo mostrar la portada: {e})\n{caption}"
        self._set_caption(text)
        self._render()

    # ---------- dibujo ----------
    def _set_caption(self, text):
        self.caption.configure(text=text)

    def _schedule(self, _event=None):
        if self._after is None:
            self._after = self.after(30, self._render)

    def _photo(self, cw, ch):
        """PhotoImage de la portada ajustada a cw x ch (o None)."""
        src = self._src
        if src is None:
            return None
        if isinstance(src, bytes):                       # sin Pillow: reducción entera de Tk
            img = tk.PhotoImage(data=base64.b64encode(src))
            f = max(math.ceil(img.width() / cw), math.ceil(img.height() / ch), 1)
            return img.subsample(f) if f > 1 else img
        from PIL import Image
        w, h = src.size
        scale = min(cw / w, ch / h, MAX_ZOOM)
        size = (max(1, int(w * scale)), max(1, int(h * scale)))
        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = io.BytesIO()
        (src if size == src.size else src.resize(size, resample)).save(out, "PNG")
        return tk.PhotoImage(data=base64.b64encode(out.getvalue()))

    def _render(self):
        self._after = None
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        key = (cw, ch, self._gen)
        if key == self._last:
            return
        self._last = key
        self.canvas.delete("all")
        self._img = None
        if self._src is None or cw < MIN_SIDE or ch < MIN_SIDE:
            return
        try:
            self._img = self._photo(cw, ch)
        except Exception as e:
            self._set_caption(f"(no se pudo mostrar la portada: {e})")
            return
        if self._img:
            self.canvas.create_image(cw // 2, 0, image=self._img, anchor="n")
