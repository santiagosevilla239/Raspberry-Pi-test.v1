import unittest, tempfile, importlib.util, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import reproducir as native

class NativeTests(unittest.TestCase):
    def test_update_only_on_boundary_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            native.core.DATA=Path(temp)
            old={'file':'a'*64+'.mp4','version':'old'}
            new={'file':'b'*64+'.mp4','version':'new'}
            native.core.atomic_json(native.core.DATA/'state.json',{**old,'pending':new})
            # Descargar y preparar un pendiente no cambia el activo.
            self.assertEqual(native.core.state()['version'],'old')
            with patch.object(native,'validate',return_value={}):
                self.assertEqual(native.select_video().name,new['file'])
            self.assertEqual(native.core.state()['backup'],old)
            self.assertTrue(native.rollback())
            self.assertEqual(native.core.state()['version'],'old')

    def test_incompatible_update_keeps_current(self):
        with tempfile.TemporaryDirectory() as temp:
            native.core.DATA=Path(temp)
            old={'file':'a'*64+'.mp4','version':'old'}
            native.core.atomic_json(native.core.DATA/'state.json',{**old,'pending':{'file':'b'*64+'.mp4','version':'bad'}})
            with patch.object(native,'validate',side_effect=ValueError('Códec incompatible')):
                self.assertEqual(native.select_video().name,old['file'])
            self.assertEqual(native.core.state()['version'],'old')
            self.assertNotIn('pending',native.core.state())

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):native.safe_path({'file':'../../config.json'})

if __name__=='__main__':unittest.main()
