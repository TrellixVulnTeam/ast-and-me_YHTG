import os
import sys
import builtins
import contextlib
import importlib.util
import inspect
import pydoc
import py_compile
import keyword
import _pickle
import pkgutil
import re
import stat
import string
import test.support
import time
import types
import typing
import unittest
import urllib.parse
import xml.etree
import xml.etree.ElementTree
import textwrap
from io import StringIO
from collections import namedtuple
from test.support.script_helper import assert_python_ok
from test.support import TESTFN, rmtree, reap_children, reap_threads, captured_output, captured_stdout, captured_stderr, unlink, requires_docstrings
from test import pydoc_mod
try:
    import threading
except ImportError:
    threading = None


class nonascii:
    """Це не латиниця"""
    pass


if test.support.HAVE_DOCSTRINGS:
    expected_data_docstrings = (
        'dictionary for instance variables (if defined)',
        'list of weak references to the object (if defined)') * 2
else:
    expected_data_docstrings = '', '', '', ''
expected_text_pattern = (
    """
NAME
    test.pydoc_mod - This is a test module for test_pydoc
%s
CLASSES
    builtins.object
        A
        B
        C
    
    class A(builtins.object)
     |  Hello and goodbye
     |  
     |  Methods defined here:
     |  
     |  __init__()
     |      Wow, I have no function!
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__%s
     |  
     |  __weakref__%s
    
    class B(builtins.object)
     |  Data descriptors defined here:
     |  
     |  __dict__%s
     |  
     |  __weakref__%s
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  NO_MEANING = 'eggs'
     |  
     |  __annotations__ = {'NO_MEANING': <class 'str'>}
    
    class C(builtins.object)
     |  Methods defined here:
     |  
     |  get_answer(self)
     |      Return say_no()
     |  
     |  is_it_true(self)
     |      Return self.get_answer()
     |  
     |  say_no(self)
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

FUNCTIONS
    doc_func()
        This function solves all of the world's problems:
        hunger
        lack of Python
        war
    
    nodoc_func()

DATA
    __xyz__ = 'X, Y and Z'

VERSION
    1.2.3.4

AUTHOR
    Benjamin Peterson

CREDITS
    Nobody

FILE
    %s
"""
    .strip())
expected_text_data_docstrings = tuple('\n     |      ' + s if s else '' for
    s in expected_data_docstrings)
