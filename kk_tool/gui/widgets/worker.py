"""Ejecutor en segundo plano para la interfaz.

El hilo nunca toca widgets: envía funciones con post(fn, *args) y se ejecutan en el hilo de Tk.
"""
import queue
import threading


class Worker:
    def __init__(self, widget, on_state=None, on_error=None):
        self.widget = widget
        self.q = queue.Queue()
        self.busy = False
        self.on_state = on_state      # on_state(busy: bool), al empezar y al terminar
        self.on_error = on_error      # on_error(exc)
        self._after = widget.after(100, self._poll)
        widget.bind("<Destroy>", self._destroy, add="+")

    def post(self, fn, *args, **kw):
        self.q.put((fn, args, kw))

    def start(self, fn):
        """Ejecuta fn(post) en un hilo. Ignorado si ya hay algo en marcha."""
        if self.busy:
            return
        self._set_busy(True)

        def work():
            try:
                fn(self.post)
            except Exception as e:  # el error se muestra; la ventana no se cuelga
                self.post(self._error, e)
            self.post(self._set_busy, False)

        threading.Thread(target=work, daemon=True).start()

    def _error(self, exc):
        if self.on_error:
            self.on_error(exc)

    def _set_busy(self, value):
        self.busy = value
        if self.on_state:
            self.on_state(value)

    def _poll(self):
        try:
            while True:
                fn, args, kw = self.q.get_nowait()
                fn(*args, **kw)
        except queue.Empty:
            pass
        self._after = self.widget.after(100, self._poll)

    def _destroy(self, event):
        if event.widget is self.widget:
            try:
                self.widget.after_cancel(self._after)
            except Exception:
                pass
