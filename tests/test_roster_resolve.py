"""python3 -m unittest tests.test_roster_resolve   (run from the repo root)"""
import datetime, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
import roster_resolve as R

TODAY = datetime.date(2026, 11, 12)
MAPPED = ['Aaron Ford', 'Joe Lombardo']


def obs(tier=3, total=3, names=None, as_of='2026-11-10', pub='P', **kw):
    o = {'tier': tier, 'publisher': pub, 'url': 'https://x.test/' + pub, 'as_of': as_of, 'retrieved': '2026-11-11', 'total': total}
    if names: o['names'] = names
    o.update(kw); return o


class Resolve(unittest.TestCase):
    def go(self, *o, ev=None):
        return R.resolve_race('nv', ev or {'observations': list(o)}, MAPPED, TODAY)

    def test_higher_tier_wins_and_conflict_is_logged(self):
        r, u, _ = self.go(obs(tier=4, total=5, pub='News'), obs(tier=1, total=3, pub='State'))
        self.assertEqual((r['total'], r['confidence'], r['publisher']), (3, 'confirmed', 'State'))
        self.assertEqual(r['conflicts'][0]['count'], 5)

    def test_same_rank_same_date_disagreement_is_unresolved(self):
        r, u, _ = self.go(obs(total=3, pub='A'), obs(total=4, pub='B'))
        self.assertIsNone(r); self.assertIn('disagree', u)

    def test_newer_same_tier_wins(self):
        r, _, _ = self.go(obs(total=5, as_of='2026-10-01', pub='Old'), obs(total=3, as_of='2026-11-09', pub='New'))
        self.assertEqual(r['total'], 3)

    def test_bad_observation_is_skipped_not_fatal(self):
        r, _, w = self.go({'tier': 9}, 'junk', obs(total=3))
        self.assertEqual(r['total'], 3); self.assertEqual(len(w), 2)

    def test_no_valid_observation_gives_unverified(self):
        r, u, w = self.go({'tier': 9}, ev=None)
        self.assertIsNone(r)

    def test_unresolved_note_passes_through(self):
        r, u, _ = self.go(ev={'unresolved': 'Check the state list', 'observations': []})
        self.assertIsNone(r); self.assertEqual(u, 'Check the state list')

    def test_similar_surnames_are_different_people(self):
        r, _, _ = self.go(obs(total=3, names=['Aaron Ford', 'Joe Lombardo', 'Danielle Ford (Independent)']))
        self.assertEqual(r['omitted'], ['Danielle Ford (Independent)'])

    def test_mapped_candidate_missing_from_source_warns(self):
        r, _, w = self.go(obs(total=3, names=['Aaron Ford', 'Someone Else', 'Third Person']))
        self.assertTrue(any('not in the source list' in x for x in w))

    def test_partial_list_is_marked_at_least(self):
        r, _, _ = self.go(obs(total=None, names=['Aaron Ford', 'Joe Lombardo', 'Third Person'], exhaustive=False))
        self.assertTrue(r['at_least']); self.assertEqual(r['total'], 3)

    def test_stale_evidence_warns(self):
        _, _, w = self.go(obs(total=3, retrieved='2026-10-01'))
        self.assertTrue(any('days old' in x for x in w))


class Files(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); os.makedirs(os.path.join(self.d, 'errata', 'evidence')); os.makedirs(os.path.join(self.d, 'elections', 'nv'))
        json.dump({'candidates': {'a': {'full': 'Aaron Ford'}, 'b': {'full': 'Joe Lombardo'}}}, open(os.path.join(self.d, 'elections', 'nv', 'config.json'), 'w'))

    def put(self, name, text): open(os.path.join(self.d, 'errata', 'evidence', name), 'w').write(text)

    def test_one_corrupt_file_does_not_block_others(self):
        self.put('nv.json', json.dumps({'observations': [obs(total=3)]})); self.put('tx.json', '{not json')
        out, warns = R.resolve_all(self.d, TODAY)
        self.assertIn('nv', out['races']); self.assertTrue(any('tx' in w for w in warns))

    def test_failed_run_keeps_last_good_file(self):
        path = os.path.join(self.d, 'errata', 'rosters.json'); json.dump({'races': {'keep': {}}}, open(path, 'w'))
        self.put('nv.json', '{broken')
        self.assertEqual(R.resolve(self.d), 1); self.assertIn('keep', json.load(open(path))['races'])

    def test_successful_run_writes_backup(self):
        path = os.path.join(self.d, 'errata', 'rosters.json'); json.dump({'races': {'old': {}}}, open(path, 'w'))
        self.put('nv.json', json.dumps({'observations': [obs(total=3)]}))
        self.assertEqual(R.resolve(self.d), 0)
        self.assertIn('old', json.load(open(path.replace('.json', '.last-good.json')))['races'])


if __name__ == '__main__':
    unittest.main()