expected_html_pattern = (
    """
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="heading">
<tr bgcolor="#7799ee">
<td valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial">&nbsp;<br><big><big><strong><a href="test.html"><font color="#ffffff">test</font></a>.pydoc_mod</strong></big></big> (version 1.2.3.4)</font></td
><td align=right valign=bottom
><font color="#ffffff" face="helvetica, arial"><a href=".">index</a><br><a href="file:%s">%s</a>%s</font></td></tr></table>
    <p><tt>This&nbsp;is&nbsp;a&nbsp;test&nbsp;module&nbsp;for&nbsp;test_pydoc</tt></p>
<p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#ee77aa">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial"><big><strong>Classes</strong></big></font></td></tr>
    
<tr><td bgcolor="#ee77aa"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%"><dl>
<dt><font face="helvetica, arial"><a href="builtins.html#object">builtins.object</a>
</font></dt><dd>
<dl>
<dt><font face="helvetica, arial"><a href="test.pydoc_mod.html#A">A</a>
</font></dt><dt><font face="helvetica, arial"><a href="test.pydoc_mod.html#B">B</a>
</font></dt><dt><font face="helvetica, arial"><a href="test.pydoc_mod.html#C">C</a>
</font></dt></dl>
</dd>
</dl>
 <p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#ffc8d8">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#000000" face="helvetica, arial"><a name="A">class <strong>A</strong></a>(<a href="builtins.html#object">builtins.object</a>)</font></td></tr>
    
<tr bgcolor="#ffc8d8"><td rowspan=2><tt>&nbsp;&nbsp;&nbsp;</tt></td>
<td colspan=2><tt>Hello&nbsp;and&nbsp;goodbye<br>&nbsp;</tt></td></tr>
<tr><td>&nbsp;</td>
<td width="100%%">Methods defined here:<br>
<dl><dt><a name="A-__init__"><strong>__init__</strong></a>()</dt><dd><tt>Wow,&nbsp;I&nbsp;have&nbsp;no&nbsp;function!</tt></dd></dl>

<hr>
Data descriptors defined here:<br>
<dl><dt><strong>__dict__</strong></dt>
<dd><tt>%s</tt></dd>
</dl>
<dl><dt><strong>__weakref__</strong></dt>
<dd><tt>%s</tt></dd>
</dl>
</td></tr></table> <p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#ffc8d8">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#000000" face="helvetica, arial"><a name="B">class <strong>B</strong></a>(<a href="builtins.html#object">builtins.object</a>)</font></td></tr>
    
<tr><td bgcolor="#ffc8d8"><tt>&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%">Data descriptors defined here:<br>
<dl><dt><strong>__dict__</strong></dt>
<dd><tt>%s</tt></dd>
</dl>
<dl><dt><strong>__weakref__</strong></dt>
<dd><tt>%s</tt></dd>
</dl>
<hr>
Data and other attributes defined here:<br>
<dl><dt><strong>NO_MEANING</strong> = 'eggs'</dl>

<dl><dt><strong>__annotations__</strong> = {'NO_MEANING': &lt;class 'str'&gt;}</dl>

</td></tr></table> <p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#ffc8d8">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#000000" face="helvetica, arial"><a name="C">class <strong>C</strong></a>(<a href="builtins.html#object">builtins.object</a>)</font></td></tr>
    
<tr><td bgcolor="#ffc8d8"><tt>&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%">Methods defined here:<br>
<dl><dt><a name="C-get_answer"><strong>get_answer</strong></a>(self)</dt><dd><tt>Return&nbsp;<a href="#C-say_no">say_no</a>()</tt></dd></dl>

<dl><dt><a name="C-is_it_true"><strong>is_it_true</strong></a>(self)</dt><dd><tt>Return&nbsp;self.<a href="#C-get_answer">get_answer</a>()</tt></dd></dl>

<dl><dt><a name="C-say_no"><strong>say_no</strong></a>(self)</dt></dl>

<hr>
Data descriptors defined here:<br>
<dl><dt><strong>__dict__</strong></dt>
<dd><tt>dictionary&nbsp;for&nbsp;instance&nbsp;variables&nbsp;(if&nbsp;defined)</tt></dd>
</dl>
<dl><dt><strong>__weakref__</strong></dt>
<dd><tt>list&nbsp;of&nbsp;weak&nbsp;references&nbsp;to&nbsp;the&nbsp;object&nbsp;(if&nbsp;defined)</tt></dd>
</dl>
</td></tr></table></td></tr></table><p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#eeaa77">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial"><big><strong>Functions</strong></big></font></td></tr>
    
<tr><td bgcolor="#eeaa77"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%"><dl><dt><a name="-doc_func"><strong>doc_func</strong></a>()</dt><dd><tt>This&nbsp;function&nbsp;solves&nbsp;all&nbsp;of&nbsp;the&nbsp;world's&nbsp;problems:<br>
hunger<br>
lack&nbsp;of&nbsp;Python<br>
war</tt></dd></dl>
 <dl><dt><a name="-nodoc_func"><strong>nodoc_func</strong></a>()</dt></dl>
</td></tr></table><p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#55aa55">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial"><big><strong>Data</strong></big></font></td></tr>
    
<tr><td bgcolor="#55aa55"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%"><strong>__xyz__</strong> = 'X, Y and Z'</td></tr></table><p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#7799ee">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial"><big><strong>Author</strong></big></font></td></tr>
    
<tr><td bgcolor="#7799ee"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%">Benjamin&nbsp;Peterson</td></tr></table><p>
<table width="100%%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#7799ee">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial"><big><strong>Credits</strong></big></font></td></tr>
    
<tr><td bgcolor="#7799ee"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%%">Nobody</td></tr></table>
"""
    .strip())
expected_html_data_docstrings = tuple(s.replace(' ', '&nbsp;') for s in
    expected_data_docstrings)
missing_pattern = (
    """No Python documentation found for %r.
Use help() to get the interactive help utility.
Use help(str) for help on the str class."""
    .replace('\n', os.linesep))
