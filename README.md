# KK_Tool

🇬🇧 English · 🇪🇸 [Español](README.es.md)

A desktop tool (Python + tkinter) to manage and **bulk-edit** character cards for the original **Koikatsu (KK)**. It does not support Koikatsu Party or Sunshine.

It is built on the [`kkloader`](https://pypi.org/project/kkloader/) library to read and write cards. Original cards are **never modified**: every tool writes copies to an output folder and verifies each copy after saving it.

## What it does

| Tab | Purpose |
|---|---|
| **Leer datos** (Read data) | Lists cards with name, type (female / male / futa), height, effective penis size, plugins… Includes search, sorting and attribute filters. |
| **Female → Futa** | Converts the checked cards (☐/☑ checkboxes) to futa atomically, resets the genital bones and sets the penis size according to the body height. |
| **Donante → Receptores** (Donor → Recipients) | Creates copies of the recipient cards with the body of a donor card (modes: full, keep height, breasts only), optionally converting them to futa. |
| **Reparar pene (futas)** (Fix penis size) | Fixes the penis size of futas that were already converted (writes new copies). |

> The interface is currently in Spanish. Language selection is planned for the future.

## Installation (Windows)

1. Install Python 3.10 or newer from python.org (tick "Add Python to PATH").
2. Double-click `instalar.bat` (first time only; installs `kkloader`, `send2trash` and `pillow`).
3. Double-click `abrir_programa.bat`, or run `python -m kk_tool` from a console in this folder.

More usage details are in [`LEEME.txt`](LEEME.txt) (Spanish).

## Project structure

```
kk_tool/
├── core/      card I/O, settings, search and filtering (no GUI)
├── readers/   read-only: card summaries and classification
├── editors/   modify the card in memory (never touch files)
├── batch/     orchestrate batches: save, reload and verify
├── gui/       interface (tabs and widgets)
└── config/    game numbers and definitions as JSON (presets, donations, attributes, measurements)
```

Design rules: `editors/` never touches files, `batch/` orchestrates and writes, `gui/` is interface only. A new feature = a new file. Game-related numbers live in `config/`, not in the code.

## Documentation

Project status, design decisions and what has been measured about the card format are in [`docs/`](docs/) (the latest `.md`, in Spanish). Version history is in [`CHANGELOG.md`](CHANGELOG.md).

## What is NOT stored in this repository

Cards (`.png`), the input/output folders and `settings.json` (per-PC paths) are excluded through `.gitignore`.
