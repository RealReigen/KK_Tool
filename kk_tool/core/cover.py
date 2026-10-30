"""Extrae la portada (la imagen PNG) de una card sin cargar los datos del personaje."""

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def read_cover_png(path):
    """Devuelve los bytes del PNG de portada (hasta IEND). Lee solo lo necesario."""
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != PNG_SIG:
            raise ValueError("no es un PNG")
        parts = [sig]
        while True:
            head = f.read(8)
            if len(head) < 8:
                raise ValueError("PNG incompleto")
            length = int.from_bytes(head[:4], "big")
            if length > 100_000_000:
                raise ValueError("bloque PNG anómalo")
            body = f.read(length + 4)  # datos + CRC
            parts += [head, body]
            if head[4:8] == b"IEND":
                break
    return b"".join(parts)