badimport_pattern = 'problem in %s - ModuleNotFoundError: No module named %r'
expected_dynamicattribute_pattern = (
    """
Help on class DA in module %s:

class DA(builtins.object)
 |  Data descriptors defined here:
 |  
 |  __dict__%s
 |  
 |  __weakref__%s
 |  
 |  ham
 |  
 |  ----------------------------------------------------------------------
 |  Data and other attributes inherited from Meta:
 |  
 |  ham = 'spam'
"""
    .strip())
expected_virtualattribute_pattern1 = (
    """
Help on class Class in module %s:

class Class(builtins.object)
 |  Data and other attributes inherited from Meta:
 |  
 |  LIFE = 42
"""
    .strip())
expected_virtualattribute_pattern2 = (
    """
Help on class Class1 in module %s:

class Class1(builtins.object)
 |  Data and other attributes inherited from Meta1:
 |  
 |  one = 1
"""
    .strip())
expected_virtualattribute_pattern3 = (
    """
Help on class Class2 in module %s:

class Class2(Class1)
 |  Method resolution order:
 |      Class2
 |      Class1
 |      builtins.object
 |  
 |  Data and other attributes inherited from Meta1:
 |  
 |  one = 1
 |  
 |  ----------------------------------------------------------------------
 |  Data and other attributes inherited from Meta3:
 |  
 |  three = 3
 |  
 |  ----------------------------------------------------------------------
 |  Data and other attributes inherited from Meta2:
 |  
 |  two = 2
"""
    .strip())
expected_missingattribute_pattern = (
    """
Help on class C in module %s:

class C(builtins.object)
 |  Data and other attributes defined here:
 |  
 |  here = 'present!'
"""
    .strip())


def run_pydoc(module_name, *args, **env):
    """
    Runs pydoc on the specified module. Returns the stripped
    output of pydoc.
    """
    args = args + (module_name,)
    rc, out, err = assert_python_ok('-B', pydoc.__file__, *args, **env)
    return out.strip()


def get_pydoc_html(module):
    """Returns pydoc generated output as html"""
    doc = pydoc.HTMLDoc()
    output = doc.docmodule(module)
    loc = doc.getdocloc(pydoc_mod) or ''
    if loc:
        loc = '<br><a href="' + loc + '">Module Docs</a>'
    return output.strip(), loc


def get_pydoc_link(module):
    """Returns a documentation web link of a module"""
    dirname = os.path.dirname
    basedir = dirname(dirname(__file__))
    doc = pydoc.TextDoc()
    loc = doc.getdocloc(module, basedir=basedir)
    return loc


def get_pydoc_text(module):
    """Returns pydoc generated output as text"""
    doc = pydoc.TextDoc()
    loc = doc.getdocloc(pydoc_mod) or ''
    if loc:
        loc = '\nMODULE DOCS\n    ' + loc + '\n'
    output = doc.docmodule(module)
    patt = re.compile('\x08.')
    output = patt.sub('', output)
    return output.strip(), loc


def get_html_title(text):
    header, _, _ = text.partition('</head>')
    _, _, title = header.partition('<title>')
    title, _, _ = title.partition('</title>')
    return title


class PydocBaseTest(unittest.TestCase):

    def _restricted_walk_packages(self, walk_packages, path=None):
        """
        A version of pkgutil.walk_packages() that will restrict itself to
        a given path.
        """
        default_path = path or [os.path.dirname(__file__)]

        def wrapper(path=None, prefix='', onerror=None):
            return walk_packages(path or default_path, prefix, onerror)
        return wrapper

    @contextlib.contextmanager
    def restrict_walk_packages(self, path=None):
        walk_packages = pkgutil.walk_packages
        pkgutil.walk_packages = self._restricted_walk_packages(walk_packages,
            path)
        try:
            yield
        finally:
            pkgutil.walk_packages = walk_packages

    def call_url_handler(self, url, expected_title):
        text = pydoc._url_handler(url, 'text/html')
        result = get_html_title(text)
        self.assertEqual(result, expected_title, text)
        return text


