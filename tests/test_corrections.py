"""python3 -m unittest tests.test_corrections   (run from the repo root)"""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
import corrections as C


class Banner(unittest.TestCase):
    def setUp(self): self.ent, self.ban = C.ENT, C.BAN
    def tearDown(self): C.ENT, C.BAN = self.ent, self.ban
    def run_on(self, ent, mode='per_entry'):
        C.ENT = ent; C.BAN = {'mode': mode}; return C.banner_on('x')
    def e(self, **kw): d = {'id': 'E', 'races': ['x'], 'severity': 'S2', 'status': 'open'}; d.update(kw); return d

    def test_s2_is_off_by_default(self): self.assertFalse(self.run_on([self.e()]))
    def test_explicit_banner_turns_on(self): self.assertTrue(self.run_on([self.e(banner=True)]))
    def test_open_s1_forces_banner(self): self.assertTrue(self.run_on([self.e(severity='S1')]))
    def test_corrected_s1_does_not(self): self.assertFalse(self.run_on([self.e(severity='S1', status='corrected')]))
    def test_explicit_false_beats_s1(self): self.assertFalse(self.run_on([self.e(severity='S1', banner=False)]))
    def test_all_mode_restores_every_page(self): self.assertTrue(self.run_on([], 'all'))
    def test_page_not_in_any_entry(self): self.assertFalse(self.run_on([self.e(races=['y'])]))


if __name__ == '__main__': unittest.main()
