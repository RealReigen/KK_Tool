"""Visor de portada de card. Reutilizable: se puede colocar en cualquier pestaña/distribución."""
import base64
import math
import tkinter as tk
from tkinter import ttk

from ...core.cover import read_cover_png


class CardPreview(ttk.Frame):
    def __init__(self, master, max_w=300, max_h=420):
        super().__init__(master, padding=6)
        self.MAX_W, self.MAX_H = max_w, max_h
        self._img = None  # referencia obligatoria: si no, Tk borra la imagen
        self.image_lbl = ttk.Label(self, anchor="center")
        self.image_lbl.pack(fill="x")
        self.caption = ttk.Label(self, justify="left", anchor="nw", wraplength=self.MAX_W)
        self.caption.pack(fill="x", pady=(8, 0))
        self.clear()

    def clear(self):
        self._set_image(None)
        self.caption.configure(text="Selecciona una card para verla aquí.")

    def show(self, path, caption=""):
        try:
            img = tk.PhotoImage(data=base64.b64encode(read_cover_png(path)))
            f = max(math.ceil(img.width() / self.MAX_W), math.ceil(img.height() / self.MAX_H), 1)
            if f > 1:
                img = img.subsample(f)
            self._set_image(img)
            text = caption
        except Exception as e:
            self._set_image(None)
            text = f"(no se pudo mostrar la portada: {e})\n{caption}"
        self.caption.configure(text=text)

    def _set_image(self, img):
        self._img = img
        self.image_lbl.configure(image=img if img else "")