class PydocDocTest(unittest.TestCase):

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_html_doc(self):
        result, doc_loc = get_pydoc_html(pydoc_mod)
        mod_file = inspect.getabsfile(pydoc_mod)
        mod_url = urllib.parse.quote(mod_file)
        expected_html = expected_html_pattern % ((mod_url, mod_file,
            doc_loc) + expected_html_data_docstrings)
        self.assertEqual(result, expected_html)

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_text_doc(self):
        result, doc_loc = get_pydoc_text(pydoc_mod)
        expected_text = expected_text_pattern % ((doc_loc,) +
            expected_text_data_docstrings + (inspect.getabsfile(pydoc_mod),))
        self.assertEqual(expected_text, result)

    def test_text_enum_member_with_value_zero(self):
        import enum


        class BinaryInteger(enum.IntEnum):
            zero = 0
            one = 1
        doc = pydoc.render_doc(BinaryInteger)
        self.assertIn('<BinaryInteger.zero: 0>', doc)

    def test_mixed_case_module_names_are_lower_cased(self):
        doc_link = get_pydoc_link(xml.etree.ElementTree)
        self.assertIn('xml.etree.elementtree', doc_link)

    def test_issue8225(self):
        result, doc_loc = get_pydoc_text(xml.etree)
        self.assertEqual(doc_loc, '', 'MODULE DOCS incorrectly includes a link'
            )

    def test_getpager_with_stdin_none(self):
        previous_stdin = sys.stdin
        try:
            sys.stdin = None
            pydoc.getpager()
        finally:
            sys.stdin = previous_stdin

    def test_non_str_name(self):


        class A:
            __name__ = 42


        class B:
            pass
        adoc = pydoc.render_doc(A())
        bdoc = pydoc.render_doc(B())
        self.assertEqual(adoc.replace('A', 'B'), bdoc)

    def test_not_here(self):
        missing_module = 'test.i_am_not_here'
        result = str(run_pydoc(missing_module), 'ascii')
        expected = missing_pattern % missing_module
        self.assertEqual(expected, result,
            'documentation for missing module found')

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -OO and above')
    def test_not_ascii(self):
        result = run_pydoc('test.test_pydoc.nonascii', PYTHONIOENCODING='ascii'
            )
        encoded = nonascii.__doc__.encode('ascii', 'backslashreplace')
        self.assertIn(encoded, result)

    def test_input_strip(self):
        missing_module = ' test.i_am_not_here '
        result = str(run_pydoc(missing_module), 'ascii')
        expected = missing_pattern % missing_module.strip()
        self.assertEqual(expected, result)

    def test_stripid(self):
        stripid = pydoc.stripid
        self.assertEqual(stripid('<function stripid at 0x88dcee4>'),
            '<function stripid>')
        self.assertEqual(stripid('<function stripid at 0x01F65390>'),
            '<function stripid>')
        self.assertEqual(stripid('42'), '42')
        self.assertEqual(stripid("<type 'exceptions.Exception'>"),
            "<type 'exceptions.Exception'>")

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    @requires_docstrings
    def test_help_output_redirect(self):
        old_pattern = expected_text_pattern
        getpager_old = pydoc.getpager
        getpager_new = lambda : lambda x: x
        self.maxDiff = None
        buf = StringIO()
        helper = pydoc.Helper(output=buf)
        unused, doc_loc = get_pydoc_text(pydoc_mod)
        module = 'test.pydoc_mod'
        help_header = (
            """
        Help on module test.pydoc_mod in test:

        """
            .lstrip())
        help_header = textwrap.dedent(help_header)
        expected_help_pattern = help_header + expected_text_pattern
        pydoc.getpager = getpager_new
        try:
            with captured_output('stdout') as output, captured_output('stderr'
                ) as err:
                helper.help(module)
                result = buf.getvalue().strip()
                expected_text = expected_help_pattern % ((doc_loc,) +
                    expected_text_data_docstrings + (inspect.getabsfile(
                    pydoc_mod),))
                self.assertEqual('', output.getvalue())
                self.assertEqual('', err.getvalue())
                self.assertEqual(expected_text, result)
        finally:
            pydoc.getpager = getpager_old

    def test_namedtuple_public_underscore(self):
        NT = namedtuple('NT', ['abc', 'def'], rename=True)
        with captured_stdout() as help_io:
            pydoc.help(NT)
        helptext = help_io.getvalue()
        self.assertIn('_1', helptext)
        self.assertIn('_replace', helptext)
        self.assertIn('_asdict', helptext)

    def test_synopsis(self):
        self.addCleanup(unlink, TESTFN)
        for encoding in ('ISO-8859-1', 'UTF-8'):
            with open(TESTFN, 'w', encoding=encoding) as script:
                if encoding != 'UTF-8':
                    print('#coding: {}'.format(encoding), file=script)
                print('"""line 1: hé', file=script)
                print('line 2: hi"""', file=script)
            synopsis = pydoc.synopsis(TESTFN, {})
            self.assertEqual(synopsis, 'line 1: hé')

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -OO and above')
    def test_synopsis_sourceless(self):
        expected = os.__doc__.splitlines()[0]
        filename = os.__cached__
        synopsis = pydoc.synopsis(filename)
        self.assertEqual(synopsis, expected)

    def test_synopsis_sourceless_empty_doc(self):
        with test.support.temp_cwd() as test_dir:
            init_path = os.path.join(test_dir, 'foomod42.py')
            cached_path = importlib.util.cache_from_source(init_path)
            with open(init_path, 'w') as fobj:
                fobj.write('foo = 1')
            py_compile.compile(init_path)
            synopsis = pydoc.synopsis(init_path, {})
            self.assertIsNone(synopsis)
            synopsis_cached = pydoc.synopsis(cached_path, {})
            self.assertIsNone(synopsis_cached)

    def test_splitdoc_with_description(self):
        example_string = 'I Am A Doc\n\n\nHere is my description'
        self.assertEqual(pydoc.splitdoc(example_string), ('I Am A Doc',
            '\nHere is my description'))

    def test_is_object_or_method(self):
        doc = pydoc.Doc()
        self.assertTrue(pydoc._is_some_method(doc.fail))
        self.assertTrue(pydoc._is_some_method(int.__add__))
        self.assertFalse(pydoc._is_some_method('I am not a method'))

    def test_is_package_when_not_package(self):
        with test.support.temp_cwd() as test_dir:
            self.assertFalse(pydoc.ispackage(test_dir))

    def test_is_package_when_is_package(self):
        with test.support.temp_cwd() as test_dir:
            init_path = os.path.join(test_dir, '__init__.py')
            open(init_path, 'w').close()
            self.assertTrue(pydoc.ispackage(test_dir))
            os.remove(init_path)

    def test_allmethods(self):


        class TestClass(object):

            def method_returning_true(self):
                return True
        expected = dict(vars(object))
        expected['method_returning_true'] = TestClass.method_returning_true
        del expected['__doc__']
        del expected['__class__']
        expected['__subclasshook__'] = TestClass.__subclasshook__
        expected['__init_subclass__'] = TestClass.__init_subclass__
        methods = pydoc.allmethods(TestClass)
        self.assertDictEqual(methods, expected)


