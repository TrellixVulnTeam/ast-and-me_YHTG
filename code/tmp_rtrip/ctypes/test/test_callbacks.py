import functools
import unittest
from ctypes import *
from ctypes.test import need_symbol
import _ctypes_test


class Callbacks(unittest.TestCase):
    functype = CFUNCTYPE

    def callback(self, *args):
        self.got_args = args
        return args[-1]

    def check_type(self, typ, arg):
        PROTO = self.functype.__func__(typ, typ)
        result = PROTO(self.callback)(arg)
        if typ == c_float:
            self.assertAlmostEqual(result, arg, places=5)
        else:
            self.assertEqual(self.got_args, (arg,))
            self.assertEqual(result, arg)
        PROTO = self.functype.__func__(typ, c_byte, typ)
        result = PROTO(self.callback)(-3, arg)
        if typ == c_float:
            self.assertAlmostEqual(result, arg, places=5)
        else:
            self.assertEqual(self.got_args, (-3, arg))
            self.assertEqual(result, arg)

    def test_byte(self):
        self.check_type(c_byte, 42)
        self.check_type(c_byte, -42)

    def test_ubyte(self):
        self.check_type(c_ubyte, 42)

    def test_short(self):
        self.check_type(c_short, 42)
        self.check_type(c_short, -42)

    def test_ushort(self):
        self.check_type(c_ushort, 42)

    def test_int(self):
        self.check_type(c_int, 42)
        self.check_type(c_int, -42)

    def test_uint(self):
        self.check_type(c_uint, 42)

    def test_long(self):
        self.check_type(c_long, 42)
        self.check_type(c_long, -42)

    def test_ulong(self):
        self.check_type(c_ulong, 42)

    def test_longlong(self):
        self.check_type(c_longlong, 42)
        self.check_type(c_longlong, -42)

    def test_ulonglong(self):
        self.check_type(c_ulonglong, 42)

    def test_float(self):
        import math
        self.check_type(c_float, math.e)
        self.check_type(c_float, -math.e)

    def test_double(self):
        self.check_type(c_double, 3.14)
        self.check_type(c_double, -3.14)

    def test_longdouble(self):
        self.check_type(c_longdouble, 3.14)
        self.check_type(c_longdouble, -3.14)

    def test_char(self):
        self.check_type(c_char, b'x')
        self.check_type(c_char, b'a')

    @unittest.skip('test disabled')
    def test_char_p(self):
        self.check_type(c_char_p, 'abc')
        self.check_type(c_char_p, 'def')

    def test_pyobject(self):
        o = ()
        from sys import getrefcount as grc
        for o in ((), [], object()):
            initial = grc(o)
            self.check_type(py_object, o)
            before = grc(o)
            self.check_type(py_object, o)
            after = grc(o)
            self.assertEqual((after, o), (before, o))

    def test_unsupported_restype_1(self):
        prototype = self.functype.__func__(POINTER(c_double))
        self.assertRaises(TypeError, prototype, lambda : None)

    def test_unsupported_restype_2(self):
        prototype = self.functype.__func__(object)
        self.assertRaises(TypeError, prototype, lambda : None)

    def test_issue_7959(self):
        proto = self.functype.__func__(None)


        class X(object):

            def func(self):
                pass

            def __init__(self):
                self.v = proto(self.func)
        import gc
        for i in range(32):
            X()
        gc.collect()
        live = [x for x in gc.get_objects() if isinstance(x, X)]
        self.assertEqual(len(live), 0)

    def test_issue12483(self):
        import gc


        class Nasty:

            def __del__(self):
                gc.collect()
        CFUNCTYPE(None)(lambda x=Nasty(): None)


@need_symbol('WINFUNCTYPE')
class StdcallCallbacks(Callbacks):
    try:
        functype = WINFUNCTYPE
    except NameError:
        pass


