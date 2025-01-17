import os
import unittest


def load_tests(loader, standard_tests, pattern):
    this_dir = os.path.dirname(__file__)
    pattern = pattern or 'test*.py'
    top_level_dir = os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))
    package_tests = loader.discover(start_dir=this_dir, pattern=pattern,
        top_level_dir=top_level_dir)
    standard_tests.addTests(package_tests)
    return standard_tests


if __name__ == '__main__':
    unittest.main()