class PydocImportTest(PydocBaseTest):

    def setUp(self):
        self.test_dir = os.mkdir(TESTFN)
        self.addCleanup(rmtree, TESTFN)
        importlib.invalidate_caches()

    def test_badimport(self):
        modname = 'testmod_xyzzy'
        testpairs = ('i_am_not_here', 'i_am_not_here'), (
            'test.i_am_not_here_either', 'test.i_am_not_here_either'), (
            'test.i_am_not_here.neither_am_i', 'test.i_am_not_here'), (
            'i_am_not_here.{}'.format(modname), 'i_am_not_here'), ('test.{}'
            .format(modname), 'test.{}'.format(modname))
        sourcefn = os.path.join(TESTFN, modname) + os.extsep + 'py'
        for importstring, expectedinmsg in testpairs:
            with open(sourcefn, 'w') as f:
                f.write('import {}\n'.format(importstring))
            result = run_pydoc(modname, PYTHONPATH=TESTFN).decode('ascii')
            expected = badimport_pattern % (modname, expectedinmsg)
            self.assertEqual(expected, result)

    def test_apropos_with_bad_package(self):
        pkgdir = os.path.join(TESTFN, 'syntaxerr')
        os.mkdir(pkgdir)
        badsyntax = os.path.join(pkgdir, '__init__') + os.extsep + 'py'
        with open(badsyntax, 'w') as f:
            f.write('invalid python syntax = $1\n')
        with self.restrict_walk_packages(path=[TESTFN]):
            with captured_stdout() as out:
                with captured_stderr() as err:
                    pydoc.apropos('xyzzy')
            self.assertEqual(out.getvalue(), '')
            self.assertEqual(err.getvalue(), '')
            with captured_stdout() as out:
                with captured_stderr() as err:
                    pydoc.apropos('syntaxerr')
            self.assertEqual(out.getvalue().strip(), 'syntaxerr')
            self.assertEqual(err.getvalue(), '')

    def test_apropos_with_unreadable_dir(self):
        self.unreadable_dir = os.path.join(TESTFN, 'unreadable')
        os.mkdir(self.unreadable_dir, 0)
        self.addCleanup(os.rmdir, self.unreadable_dir)
        with self.restrict_walk_packages(path=[TESTFN]):
            with captured_stdout() as out:
                with captured_stderr() as err:
                    pydoc.apropos('SOMEKEY')
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), '')

    def test_apropos_empty_doc(self):
        pkgdir = os.path.join(TESTFN, 'walkpkg')
        os.mkdir(pkgdir)
        self.addCleanup(rmtree, pkgdir)
        init_path = os.path.join(pkgdir, '__init__.py')
        with open(init_path, 'w') as fobj:
            fobj.write('foo = 1')
        current_mode = stat.S_IMODE(os.stat(pkgdir).st_mode)
        try:
            os.chmod(pkgdir, current_mode & ~stat.S_IEXEC)
            with self.restrict_walk_packages(path=[TESTFN]), captured_stdout(
                ) as stdout:
                pydoc.apropos('')
            self.assertIn('walkpkg', stdout.getvalue())
        finally:
            os.chmod(pkgdir, current_mode)

    def test_url_search_package_error(self):
        pkgdir = os.path.join(TESTFN, 'test_error_package')
        os.mkdir(pkgdir)
        init = os.path.join(pkgdir, '__init__.py')
        with open(init, 'wt', encoding='ascii') as f:
            f.write('raise ValueError("ouch")\n')
        with self.restrict_walk_packages(path=[TESTFN]):
            saved_paths = tuple(sys.path)
            sys.path.insert(0, TESTFN)
            try:
                with self.assertRaisesRegex(ValueError, 'ouch'):
                    import test_error_package
                text = self.call_url_handler('search?key=test_error_package',
                    'Pydoc: Search Results')
                found = (
                    '<a href="test_error_package.html">test_error_package</a>')
                self.assertIn(found, text)
            finally:
                sys.path[:] = saved_paths

    @unittest.skip('causes undesirable side-effects (#20128)')
    def test_modules(self):
        num_header_lines = 2
        num_module_lines_min = 5
        num_footer_lines = 3
        expected = num_header_lines + num_module_lines_min + num_footer_lines
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper('modules')
        result = output.getvalue().strip()
        num_lines = len(result.splitlines())
        self.assertGreaterEqual(num_lines, expected)

    @unittest.skip('causes undesirable side-effects (#20128)')
    def test_modules_search(self):
        expected = 'pydoc - '
        output = StringIO()
        helper = pydoc.Helper(output=output)
        with captured_stdout() as help_io:
            helper('modules pydoc')
        result = help_io.getvalue()
        self.assertIn(expected, result)

    @unittest.skip('some buildbots are not cooperating (#20128)')
    def test_modules_search_builtin(self):
        expected = 'gc - '
        output = StringIO()
        helper = pydoc.Helper(output=output)
        with captured_stdout() as help_io:
            helper('modules garbage')
        result = help_io.getvalue()
        self.assertTrue(result.startswith(expected))

    def test_importfile(self):
        loaded_pydoc = pydoc.importfile(pydoc.__file__)
        self.assertIsNot(loaded_pydoc, pydoc)
        self.assertEqual(loaded_pydoc.__name__, 'pydoc')
        self.assertEqual(loaded_pydoc.__file__, pydoc.__file__)
        self.assertEqual(loaded_pydoc.__spec__, pydoc.__spec__)


