from pathlib import Path
import tempfile
import unittest
from project_setup.licensing import generate, BEGIN

class LicensingTests(unittest.TestCase):
    def test_records_escaping_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'docs/nested').mkdir(parents=True)
            page = root/'docs/nested/index.html'
            page.write_text('<html><body>Hello</body></html>')
            (root/'LICENSE').write_text('Existing license')
            info = dict(project='demo', author='A <B>', author_email='a@example.org', author_affil='Institute', doi_paper='', link='https://example.org')
            generate(root, info, '{{project}} {{author}}')
            generate(root, info, '{{project}} {{author}}')
            self.assertEqual(page.read_text().count(BEGIN), 1)
            self.assertIn('A &lt;B&gt;', page.read_text())
            self.assertIn('../../lisence/LICENSE.html', page.read_text())
            self.assertEqual((root/'LICENSE').read_text(), 'Existing license')
            (root/'lisence/LICENSE.txt').write_text('Other rights')
            with self.assertRaises(ValueError):
                generate(root, info, 'test')

    def test_outside_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            (root/'docs').mkdir()
            (Path(outside)/'a.html').write_text('outside')
            (root/'docs/a.html').symlink_to(Path(outside)/'a.html')
            info = dict(project='demo', author='A', author_email='a@example.org', author_affil='I', doi_paper='', link='')
            with self.assertRaises(ValueError):
                generate(root, info, 'test')
            self.assertEqual((Path(outside)/'a.html').read_text(), 'outside')
