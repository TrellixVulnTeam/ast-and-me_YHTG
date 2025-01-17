from .. import util
from importlib import machinery
import sys
import types
import unittest
PKG_NAME = 'fine'
SUBMOD_NAME = 'fine.bogus'


class BadSpecFinderLoader:

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname == SUBMOD_NAME:
            spec = machinery.ModuleSpec(fullname, cls)
            return spec

    @staticmethod
    def create_module(spec):
        return None

    @staticmethod
    def exec_module(module):
        if module.__name__ == SUBMOD_NAME:
            raise ImportError('I cannot be loaded!')


class BadLoaderFinder:

    @classmethod
    def find_module(cls, fullname, path):
        if fullname == SUBMOD_NAME:
            return cls

    @classmethod
    def load_module(cls, fullname):
        if fullname == SUBMOD_NAME:
            raise ImportError('I cannot be loaded!')


class APITest:
    """Test API-specific details for __import__ (e.g. raising the right
    exception when passing in an int for the module name)."""

    def test_raises_ModuleNotFoundError(self):
        with self.assertRaises(ModuleNotFoundError):
            util.import_importlib('some module that does not exist')

    def test_name_requires_rparition(self):
        with self.assertRaises(TypeError):
            self.__import__(42)

    def test_negative_level(self):
        with self.assertRaises(ValueError):
            self.__import__('os', globals(), level=-1)

    def test_nonexistent_fromlist_entry(self):
        mod = types.ModuleType(PKG_NAME)
        mod.__path__ = ['XXX']
        with util.import_state(meta_path=[self.bad_finder_loader]):
            with util.uncache(PKG_NAME):
                sys.modules[PKG_NAME] = mod
                self.__import__(PKG_NAME, fromlist=['not here'])

    def test_fromlist_load_error_propagates(self):
        mod = types.ModuleType(PKG_NAME)
        mod.__path__ = ['XXX']
        with util.import_state(meta_path=[self.bad_finder_loader]):
            with util.uncache(PKG_NAME):
                sys.modules[PKG_NAME] = mod
                with self.assertRaises(ImportError):
                    self.__import__(PKG_NAME, fromlist=[SUBMOD_NAME.
                        rpartition('.')[-1]])


class OldAPITests(APITest):
    bad_finder_loader = BadLoaderFinder


Frozen_OldAPITests, Source_OldAPITests = util.test_both(OldAPITests,
    __import__=util.__import__)


class SpecAPITests(APITest):
    bad_finder_loader = BadSpecFinderLoader


Frozen_SpecAPITests, Source_SpecAPITests = util.test_both(SpecAPITests,
    __import__=util.__import__)
if __name__ == '__main__':
    unittest.main()