class TestDescriptions(unittest.TestCase):

    def test_module(self):
        from test import pydocfodder
        doc = pydoc.render_doc(pydocfodder)
        self.assertIn('pydocfodder', doc)

    def test_class(self):


        class C:
            """New-style class"""
        c = C()
        self.assertEqual(pydoc.describe(C), 'class C')
        self.assertEqual(pydoc.describe(c), 'C')
        expected = 'C in module %s object' % __name__
        self.assertIn(expected, pydoc.render_doc(c))

    def test_typing_pydoc(self):

        def foo(data: typing.List[typing.Any], x: int) ->typing.Iterator[
            typing.Tuple[int, typing.Any]]:
            ...
        T = typing.TypeVar('T')


        class C(typing.Generic[T], typing.Mapping[int, str]):
            ...
        self.assertEqual(pydoc.render_doc(foo).splitlines()[-1],
            'f\x08fo\x08oo\x08o(data:List[Any], x:int) -> Iterator[Tuple[int, Any]]'
            )
        self.assertEqual(pydoc.render_doc(C).splitlines()[2],
            'class C\x08C(typing.Mapping)')

    def test_builtin(self):
        for name in ('str', 'str.translate', 'builtins.str',
            'builtins.str.translate'):
            self.assertIsNotNone(pydoc.locate(name))
            try:
                pydoc.render_doc(name)
            except ImportError:
                self.fail('finding the doc of {!r} failed'.format(name))
        for name in ('notbuiltins', 'strrr', 'strr.translate',
            'str.trrrranslate', 'builtins.strrr', 'builtins.str.trrranslate'):
            self.assertIsNone(pydoc.locate(name))
            self.assertRaises(ImportError, pydoc.render_doc, name)

    @staticmethod
    def _get_summary_line(o):
        text = pydoc.plain(pydoc.render_doc(o))
        lines = text.split('\n')
        assert len(lines) >= 2
        return lines[2]

    def test_unbound_python_method(self):
        self.assertEqual(self._get_summary_line(textwrap.TextWrapper.wrap),
            'wrap(self, text)')

    @requires_docstrings
    def test_unbound_builtin_method(self):
        self.assertEqual(self._get_summary_line(_pickle.Pickler.dump),
            'dump(self, obj, /)')

    def test_bound_python_method(self):
        t = textwrap.TextWrapper()
        self.assertEqual(self._get_summary_line(t.wrap),
            'wrap(text) method of textwrap.TextWrapper instance')

    def test_field_order_for_named_tuples(self):
        Person = namedtuple('Person', ['nickname', 'firstname', 'agegroup'])
        s = pydoc.render_doc(Person)
        self.assertLess(s.index('nickname'), s.index('firstname'))
        self.assertLess(s.index('firstname'), s.index('agegroup'))


        class NonIterableFields:
            _fields = None


        class NonHashableFields:
            _fields = [[]]
        pydoc.render_doc(NonIterableFields)
        pydoc.render_doc(NonHashableFields)

    @requires_docstrings
    def test_bound_builtin_method(self):
        s = StringIO()
        p = _pickle.Pickler(s)
        self.assertEqual(self._get_summary_line(p.dump),
            'dump(obj, /) method of _pickle.Pickler instance')

    @requires_docstrings
    def test_module_level_callable(self):
        self.assertEqual(self._get_summary_line(os.stat),
            'stat(path, *, dir_fd=None, follow_symlinks=True)')


