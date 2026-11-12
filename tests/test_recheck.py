import datetime, unittest
from src import recheck as R

OBS = {'publisher': 'X', 'url': 'u', 'as_of': '2026-11-12', 'names': ['Tom Tiffany (Republican)', 'David Crowley (Democratic)', 'Ben Johnson Jr.']}
PAGE = ('<html><body>' + 'Candidates on ballot. ' * 30 + 'TIFFANY Republican Crowley Democratic Johnson</body></html>').encode()

def f(body, ctype='text/html'):
    return lambda url: (body, ctype)

def boom(url):
    raise OSError('403')

class T(unittest.TestCase):
    def test_last_name(self):
        self.assertEqual(R.last_name('Ben Johnson Jr.'), 'Johnson')
        self.assertEqual(R.last_name('Tom Tiffany (Republican)'), 'Tiffany')
    def test_ok(self):
        self.assertEqual(R.check_race('r', OBS, f(PAGE))['status'], 'ok')
    def test_review_when_a_name_vanishes(self):
        body = PAGE.replace(b'Crowley', b'')
        r = R.check_race('r', OBS, f(body))
        self.assertEqual(r['status'], 'review'); self.assertIn('Crowley', r['why'])
    def test_manual_when_script_page(self):
        self.assertEqual(R.check_race('r', OBS, f(b'<html><script>app()</script></html>'))['status'], 'manual')
    def test_manual_when_no_name_found(self):
        body = ('<p>' + 'nothing here ' * 60 + '</p>').encode()
        self.assertEqual(R.check_race('r', OBS, f(body))['status'], 'manual')
    def test_manual_on_error(self):
        self.assertEqual(R.check_race('r', OBS, boom)['status'], 'manual')
    def test_window(self):
        self.assertEqual(R.main([], f(PAGE), today=datetime.date(2026, 11, 20)), 0)
    def test_render_flags_limit(self):
        rep = R.render([R.check_race('r', OBS, boom)], datetime.date(2026, 12, 7))
        self.assertIn('cannot see a candidate added', rep); self.assertIn('Manual checklist', rep)

if __name__ == '__main__':
    unittest.main()
