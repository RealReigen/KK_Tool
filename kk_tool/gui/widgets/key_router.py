"""Teclado de las listas de cards, válido aunque el foco esté fuera de la lista.

Teclas (solo actúan si el foco NO está en un cuadro de texto, desplegable o similar):
  ↑ / ↓      mover la selección de la lista activa (si el foco ya está en la lista, lo hace el propio Tk)
  Enter      marcar/desmarcar las filas seleccionadas (solo listas con casillas)
  Ctrl+A     seleccionar todas las filas visibles (no en listas de selección única)
  Esc        quitar la selección

"Lista activa" = la que contiene el foco; si el foco está fuera de todas (botones de otra zona, el
registro…), la última que se usó en la pestaña visible. Los diálogos (otra ventana) se ignoran.
Para ampliar: añadir una tecla = un método `_xxx` + una línea en __init__.
"""
import tkinter as tk

# Clases de widget donde escribir/elegir tiene prioridad: aquí el router no interviene nunca.
TEXT_CLASSES = {"Entry", "TEntry", "Text", "TCombobox", "Spinbox", "TSpinbox", "Listbox"}


class KeyRouter:
    def __init__(self, root):
        self.root = root
        self.panels = []        # paneles registrados (CardPanel se registra solo)
        self.last = None        # última lista usada
        root.key_router = self
        root.bind_all("<FocusIn>", self._focus_in, add="+")
        root.bind_all("<Up>", lambda e: self._arrow(e, -1), add="+")
        root.bind_all("<Down>", lambda e: self._arrow(e, +1), add="+")
        root.bind_all("<Return>", self._enter, add="+")
        root.bind_all("<KP_Enter>", self._enter, add="+")
        root.bind_all("<Control-a>", self._select_all, add="+")
        root.bind_all("<Control-A>", self._select_all, add="+")
        root.bind_all("<Escape>", self._escape, add="+")

    def register(self, panel):
        self.panels.append(panel)

    # ---------- contexto ----------
    @staticmethod
    def _panel_of(widget):
        w = widget
        while w is not None:
            if getattr(w, "is_card_panel", False):
                return w
            w = getattr(w, "master", None)
        return None

    def _fallback(self):
        def visible(p):
            try:
                return bool(p.winfo_viewable())
            except tk.TclError:
                return False
        if self.last is not None and visible(self.last):
            return self.last
        return next((p for p in self.panels if visible(p)), None)

    def _context(self, event):
        """(widget con el foco, lista que debe actuar) o None si el router no debe intervenir."""
        w = event.widget
        if not isinstance(w, tk.Misc):
            return None
        try:
            if w.winfo_toplevel() is not self.root or w.winfo_class() in TEXT_CLASSES:
                return None
        except tk.TclError:
            return None
        panel = self._panel_of(w) or self._fallback()
        if panel is None:
            return None
        self.last = panel
        return w, panel

    def _focus_in(self, event):
        p = self._panel_of(event.widget) if isinstance(event.widget, tk.Misc) else None
        if p is not None:
            self.last = p

    # ---------- teclas ----------
    def _arrow(self, event, delta):
        ctx = self._context(event)
        if not ctx:
            return None
        widget, panel = ctx
        if widget is panel.tree:
            return None             # ya está en la lista: funciona el comportamiento normal de Tk
        panel.move_selection(delta)
        return "break"

    def _enter(self, event):
        ctx = self._context(event)
        if not ctx or not ctx[1].checkable:
            return None
        ctx[1].toggle_selected_checks()
        return "break"

    def _select_all(self, event):
        ctx = self._context(event)
        return "break" if ctx and ctx[1].select_all_visible() else None

    def _escape(self, event):
        ctx = self._context(event)
        if not ctx:
            return None
        ctx[1].clear_selection()
        return "break"