@unittest.skipUnless(threading, 'Threading required for this test.')
class PydocServerTest(unittest.TestCase):
    """Tests for pydoc._start_server"""

    def test_server(self):

        def my_url_handler(url, content_type):
            text = 'the URL sent was: (%s, %s)' % (url, content_type)
            return text
        serverthread = pydoc._start_server(my_url_handler, port=0)
        self.assertIn('localhost', serverthread.docserver.address)
        starttime = time.time()
        timeout = 1
        while serverthread.serving:
            time.sleep(0.01)
            if serverthread.serving and time.time() - starttime > timeout:
                serverthread.stop()
                break
        self.assertEqual(serverthread.error, None)


class PydocUrlHandlerTest(PydocBaseTest):
    """Tests for pydoc._url_handler"""

    def test_content_type_err(self):
        f = pydoc._url_handler
        self.assertRaises(TypeError, f, 'A', '')
        self.assertRaises(TypeError, f, 'B', 'foobar')

    def test_url_requests(self):
        requests = [('', 'Pydoc: Index of Modules'), ('get?key=',
            'Pydoc: Index of Modules'), ('index', 'Pydoc: Index of Modules'
            ), ('topics', 'Pydoc: Topics'), ('keywords', 'Pydoc: Keywords'),
            ('pydoc', 'Pydoc: module pydoc'), ('get?key=pydoc',
            'Pydoc: module pydoc'), ('search?key=pydoc',
            'Pydoc: Search Results'), ('topic?key=def',
            'Pydoc: KEYWORD def'), ('topic?key=STRINGS',
            'Pydoc: TOPIC STRINGS'), ('foobar', 'Pydoc: Error - foobar'), (
            'getfile?key=foobar', 'Pydoc: Error - getfile?key=foobar')]
        with self.restrict_walk_packages():
            for url, title in requests:
                self.call_url_handler(url, title)
            path = string.__file__
            title = 'Pydoc: getfile ' + path
            url = 'getfile?key=' + path
            self.call_url_handler(url, title)


