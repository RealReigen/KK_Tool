"""Memoria de la app (settings.json en la carpeta KK_Tool). Sin dependencias de GUI."""
import json
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]  # carpeta KK_Tool
SETTINGS_FILE = ROOT_DIR / "settings.json"


class Settings:
    """Claves con puntos: settings.get("tabs.futa.folders", [])."""

    def __init__(self, path=SETTINGS_FILE):
        self.path = Path(path)
        self.data = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(self.data, dict):
                raise ValueError("no es un objeto JSON")
        except Exception:
            # archivo dañado: se conserva una copia y se empieza limpio
            try:
                os.replace(self.path, self.path.with_suffix(".json.bad"))
            except OSError:
                pass
            self.data = {}

    def get(self, key, default=None):
        node = self.data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key, value):
        parts = key.split(".")
        node = self.data
        for part in parts[:-1]:
            if not isinstance(node.get(part), dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        self.save()

    def save(self):
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)  # escritura atómica
