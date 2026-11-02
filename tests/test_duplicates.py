"""Pruebas de la comparación por contenido y del reparto a male/ y male/duplicados/ (cards sintéticas).
Ejecutar desde la carpeta KK_Tool:  python -m unittest discover -s tests -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from make_cards import KOKAN, make_card                                   # noqa: E402
from kk_tool.batch.convert import convert_cards                           # noqa: E402
from kk_tool.batch.fp_cache import FingerprintCache                       # noqa: E402
from kk_tool.batch.futa_index import DUP_SUBDIR, FutaIndex                # noqa: E402
from kk_tool.core.card_io import load_card                                # noqa: E402
from kk_tool.core.game_paths import resolve_install                       # noqa: E402
from kk_tool.editors.futa import apply_futa, load_presets                 # noqa: E402
from kk_tool.readers.fingerprint import fingerprint                       # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.female, self.male, self.report = self.root / "female", self.root / "male", self.root / "report"
        self.female.mkdir()
        self.male.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def index(self):
        idx = FutaIndex(FingerprintCache(self.root / "cache.json"))
        idx.scan(self.male, log=lambda m: None)
        return idx

    def convert(self, names, idx):
        return convert_cards([self.female / n for n in names], self.male, self.report,
                             log=lambda m: None, roots=[self.female], index=idx)


class TestFingerprint(Base):
    def test_female_and_its_futa_have_same_fingerprint(self):
        for bones in (None, [], [KOKAN]):
            p = make_card(self.female / "x.png", bones=bones)
            card = load_card(p)
            before = fingerprint(card)
            apply_futa(card, load_presets()["futa_bp_sos"])
            self.assertEqual(before, fingerprint(card))
            p.unlink()

    def test_name_cover_and_file_name_do_not_matter(self):
        a = load_card(make_card(self.female / "a.png", first="Ana"))
        b = load_card(make_card(self.female / "otro_nombre.png", first="Renombrada", cover=(1, 2, 3)))
        self.assertEqual(fingerprint(a), fingerprint(b))

    def test_real_differences_are_detected(self):
        base = fingerprint(load_card(make_card(self.female / "a.png")))
        for kw in ({"hair": 4}, {"height": 0.3}, {"plugins": {"madevil.kk.ca": [1, {"note": "y"}]}},
                   {"bones": [["cf_s_bust00_L", [[[1.2, 1.2, 1.2], 1.0, [0, 0, 0], [0, 0, 0]]], 1]]}):
            other = fingerprint(load_card(make_card(self.female / "b.png", **kw)))
            self.assertNotEqual(base, other, kw)
            (self.female / "b.png").unlink()


class TestConvertDuplicates(Base):
    def test_new_card_goes_to_male_and_repeat_goes_to_duplicados(self):
        make_card(self.female / "ana.png", first="Ana", bones=[KOKAN])
        make_card(self.female / "bea.png", first="Bea", hair=9)
        idx = self.index()
        self.assertEqual(self.convert(["ana.png"], idx), (1, 0, 0, 0))
        self.assertTrue((self.male / "ana.png").exists())
        # segunda vez: el índice (actualizado en memoria) ya conoce la futa
        self.assertEqual(self.convert(["ana.png"], idx), (0, 0, 0, 1))
        self.assertTrue((self.male / DUP_SUBDIR / "ana.png").exists())
        # tercera vez: ya está también en duplicados/ -> no se amontona
        self.assertEqual(self.convert(["ana.png"], idx), (0, 1, 0, 0))
        self.assertEqual(len(list((self.male / DUP_SUBDIR).rglob("*.png"))), 1)
        # una card distinta sigue yendo a male/
        self.assertEqual(self.convert(["bea.png"], idx), (1, 0, 0, 0))
        self.assertTrue((self.male / "bea.png").exists())

    def test_rescan_from_disk_recognises_converted_futas(self):
        make_card(self.female / "ana.png", first="Ana", bones=[KOKAN])
        self.convert(["ana.png"], self.index())
        fresh = self.index()                       # índice nuevo, leído del disco (y de la caché)
        self.assertEqual(self.convert(["ana.png"], fresh), (0, 0, 0, 1))

    def test_same_content_twice_in_one_batch(self):
        make_card(self.female / "uno.png", first="Uno")
        make_card(self.female / "dos.png", first="Dos")          # mismo contenido, otro nombre
        self.assertEqual(self.convert(["uno.png", "dos.png"], self.index()), (1, 0, 0, 1))

    def test_futa_converted_with_old_penis_size_still_counts(self):
        make_card(self.female / "ana.png", first="Ana", height=0.1)
        card = load_card(self.female / "ana.png")
        apply_futa(card, load_presets()["futa_bp_sos"])
        card["KKEx"].data["KKABMPlugin.ABMData"][1]["boneData"] = []     # futa «antigua» sin compensar el pene
        card.save(str(self.male / "vieja.png"))
        self.assertEqual(self.convert(["ana.png"], self.index()), (0, 0, 0, 1))

    def test_without_index_nothing_is_compared(self):
        make_card(self.female / "ana.png")
        self.convert(["ana.png"], None)
        make_card(self.female / "ana2.png")
        self.assertEqual(self.convert(["ana2.png"], None)[3], 0)

    def test_subfolders_and_report_dir(self):
        (self.female / "A" / "B").mkdir(parents=True)
        make_card(self.female / "A" / "B" / "ana.png")
        convert_cards([self.female / "A" / "B" / "ana.png"], self.male, self.report,
                      log=lambda m: None, roots=[self.female], index=self.index())
        self.assertTrue((self.male / "A" / "B" / "ana.png").exists())
        self.assertTrue((self.report / "log.txt").exists())
        self.assertFalse((self.male / "log.txt").exists())


class TestExtraFolders(Base):
    def test_futa_in_extra_folder_counts_as_done(self):
        legacy = self.root / "viejas"
        legacy.mkdir()
        make_card(self.female / "ana.png", first="Ana")
        old_male = self.root / "salida_male"
        old_male.mkdir()
        convert_cards([self.female / "ana.png"], legacy, self.report, log=lambda m: None, roots=[self.female])
        idx = FutaIndex(FingerprintCache(self.root / "cache.json"))
        idx.scan(self.male, log=lambda m: None, extra=[legacy, legacy, self.male, self.root / "no_existe"])
        self.assertEqual(len(idx.roots), 2)                      # sin repetir ni contar la salida ni la inexistente
        fp = fingerprint(load_card(self.female / "ana.png"))
        self.assertEqual(idx.find_main(fp), legacy / "ana.png")
        # la futa existe en la carpeta extra: convertir de nuevo la manda a male/duplicados/
        self.assertEqual(self.convert(["ana.png"], idx), (0, 0, 0, 1))
        self.assertTrue((self.male / DUP_SUBDIR / "ana.png").exists())


class TestGamePaths(Base):
    def test_resolve(self):
        chara = self.root / "Koikatsu X" / "UserData" / "chara"
        (chara / "female").mkdir(parents=True)
        (chara / "male").mkdir()
        want = resolve_install(self.root / "Koikatsu X")
        self.assertEqual((want.female, want.male), (chara / "female", chara / "male"))
        for p in (chara.parent, chara, chara / "female", chara / "male"):
            self.assertEqual(resolve_install(p), want)
        self.assertIsNone(resolve_install(self.root))
        self.assertIsNone(resolve_install(""))


if __name__ == "__main__":
    unittest.main()
