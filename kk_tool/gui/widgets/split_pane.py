"""Divisor redimensionable con agarre VISIBLE (franja gris ancha y cursor de doble flecha).

Sustituye a ttk.Panedwindow, cuyo divisor en Windows es casi invisible. Mantiene su misma interfaz:
  add(hijo, weight=1)   weight > 0: absorbe el cambio de tamaño de la ventana; 0: conserva su tamaño
  sashpos(i[, pos])     posición del divisor i (x si es horizontal, y si es vertical)
Para cambiar el aspecto del divisor: SASH_WIDTH / SASH_COLOR.
"""
import tkinter as tk

SASH_WIDTH = 9
SASH_COLOR = "#a9a9a9"


class SplitPane(tk.PanedWindow):
    def __init__(self, master, orient="horizontal", **kw):
        kw.setdefault("sashwidth", SASH_WIDTH)
        kw.setdefault("sashrelief", "raised")
        kw.setdefault("bg", SASH_COLOR)
        kw.setdefault("bd", 0)
        super().__init__(master, orient=orient, **kw)
        self._vertical = orient == "vertical"

    def add(self, child, weight=0, minsize=40, **kw):
        super().add(child, stretch="always" if weight else "never", minsize=minsize, **kw)

    def sashpos(self, index, position=None):
        if position is None:
            x, y = self.sash_coord(index)
            return y if self._vertical else x
        if self._vertical:
            self.sash_place(index, 0, int(position))
        else:
            self.sash_place(index, int(position), 0)
        return position
