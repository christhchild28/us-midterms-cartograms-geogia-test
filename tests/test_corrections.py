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


class Drafts(unittest.TestCase):
    def setUp(self): self.ros, self.ent = C.ROS, C.ENT
    def tearDown(self): C.ROS, C.ENT = self.ros, self.ent
    def test_conflict_and_stale_are_reported_unless_already_an_error(self):
        import datetime
        C.ROS = {'races': {'a': {'total': 4, 'tier': 2, 'publisher': 'GP', 'retrieved': '2026-01-01', 'conflicts': [{'publisher': 'BP', 'tier': 3, 'count': 7}]},
                           'b': {'total': 4, 'tier': 2, 'publisher': 'GP', 'retrieved': '2026-11-12', 'conflicts': [{'publisher': 'BP', 'tier': 3, 'count': 7}]}}, 'unresolved': {'u': 'x'}}
        C.ENT = [{'id': 'E', 'kind': 'error', 'races': ['b']}]
        out = C.drafts(datetime.date(2026, 11, 12))
        self.assertTrue(any(x.startswith('a: BP says 7') for x in out)); self.assertTrue(any('a: roster evidence' in x for x in out))
        self.assertTrue(any(x.startswith('u:') for x in out)); self.assertFalse(any(x.startswith('b:') for x in out))


if __name__ == '__main__': unittest.main()
