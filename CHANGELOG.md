# Changelog

Newest first. The early v1–v7 numbering referred to the project status document; the code started at v0.1.

## 0.5.5 — 2026-10-30
- Fix: an exception inside a queued GUI callback no longer stops the `Worker` queue (the tab stayed "busy" forever).
- `save_card` now refuses to write if the destination already exists (no longer relies on `original_file_path`).
- `altura` attribute: the slider term now weighs 0.2 (measured model); cuts changed to ±0.04 (`atributos.json`).
- Card list shows the name as last name + first name, like the game and the `[mode: donor]` tag.
- `FilterBar.clear()` refreshes once; `donate` CLI warns about paths that do not exist.
- Added `requirements.txt` and `__version__`.

## 0.5.4 — 2026-10-30
- "Female → Futa" is now a **checklist**: ☐/☑ checkboxes independent of the preview selection (clicking another card to see its cover no longer unchecks the previous ones). New buttons: "Marcar todas" (check all), "Ninguna" (none) and "Marcar las seleccionadas" (check selected), plus a counter of checked cards.
- `CardListTab.checkable`: any list tab can enable checkboxes.
- Repository files added: `.gitignore`, `.gitattributes`, `README.md`, `README.es.md` and this `CHANGELOG.md`.

## 0.5.3
- New tab **"Reparar pene (futas)"**: fixes the penis size of futas that were already made, into new verified copies (`batch/repair.py`, `editors/penis_size.py::needs_repair`).
- `OutDirMixin`: the output folder is shared between "Female → Futa" and the repair tab.

## 0.5.2
- The penis compensation now also takes the **height slider** into account (measured model: body scale = 0.9 + 0.2 × slider). `config/medidas.json`.
- Confirmed in game: H scenes work much better; the remaining clipping also happens with the default cards.

## 0.5.1
- Penis size compensated by height (only the `cf_n_height` bone). New "Pene" column and filter. It did nothing on cards whose height was set only through the slider (fixed in 0.5.2).

## 0.5.0
- Search, sorting and attribute filters in every card list. Attributes are defined in `config/atributos.json` (height, breasts, type, penis…).

## 0.4.3
- Reset of the genital bones (`cf_d_kokan`, `cf_j_kokan`…) when converting to futa and when donating to a futa/male.

## 0.4.2
- Donate and convert to futa in a single action.

## 0.4.1
- Name of donated cards: `Name [mode: Donor]`.
- Female → Futa keeps the subfolder structure of the input folder.
- `Bulge` always disabled and `DisplayBalls` always `False`.

## 0.4.0
- New tab **"Donante → Receptores"**: donation engine with 3 modes (full, keep height, breasts), grey strip on the cover and a hidden donor marker. Reusable `CardPanel` and `Worker`.

## 0.3.x
- 0.3.2: recycle bin (`send2trash`) and resizable columns and dividers.
- 0.3: tabbed GUI, cover viewer and remembered settings.

## 0.1 – 0.2
- Core (`core`, `readers`, `editors/futa`, `batch`) and the first atomic, verified female → futa conversion.
