"""Test script for the dumbdbm module
   Original by Roger E. Masse
"""
import io
import operator
import os
import stat
import unittest
import warnings
import dbm.dumb as dumbdbm
from test import support
from functools import partial
_fname = support.TESTFN


def _delete_files():
    for ext in ['.dir', '.dat', '.bak']:
        try:
            os.unlink(_fname + ext)
        except OSError:
            pass


class DumbDBMTestCase(unittest.TestCase):
    _dict = {b'0': b'', b'a': b'Python:', b'b': b'Programming', b'c':
        b'the', b'd': b'way', b'f': b'Guido', b'g': b'intended', 'ü'.encode
        ('utf-8'): b'!'}

    def test_dumbdbm_creation(self):
        f = dumbdbm.open(_fname, 'c')
        self.assertEqual(list(f.keys()), [])
        for key in self._dict:
            f[key] = self._dict[key]
        self.read_helper(f)
        f.close()

    @unittest.skipUnless(hasattr(os, 'umask'), 'test needs os.umask()')
    @unittest.skipUnless(hasattr(os, 'chmod'), 'test needs os.chmod()')
    def test_dumbdbm_creation_mode(self):
        try:
            old_umask = os.umask(2)
            f = dumbdbm.open(_fname, 'c', 415)
            f.close()
        finally:
            os.umask(old_umask)
        expected_mode = 413
        if os.name != 'posix':
            expected_mode = 438
        import stat
        st = os.stat(_fname + '.dat')
        self.assertEqual(stat.S_IMODE(st.st_mode), expected_mode)
        st = os.stat(_fname + '.dir')
        self.assertEqual(stat.S_IMODE(st.st_mode), expected_mode)

    def test_close_twice(self):
        f = dumbdbm.open(_fname)
        f[b'a'] = b'b'
        self.assertEqual(f[b'a'], b'b')
        f.close()
        f.close()

    def test_dumbdbm_modification(self):
        self.init_db()
        f = dumbdbm.open(_fname, 'w')
        self._dict[b'g'] = f[b'g'] = b'indented'
        self.read_helper(f)
        f.close()

    def test_dumbdbm_read(self):
        self.init_db()
        f = dumbdbm.open(_fname, 'r')
        self.read_helper(f)
        with self.assertWarnsRegex(DeprecationWarning,
            'The database is opened for reading only'):
            f[b'g'] = b'x'
        with self.assertWarnsRegex(DeprecationWarning,
            'The database is opened for reading only'):
            del f[b'a']
        f.close()

    def test_dumbdbm_keys(self):
        self.init_db()
        f = dumbdbm.open(_fname)
        keys = self.keys_helper(f)
        f.close()

    def test_write_contains(self):
        f = dumbdbm.open(_fname)
        f[b'1'] = b'hello'
        self.assertIn(b'1', f)
        f.close()

    def test_write_write_read(self):
        f = dumbdbm.open(_fname)
        f[b'1'] = b'hello'
        f[b'1'] = b'hello2'
        f.close()
        f = dumbdbm.open(_fname)
        self.assertEqual(f[b'1'], b'hello2')
        f.close()

    def test_str_read(self):
        self.init_db()
        f = dumbdbm.open(_fname, 'r')
        self.assertEqual(f['ü'], self._dict['ü'.encode('utf-8')])

    def test_str_write_contains(self):
        self.init_db()
        f = dumbdbm.open(_fname)
        f['ü'] = b'!'
        f['1'] = 'a'
        f.close()
        f = dumbdbm.open(_fname, 'r')
        self.assertIn('ü', f)
        self.assertEqual(f['ü'.encode('utf-8')], self._dict['ü'.encode(
            'utf-8')])
        self.assertEqual(f[b'1'], b'a')

    def test_line_endings(self):
        f = dumbdbm.open(_fname)
        f[b'1'] = b'hello'
        f[b'2'] = b'hello2'
        f.close()
        with io.open(_fname + '.dir', 'rb') as file:
            data = file.read()
        if os.linesep == '\n':
            data = data.replace(b'\n', b'\r\n')
        else:
            data = data.replace(b'\r\n', b'\n')
        with io.open(_fname + '.dir', 'wb') as file:
            file.write(data)
        f = dumbdbm.open(_fname)
        self.assertEqual(f[b'1'], b'hello')
        self.assertEqual(f[b'2'], b'hello2')

    def read_helper(self, f):
        keys = self.keys_helper(f)
        for key in self._dict:
            self.assertEqual(self._dict[key], f[key])

    def init_db(self):
        f = dumbdbm.open(_fname, 'n')
        for k in self._dict:
            f[k] = self._dict[k]
        f.close()

    def keys_helper(self, f):
        keys = sorted(f.keys())
        dkeys = sorted(self._dict.keys())
        self.assertEqual(keys, dkeys)
        return keys

    def test_random(self):
        import random
        d = {}
        for dummy in range(5):
            f = dumbdbm.open(_fname)
            for dummy in range(100):
                k = random.choice('abcdefghijklm')
                if random.random() < 0.2:
                    if k in d:
                        del d[k]
                        del f[k]
                else:
                    v = random.choice((b'a', b'b', b'c')) * random.randrange(
                        10000)
                    d[k] = v
                    f[k] = v
                    self.assertEqual(f[k], v)
            f.close()
            f = dumbdbm.open(_fname)
            expected = sorted((k.encode('latin-1'), v) for k, v in d.items())
            got = sorted(f.items())
            self.assertEqual(expected, got)
            f.close()

    def test_context_manager(self):
        with dumbdbm.open(_fname, 'c') as db:
            db['dumbdbm context manager'] = 'context manager'
        with dumbdbm.open(_fname, 'r') as db:
            self.assertEqual(list(db.keys()), [b'dumbdbm context manager'])
        with self.assertRaises(dumbdbm.error):
            db.keys()

    def test_check_closed(self):
        f = dumbdbm.open(_fname, 'c')
        f.close()
        for meth in (partial(operator.delitem, f), partial(operator.setitem,
            f, 'b'), partial(operator.getitem, f), partial(operator.
            contains, f)):
            with self.assertRaises(dumbdbm.error) as cm:
                meth('test')
            self.assertEqual(str(cm.exception),
                'DBM object has already been closed')
        for meth in (operator.methodcaller('keys'), operator.methodcaller(
            'iterkeys'), operator.methodcaller('items'), len):
            with self.assertRaises(dumbdbm.error) as cm:
                meth(f)
            self.assertEqual(str(cm.exception),
                'DBM object has already been closed')

    def test_create_new(self):
        with dumbdbm.open(_fname, 'n') as f:
            for k in self._dict:
                f[k] = self._dict[k]
        with dumbdbm.open(_fname, 'n') as f:
            self.assertEqual(f.keys(), [])

    def test_eval(self):
        with open(_fname + '.dir', 'w') as stream:
            stream.write("str(print('Hacked!')), 0\n")
        with support.captured_stdout() as stdout:
            with self.assertRaises(ValueError):
                with dumbdbm.open(_fname) as f:
                    pass
            self.assertEqual(stdout.getvalue(), '')

    def test_warn_on_ignored_flags(self):
        for value in ('r', 'w'):
            _delete_files()
            with self.assertWarnsRegex(DeprecationWarning,
                "The database file is missing, the semantics of the 'c' flag will be used."
                ):
                f = dumbdbm.open(_fname, value)
            f.close()

    def test_invalid_flag(self):
        for flag in ('x', 'rf', None):
            with self.assertWarnsRegex(DeprecationWarning,
                "Flag must be one of 'r', 'w', 'c', or 'n'"):
                f = dumbdbm.open(_fname, flag)
            f.close()

    @unittest.skipUnless(hasattr(os, 'chmod'), 'test needs os.chmod()')
    def test_readonly_files(self):
        with support.temp_dir() as dir:
            fname = os.path.join(dir, 'db')
            with dumbdbm.open(fname, 'n') as f:
                self.assertEqual(list(f.keys()), [])
                for key in self._dict:
                    f[key] = self._dict[key]
            os.chmod(fname + '.dir', stat.S_IRUSR)
            os.chmod(fname + '.dat', stat.S_IRUSR)
            os.chmod(dir, stat.S_IRUSR | stat.S_IXUSR)
            with dumbdbm.open(fname, 'r') as f:
                self.assertEqual(sorted(f.keys()), sorted(self._dict))
                f.close()

    def tearDown(self):
        _delete_files()

    def setUp(self):
        _delete_files()


if __name__ == '__main__':
    unittest.main()
