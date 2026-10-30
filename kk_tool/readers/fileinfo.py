"""Datos del archivo en disco (fechas y tamaño que da Windows). Solo lectura."""
import os
from datetime import datetime


def file_info(path):
    """{'mtime','ctime','size'}. En Windows ctime es la fecha de creación."""
    try:
        st = os.stat(path)
        return {"mtime": st.st_mtime, "ctime": st.st_ctime, "size": st.st_size}
    except OSError:
        return {"mtime": None, "ctime": None, "size": None}


def fmt_date(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""
