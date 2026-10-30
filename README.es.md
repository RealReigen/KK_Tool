# KK_Tool

🇬🇧 [English](README.md) · 🇪🇸 Español

Herramienta con interfaz gráfica (Python + tkinter) para gestionar y editar **en masa** cards de **Koikatsu original (KK)**. No sirve para Koikatsu Party ni Sunshine.

Base técnica: la librería `kkloader` para leer y escribir las cards. Todo el trabajo es sobre los datos de la card; los originales **nunca se modifican**: las herramientas escriben copias en una carpeta de salida y verifican cada copia tras guardarla.

## Qué hace

| Pestaña | Función |
|---|---|
| **Leer datos** | Lista las cards con nombre, tipo (female / male / futa), altura, tamaño efectivo del pene, plugins… Buscador, orden y filtros por atributos. |
| **Female → Futa** | Convierte las cards marcadas (casillas ☐/☑) a futa de forma atómica, resetea los huesos genitales y fija el tamaño del pene según la altura. |
| **Donante → Receptores** | Crea copias de las receptoras con el cuerpo de una card donante (modos total, sin altura, pechos), opcionalmente convirtiéndolas a futa. |
| **Reparar pene (futas)** | Corrige el tamaño del pene de futas ya hechas (copias nuevas). |

## Instalación (Windows)

1. Instala Python 3.10 o superior desde python.org (marca «Add Python to PATH»).
2. Doble clic en `instalar.bat` (solo la primera vez; instala `kkloader`, `send2trash` y `pillow`).
3. Doble clic en `abrir_programa.bat`, o desde una consola en esta carpeta: `python -m kk_tool`.

Más detalles de uso en [`LEEME.txt`](LEEME.txt).

## Estructura

```
kk_tool/
├── core/      lectura/escritura de cards, ajustes, búsqueda y filtros (sin GUI)
├── readers/   solo lectura: resúmenes y clasificación de cards
├── editors/   modifican la card en memoria (no tocan archivos)
├── batch/     orquestan lotes: guardan, releen y verifican
├── gui/       interfaz (pestañas y widgets)
└── config/    números del juego y definiciones en JSON (presets, donaciones, atributos, medidas)
```

Reglas de diseño: `editors/` nunca toca archivos, `batch/` orquesta y escribe, `gui/` solo es interfaz. Una función nueva = un archivo nuevo. Los números del juego van en `config/`, no en el código.

## Documentación

El estado del proyecto, las decisiones de diseño y lo medido sobre el formato de las cards están en [`docs/`](docs/) (el `.md` más reciente). El historial de versiones está en [`CHANGELOG.md`](CHANGELOG.md) (en inglés).

## Qué NO se sube a este repositorio

Las cards (`.png`), las carpetas de entrada y salida, y `settings.json` (rutas de cada PC) están excluidos en `.gitignore`.
