"""Test program for the fcntl C module.
"""
import platform
import os
import struct
import sys
import unittest
from test.support import verbose, TESTFN, unlink, run_unittest, import_module, cpython_only
fcntl = import_module('fcntl')


def get_lockdata():
    try:
        os.O_LARGEFILE
    except AttributeError:
        start_len = 'll'
    else:
        start_len = 'qq'
    if sys.platform.startswith(('netbsd', 'freebsd', 'openbsd', 'bsdos')
        ) or sys.platform == 'darwin':
        if struct.calcsize('l') == 8:
            off_t = 'l'
            pid_t = 'i'
        else:
            off_t = 'lxxxx'
            pid_t = 'l'
        lockdata = struct.pack(off_t + off_t + pid_t + 'hh', 0, 0, 0, fcntl
            .F_WRLCK, 0)
    elif sys.platform.startswith('gnukfreebsd'):
        lockdata = struct.pack('qqihhi', 0, 0, 0, fcntl.F_WRLCK, 0, 0)
    elif sys.platform in ['aix3', 'aix4', 'hp-uxB', 'unixware7']:
        lockdata = struct.pack('hhlllii', fcntl.F_WRLCK, 0, 0, 0, 0, 0, 0)
    else:
        lockdata = struct.pack('hh' + start_len + 'hh', fcntl.F_WRLCK, 0, 0,
            0, 0, 0)
    if lockdata:
        if verbose:
            print('struct.pack: ', repr(lockdata))
    return lockdata


lockdata = get_lockdata()


class BadFile:

    def __init__(self, fn):
        self.fn = fn

    def fileno(self):
        return self.fn


class TestFcntl(unittest.TestCase):

    def setUp(self):
        self.f = None

    def tearDown(self):
        if self.f and not self.f.closed:
            self.f.close()
        unlink(TESTFN)

    def test_fcntl_fileno(self):
        self.f = open(TESTFN, 'wb')
        rv = fcntl.fcntl(self.f.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        if verbose:
            print('Status from fcntl with O_NONBLOCK: ', rv)
        rv = fcntl.fcntl(self.f.fileno(), fcntl.F_SETLKW, lockdata)
        if verbose:
            print('String from fcntl with F_SETLKW: ', repr(rv))
        self.f.close()

    def test_fcntl_file_descriptor(self):
        self.f = open(TESTFN, 'wb')
        rv = fcntl.fcntl(self.f, fcntl.F_SETFL, os.O_NONBLOCK)
        if verbose:
            print('Status from fcntl with O_NONBLOCK: ', rv)
        rv = fcntl.fcntl(self.f, fcntl.F_SETLKW, lockdata)
        if verbose:
            print('String from fcntl with F_SETLKW: ', repr(rv))
        self.f.close()

    def test_fcntl_bad_file(self):
        with self.assertRaises(ValueError):
            fcntl.fcntl(-1, fcntl.F_SETFL, os.O_NONBLOCK)
        with self.assertRaises(ValueError):
            fcntl.fcntl(BadFile(-1), fcntl.F_SETFL, os.O_NONBLOCK)
        with self.assertRaises(TypeError):
            fcntl.fcntl('spam', fcntl.F_SETFL, os.O_NONBLOCK)
        with self.assertRaises(TypeError):
            fcntl.fcntl(BadFile('spam'), fcntl.F_SETFL, os.O_NONBLOCK)

    @cpython_only
    def test_fcntl_bad_file_overflow(self):
        from _testcapi import INT_MAX, INT_MIN
        with self.assertRaises(OverflowError):
            fcntl.fcntl(INT_MAX + 1, fcntl.F_SETFL, os.O_NONBLOCK)
        with self.assertRaises(OverflowError):
            fcntl.fcntl(BadFile(INT_MAX + 1), fcntl.F_SETFL, os.O_NONBLOCK)
        with self.assertRaises(OverflowError):
            fcntl.fcntl(INT_MIN - 1, fcntl.F_SETFL, os.O_NONBLOCK)
        with self.assertRaises(OverflowError):
            fcntl.fcntl(BadFile(INT_MIN - 1), fcntl.F_SETFL, os.O_NONBLOCK)

    @unittest.skipIf(platform.machine().startswith('arm') and platform.
        system() == 'Linux',
        'ARM Linux returns EINVAL for F_NOTIFY DN_MULTISHOT')
    def test_fcntl_64_bit(self):
        try:
            cmd = fcntl.F_NOTIFY
            flags = fcntl.DN_MULTISHOT
        except AttributeError:
            self.skipTest('F_NOTIFY or DN_MULTISHOT unavailable')
        fd = os.open(os.path.dirname(os.path.abspath(TESTFN)), os.O_RDONLY)
        try:
            fcntl.fcntl(fd, cmd, flags)
        finally:
            os.close(fd)

    def test_flock(self):
        self.f = open(TESTFN, 'wb+')
        fileno = self.f.fileno()
        fcntl.flock(fileno, fcntl.LOCK_SH)
        fcntl.flock(fileno, fcntl.LOCK_UN)
        fcntl.flock(self.f, fcntl.LOCK_SH | fcntl.LOCK_NB)
        fcntl.flock(self.f, fcntl.LOCK_UN)
        fcntl.flock(fileno, fcntl.LOCK_EX)
        fcntl.flock(fileno, fcntl.LOCK_UN)
        self.assertRaises(ValueError, fcntl.flock, -1, fcntl.LOCK_SH)
        self.assertRaises(TypeError, fcntl.flock, 'spam', fcntl.LOCK_SH)

    @cpython_only
    def test_flock_overflow(self):
        import _testcapi
        self.assertRaises(OverflowError, fcntl.flock, _testcapi.INT_MAX + 1,
            fcntl.LOCK_SH)


def test_main():
    run_unittest(TestFcntl)


if __name__ == '__main__':
    test_main()
