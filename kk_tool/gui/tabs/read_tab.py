"""Pestaña 'Leer datos': solo consulta, no modifica nada."""
from .base import BASE_COLUMNS, CardListTab
from ..widgets.card_panel import PENE_COLUMN, attribute_columns


class ReadTab(CardListTab):
    key = "leer"
    title = "Leer datos"
    columns = BASE_COLUMNS + [
        ("sexo", "Sexo", 60, lambda p, s: "male" if s["sex"] == 0 else "female"),
        ("trap", "Trap", 50, lambda p, s: "sí" if s["is_trap"] else "no"),
        ("plugins", "Plugins", 60, lambda p, s: s["n_plugins"]),
        ("donante", "Cuerpo de", 130, lambda p, s: s["donante"] or ""),
        PENE_COLUMN,
    ] + attribute_columns(skip=("tipo", "pene"))      # una columna por atributo de config/atributos.json (altura, pecho…)
