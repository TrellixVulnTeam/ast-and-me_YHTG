import os
import sys
import unittest
import test.support as test_support
from tkinter import Tcl, TclError
test_support.requires('gui')


class TkLoadTest(unittest.TestCase):

    @unittest.skipIf('DISPLAY' not in os.environ, 'No $DISPLAY set.')
    def testLoadTk(self):
        tcl = Tcl()
        self.assertRaises(TclError, tcl.winfo_geometry)
        tcl.loadtk()
        self.assertEqual('1x1+0+0', tcl.winfo_geometry())
        tcl.destroy()

    def testLoadTkFailure(self):
        old_display = None
        if sys.platform.startswith(('win', 'darwin', 'cygwin')):
            return
        with test_support.EnvironmentVarGuard() as env:
            if 'DISPLAY' in os.environ:
                del env['DISPLAY']
                with os.popen('echo $DISPLAY') as pipe:
                    display = pipe.read().strip()
                if display:
                    return
            tcl = Tcl()
            self.assertRaises(TclError, tcl.winfo_geometry)
            self.assertRaises(TclError, tcl.loadtk)


tests_gui = TkLoadTest,
if __name__ == '__main__':
    test_support.run_unittest(*tests_gui)
