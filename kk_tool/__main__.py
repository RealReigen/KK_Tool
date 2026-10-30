"""Uso:
  python -m kk_tool                       -> abre la ventana
  python -m kk_tool summary <card|carpeta> -> resumen por consola
  python -m kk_tool donate <donante.png> <receptora|carpeta> [...] [--modo total|sinaltura|pechos]
                           [--salida carpeta] [--body-guid fijo|donante] [--sin-portada] [--futa]
        (donacion de cuerpo por consola; tambien tiene su pestaña en la ventana)"""
import sys
from pathlib import Path
from .batch.scan import scan


def _format(rows):
    lines = []
    for path, s, err in rows:
        lines.append(f"\n== {path.name}")
        if err:
            lines.append(f"  ERROR: {err}")
            continue
        for k, v in s.items():
            if k in ("sliders", "bones_scale"):     # medidas en bruto: demasiado largas para el resumen
                continue
            lines.append(f"  {k:20} {v}")
    return "\n".join(lines)


def _donate(argv):
    import argparse
    from .batch.donate import donate_cards
    from .batch.scan import find_cards_multi
    from .core.settings import ROOT_DIR
    ap = argparse.ArgumentParser(prog="python -m kk_tool donate")
    ap.add_argument("donante")
    ap.add_argument("receptoras", nargs="+", help="cards o carpetas")
    ap.add_argument("--modo", default="total", choices=["total", "sinaltura", "pechos"])
    ap.add_argument("--salida", default=str(ROOT_DIR / "salida_donaciones"))
    ap.add_argument("--body-guid", default="fijo", choices=["fijo", "donante"])
    ap.add_argument("--sin-portada", action="store_true", help="no dibujar la franja de texto")
    ap.add_argument("--futa", action="store_true", help="convertir tambien las receptoras a futa")
    a = ap.parse_args(argv)
    files = [p for p in a.receptoras if Path(p).is_file()]
    folders = [p for p in a.receptoras if Path(p).is_dir()]
    cards, missing = find_cards_multi(folders) if folders else ([], [])
    recs = files + [str(c) for c in cards]
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ok, skipped, failed = donate_cards(a.donante, recs, a.modo, a.salida, a.body_guid,
                                       with_cover=False if a.sin_portada else None,
                                       make_futa=a.futa)
    return 0 if failed == 0 else 2


def main(argv):
    if argv and argv[0] == "donate":
        return _donate(argv[1:])
    if not argv:
        from .gui.app import run
        run()
        return 0
    if len(argv) != 2 or argv[0] != "summary":
        print(__doc__)
        return 1
    text = _format(scan(argv[1]))
    Path("resumen.txt").write_text(text, encoding="utf-8")
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    print(text)
    print("\n(Resumen guardado tambien en resumen.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