class TestHelper(unittest.TestCase):

    def test_keywords(self):
        self.assertEqual(sorted(pydoc.Helper.keywords), sorted(keyword.kwlist))


class PydocWithMetaClasses(unittest.TestCase):

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    def test_DynamicClassAttribute(self):


        class Meta(type):

            def __getattr__(self, name):
                if name == 'ham':
                    return 'spam'
                return super().__getattr__(name)


        class DA(metaclass=Meta):

            @types.DynamicClassAttribute
            def ham(self):
                return 'eggs'
        expected_text_data_docstrings = tuple('\n |      ' + s if s else '' for
            s in expected_data_docstrings)
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(DA)
        expected_text = expected_dynamicattribute_pattern % ((__name__,) +
            expected_text_data_docstrings[:2])
        result = output.getvalue().strip()
        self.assertEqual(expected_text, result)

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    def test_virtualClassAttributeWithOneMeta(self):


        class Meta(type):

            def __dir__(cls):
                return ['__class__', '__module__', '__name__', 'LIFE']

            def __getattr__(self, name):
                if name == 'LIFE':
                    return 42
                return super().__getattr(name)


        class Class(metaclass=Meta):
            pass
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(Class)
        expected_text = expected_virtualattribute_pattern1 % __name__
        result = output.getvalue().strip()
        self.assertEqual(expected_text, result)

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    def test_virtualClassAttributeWithTwoMeta(self):


        class Meta1(type):

            def __dir__(cls):
                return ['__class__', '__module__', '__name__', 'one']

            def __getattr__(self, name):
                if name == 'one':
                    return 1
                return super().__getattr__(name)


        class Meta2(type):

            def __dir__(cls):
                return ['__class__', '__module__', '__name__', 'two']

            def __getattr__(self, name):
                if name == 'two':
                    return 2
                return super().__getattr__(name)


        class Meta3(Meta1, Meta2):

            def __dir__(cls):
                return list(sorted(set(['__class__', '__module__',
                    '__name__', 'three'] + Meta1.__dir__(cls) + Meta2.
                    __dir__(cls))))

            def __getattr__(self, name):
                if name == 'three':
                    return 3
                return super().__getattr__(name)


        class Class1(metaclass=Meta1):
            pass


        class Class2(Class1, metaclass=Meta3):
            pass
        fail1 = fail2 = False
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(Class1)
        expected_text1 = expected_virtualattribute_pattern2 % __name__
        result1 = output.getvalue().strip()
        self.assertEqual(expected_text1, result1)
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(Class2)
        expected_text2 = expected_virtualattribute_pattern3 % __name__
        result2 = output.getvalue().strip()
        self.assertEqual(expected_text2, result2)

    @unittest.skipIf(sys.flags.optimize >= 2,
        'Docstrings are omitted with -O2 and above')
    @unittest.skipIf(hasattr(sys, 'gettrace') and sys.gettrace(),
        'trace function introduces __locals__ unexpectedly')
    def test_buggy_dir(self):


        class M(type):

            def __dir__(cls):
                return ['__class__', '__name__', 'missing', 'here']


        class C(metaclass=M):
            here = 'present!'
        output = StringIO()
        helper = pydoc.Helper(output=output)
        helper(C)
        expected_text = expected_missingattribute_pattern % __name__
        result = output.getvalue().strip()
        self.assertEqual(expected_text, result)

    def test_resolve_false(self):
        with captured_stdout() as help_io:
            pydoc.help('enum.Enum')
        helptext = help_io.getvalue()
        self.assertIn('class Enum', helptext)


@reap_threads
def test_main():
    try:
        test.support.run_unittest(PydocDocTest, PydocImportTest,
            TestDescriptions, PydocServerTest, PydocUrlHandlerTest,
            TestHelper, PydocWithMetaClasses)
    finally:
        reap_children()


if __name__ == '__main__':
    test_main()
