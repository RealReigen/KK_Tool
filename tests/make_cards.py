"""Genera cards sintéticas (no son personajes reales) para probar sin necesidad de cards del usuario.

Se construyen con las propias clases de kkloader y se guardan como cualquier card: PNG + datos.
"""
import struct
import zlib

from kkloader import KoikatuCharaData
from kkloader.KoikatuCharaData import About, Coordinate, Custom, KKEx, Parameter, Status
from kkloader.funcs import msg_pack

KKEx.LZ4_UNPACK = True


def _png(w=4, h=4, rgb=(200, 120, 120)):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _block(cls, name, version, data):
    b = cls.__new__(cls)
    b.name, b.version, b.data = name, version, data
    return b


def make_card(path, first="Ana", last="Test", sex=1, height=0.5, hair=3, bones=None, plugins=None, cover=(200, 120, 120)):
    """Escribe una card sintética. bones: lista de huesos ABMX [nombre, [[[x,y,z], largo, pos, rot]], 1]."""
    kc = KoikatuCharaData()
    kc.image, kc.product_no = _png(rgb=cover), 100
    kc.header, kc.version, kc.face_image = "【KoiKatuChara】".encode(), b"0.0.0", _png()
    sliders = [0.5] * 44
    sliders[0] = height
    coords = [{"clothes": {"parts": [{"id": i, "colors": [[1.0, 0.5, 0.25, 1.0]]}]},
               "accessory": {"parts": []}, "enableMakeup": False, "makeup": {"lip": 1}} for i in range(7)]
    kkex = {"KKABMPlugin.ABMData": [2, {"boneData": bones}]} if bones is not None else {}
    kkex["madevil.kk.ca"] = [1, {"note": "x"}]
    kkex.update(plugins or {})
    blocks = {
        "Custom": _block(Custom, "Custom", "0.0.0", {"face": {"headId": 1, "shape": [0.1, 0.2]},
                                                     "body": {"shapeValueBody": sliders, "skinId": 2},
                                                     "hair": {"parts": [{"id": hair}]}}),
        "Coordinate": _block(Coordinate, "Coordinate", "0.0.0", coords),
        "Parameter": _block(Parameter, "Parameter", "0.0.5", {"sex": sex, "firstname": first, "lastname": last,
                                                             "nickname": "", "personality": 4}),
        "Status": _block(Status, "Status", "0.0.0", {"coordinateType": 0}),
        "About": _block(About, "About", "0.0.0", {"userID": "abc", "dataID": first}),
        "KKEx": _block(KKEx, "KKEx", "0.0.0", kkex),
    }
    kc._failed = None
    blocks["KKEx"]._failed_nested_paths = set()
    kc.blockdata = list(blocks)
    kc.unknown_blockdata = []
    kc.original_lstinfo_order = kc.serialized_lstinfo_order = list(blocks)
    for k, b in blocks.items():
        setattr(kc, k, b)
    kc.save(str(path))
    return path


KOKAN = ["cf_d_kokan", [[[0.66, 1.41, 1.0], 1.0, [0, 0, 0], [0, 0, 0]]], 1]