class SampleCallbacksTestCase(unittest.TestCase):

    def test_integrate(self):
        dll = CDLL(_ctypes_test.__file__)
        CALLBACK = CFUNCTYPE(c_double, c_double)
        integrate = dll.integrate
        integrate.argtypes = c_double, c_double, CALLBACK, c_long
        integrate.restype = c_double

        def func(x):
            return x ** 2
        result = integrate(0.0, 1.0, CALLBACK(func), 10)
        diff = abs(result - 1.0 / 3.0)
        self.assertLess(diff, 0.01, '%s not less than 0.01' % diff)

    def test_issue_8959_a(self):
        from ctypes.util import find_library
        libc_path = find_library('c')
        if not libc_path:
            self.skipTest('could not find libc')
        libc = CDLL(libc_path)

        @CFUNCTYPE(c_int, POINTER(c_int), POINTER(c_int))
        def cmp_func(a, b):
            return a[0] - b[0]
        array = (c_int * 5)(5, 1, 99, 7, 33)
        libc.qsort(array, len(array), sizeof(c_int), cmp_func)
        self.assertEqual(array[:], [1, 5, 7, 33, 99])

    @need_symbol('WINFUNCTYPE')
    def test_issue_8959_b(self):
        from ctypes.wintypes import BOOL, HWND, LPARAM
        global windowCount
        windowCount = 0

        @WINFUNCTYPE(BOOL, HWND, LPARAM)
        def EnumWindowsCallbackFunc(hwnd, lParam):
            global windowCount
            windowCount += 1
            return True
        windll.user32.EnumWindows(EnumWindowsCallbackFunc, 0)

    def test_callback_register_int(self):
        dll = CDLL(_ctypes_test.__file__)
        CALLBACK = CFUNCTYPE(c_int, c_int, c_int, c_int, c_int, c_int)
        func = dll._testfunc_cbk_reg_int
        func.argtypes = c_int, c_int, c_int, c_int, c_int, CALLBACK
        func.restype = c_int

        def callback(a, b, c, d, e):
            return a + b + c + d + e
        result = func(2, 3, 4, 5, 6, CALLBACK(callback))
        self.assertEqual(result, callback(2 * 2, 3 * 3, 4 * 4, 5 * 5, 6 * 6))

    def test_callback_register_double(self):
        dll = CDLL(_ctypes_test.__file__)
        CALLBACK = CFUNCTYPE(c_double, c_double, c_double, c_double,
            c_double, c_double)
        func = dll._testfunc_cbk_reg_double
        func.argtypes = (c_double, c_double, c_double, c_double, c_double,
            CALLBACK)
        func.restype = c_double

        def callback(a, b, c, d, e):
            return a + b + c + d + e
        result = func(1.1, 2.2, 3.3, 4.4, 5.5, CALLBACK(callback))
        self.assertEqual(result, callback(1.1 * 1.1, 2.2 * 2.2, 3.3 * 3.3, 
            4.4 * 4.4, 5.5 * 5.5))

    def test_callback_large_struct(self):


        class Check:
            pass


        class X(Structure):
            _fields_ = [('first', c_ulong), ('second', c_ulong), ('third',
                c_ulong)]

        def callback(check, s):
            check.first = s.first
            check.second = s.second
            check.third = s.third
            s.first = s.second = s.third = 195948557
        check = Check()
        s = X()
        s.first = 3735928559
        s.second = 3405691582
        s.third = 195894762
        CALLBACK = CFUNCTYPE(None, X)
        dll = CDLL(_ctypes_test.__file__)
        func = dll._testfunc_cbk_large_struct
        func.argtypes = X, CALLBACK
        func.restype = None
        func(s, CALLBACK(functools.partial(callback, check)))
        self.assertEqual(check.first, s.first)
        self.assertEqual(check.second, s.second)
        self.assertEqual(check.third, s.third)
        self.assertEqual(check.first, 3735928559)
        self.assertEqual(check.second, 3405691582)
        self.assertEqual(check.third, 195894762)
        self.assertEqual(s.first, check.first)
        self.assertEqual(s.second, check.second)
        self.assertEqual(s.third, check.third)


if __name__ == '__main__':
    unittest.main()
