import importlib.util
import os
import py_compile
import shutil
import stat
import sys
import tempfile
import unittest
from test import support


class PyCompileTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.source_path = os.path.join(self.directory, '_test.py')
        self.pyc_path = self.source_path + 'c'
        self.cache_path = importlib.util.cache_from_source(self.source_path)
        self.cwd_drive = os.path.splitdrive(os.getcwd())[0]
        drive = os.path.splitdrive(self.source_path)[0]
        if drive:
            os.chdir(drive)
        with open(self.source_path, 'w') as file:
            file.write('x = 123\n')

    def tearDown(self):
        shutil.rmtree(self.directory)
        if self.cwd_drive:
            os.chdir(self.cwd_drive)

    def test_absolute_path(self):
        py_compile.compile(self.source_path, self.pyc_path)
        self.assertTrue(os.path.exists(self.pyc_path))
        self.assertFalse(os.path.exists(self.cache_path))

    def test_do_not_overwrite_symlinks(self):
        try:
            os.symlink(self.pyc_path + '.actual', self.pyc_path)
        except (NotImplementedError, OSError):
            self.skipTest('need to be able to create a symlink for a file')
        else:
            assert os.path.islink(self.pyc_path)
            with self.assertRaises(FileExistsError):
                py_compile.compile(self.source_path, self.pyc_path)

    @unittest.skipIf(not os.path.exists(os.devnull) or os.path.isfile(os.
        devnull), 'requires os.devnull and for it to be a non-regular file')
    def test_do_not_overwrite_nonregular_files(self):
        with self.assertRaises(FileExistsError):
            py_compile.compile(self.source_path, os.devnull)

    def test_cache_path(self):
        py_compile.compile(self.source_path)
        self.assertTrue(os.path.exists(self.cache_path))

    def test_cwd(self):
        with support.change_cwd(self.directory):
            py_compile.compile(os.path.basename(self.source_path), os.path.
                basename(self.pyc_path))
        self.assertTrue(os.path.exists(self.pyc_path))
        self.assertFalse(os.path.exists(self.cache_path))

    def test_relative_path(self):
        py_compile.compile(os.path.relpath(self.source_path), os.path.
            relpath(self.pyc_path))
        self.assertTrue(os.path.exists(self.pyc_path))
        self.assertFalse(os.path.exists(self.cache_path))

    @unittest.skipIf(hasattr(os, 'geteuid') and os.geteuid() == 0,
        'non-root user required')
    @unittest.skipIf(os.name == 'nt',
        'cannot control directory permissions on Windows')
    def test_exceptions_propagate(self):
        mode = os.stat(self.directory)
        os.chmod(self.directory, stat.S_IREAD)
        try:
            with self.assertRaises(IOError):
                py_compile.compile(self.source_path, self.pyc_path)
        finally:
            os.chmod(self.directory, mode.st_mode)

    def test_bad_coding(self):
        bad_coding = os.path.join(os.path.dirname(__file__), 'bad_coding2.py')
        with support.captured_stderr():
            self.assertIsNone(py_compile.compile(bad_coding, doraise=False))
        self.assertFalse(os.path.exists(importlib.util.cache_from_source(
            bad_coding)))

    @unittest.skipIf(sys.flags.optimize > 0, 'test does not work with -O')
    def test_double_dot_no_clobber(self):
        weird_path = os.path.join(self.directory, 'foo.bar.py')
        cache_path = importlib.util.cache_from_source(weird_path)
        pyc_path = weird_path + 'c'
        head, tail = os.path.split(cache_path)
        penultimate_tail = os.path.basename(head)
        self.assertEqual(os.path.join(penultimate_tail, tail), os.path.join
            ('__pycache__', 'foo.bar.{}.pyc'.format(sys.implementation.
            cache_tag)))
        with open(weird_path, 'w') as file:
            file.write('x = 123\n')
        py_compile.compile(weird_path)
        self.assertTrue(os.path.exists(cache_path))
        self.assertFalse(os.path.exists(pyc_path))

    def test_optimization_path(self):
        self.assertIn('opt-2', py_compile.compile(self.source_path, optimize=2)
            )


if __name__ == '__main__':
    unittest.main()
