import unittest
import urllib.parse
RFC1808_BASE = 'http://a/b/c/d;p?q#f'
RFC2396_BASE = 'http://a/b/c/d;p?q'
RFC3986_BASE = 'http://a/b/c/d;p?q'
SIMPLE_BASE = 'http://a/b/c/d'
parse_qsl_test_cases = [('', []), ('&', []), ('&&', []), ('=', [('', '')]),
    ('=a', [('', 'a')]), ('a', [('a', '')]), ('a=', [('a', '')]), ('&a=b',
    [('a', 'b')]), ('a=a+b&b=b+c', [('a', 'a b'), ('b', 'b c')]), (
    'a=1&a=2', [('a', '1'), ('a', '2')]), (b'', []), (b'&', []), (b'&&', []
    ), (b'=', [(b'', b'')]), (b'=a', [(b'', b'a')]), (b'a', [(b'a', b'')]),
    (b'a=', [(b'a', b'')]), (b'&a=b', [(b'a', b'b')]), (b'a=a+b&b=b+c', [(
    b'a', b'a b'), (b'b', b'b c')]), (b'a=1&a=2', [(b'a', b'1'), (b'a',
    b'2')]), (';', []), (';;', []), (';a=b', [('a', 'b')]), ('a=a+b;b=b+c',
    [('a', 'a b'), ('b', 'b c')]), ('a=1;a=2', [('a', '1'), ('a', '2')]), (
    b';', []), (b';;', []), (b';a=b', [(b'a', b'b')]), (b'a=a+b;b=b+c', [(
    b'a', b'a b'), (b'b', b'b c')]), (b'a=1;a=2', [(b'a', b'1'), (b'a', b'2')])
    ]
parse_qs_test_cases = [('', {}), ('&', {}), ('&&', {}), ('=', {'': ['']}),
    ('=a', {'': ['a']}), ('a', {'a': ['']}), ('a=', {'a': ['']}), ('&a=b',
    {'a': ['b']}), ('a=a+b&b=b+c', {'a': ['a b'], 'b': ['b c']}), (
    'a=1&a=2', {'a': ['1', '2']}), (b'', {}), (b'&', {}), (b'&&', {}), (
    b'=', {b'': [b'']}), (b'=a', {b'': [b'a']}), (b'a', {b'a': [b'']}), (
    b'a=', {b'a': [b'']}), (b'&a=b', {b'a': [b'b']}), (b'a=a+b&b=b+c', {
    b'a': [b'a b'], b'b': [b'b c']}), (b'a=1&a=2', {b'a': [b'1', b'2']}), (
    ';', {}), (';;', {}), (';a=b', {'a': ['b']}), ('a=a+b;b=b+c', {'a': [
    'a b'], 'b': ['b c']}), ('a=1;a=2', {'a': ['1', '2']}), (b';', {}), (
    b';;', {}), (b';a=b', {b'a': [b'b']}), (b'a=a+b;b=b+c', {b'a': [b'a b'],
    b'b': [b'b c']}), (b'a=1;a=2', {b'a': [b'1', b'2']})]


class UrlParseTestCase(unittest.TestCase):

    def checkRoundtrips(self, url, parsed, split):
        result = urllib.parse.urlparse(url)
        self.assertEqual(result, parsed)
        t = (result.scheme, result.netloc, result.path, result.params,
            result.query, result.fragment)
        self.assertEqual(t, parsed)
        result2 = urllib.parse.urlunparse(result)
        self.assertEqual(result2, url)
        self.assertEqual(result2, result.geturl())
        result3 = urllib.parse.urlparse(result.geturl())
        self.assertEqual(result3.geturl(), result.geturl())
        self.assertEqual(result3, result)
        self.assertEqual(result3.scheme, result.scheme)
        self.assertEqual(result3.netloc, result.netloc)
        self.assertEqual(result3.path, result.path)
        self.assertEqual(result3.params, result.params)
        self.assertEqual(result3.query, result.query)
        self.assertEqual(result3.fragment, result.fragment)
        self.assertEqual(result3.username, result.username)
        self.assertEqual(result3.password, result.password)
        self.assertEqual(result3.hostname, result.hostname)
        self.assertEqual(result3.port, result.port)
        result = urllib.parse.urlsplit(url)
        self.assertEqual(result, split)
        t = (result.scheme, result.netloc, result.path, result.query,
            result.fragment)
        self.assertEqual(t, split)
        result2 = urllib.parse.urlunsplit(result)
        self.assertEqual(result2, url)
        self.assertEqual(result2, result.geturl())
        result3 = urllib.parse.urlsplit(result.geturl())
        self.assertEqual(result3.geturl(), result.geturl())
        self.assertEqual(result3, result)
        self.assertEqual(result3.scheme, result.scheme)
        self.assertEqual(result3.netloc, result.netloc)
        self.assertEqual(result3.path, result.path)
        self.assertEqual(result3.query, result.query)
        self.assertEqual(result3.fragment, result.fragment)
        self.assertEqual(result3.username, result.username)
        self.assertEqual(result3.password, result.password)
        self.assertEqual(result3.hostname, result.hostname)
        self.assertEqual(result3.port, result.port)

    def test_qsl(self):
        for orig, expect in parse_qsl_test_cases:
            result = urllib.parse.parse_qsl(orig, keep_blank_values=True)
            self.assertEqual(result, expect, 'Error parsing %r' % orig)
            expect_without_blanks = [v for v in expect if len(v[1])]
            result = urllib.parse.parse_qsl(orig, keep_blank_values=False)
            self.assertEqual(result, expect_without_blanks, 
                'Error parsing %r' % orig)

    def test_qs(self):
        for orig, expect in parse_qs_test_cases:
            result = urllib.parse.parse_qs(orig, keep_blank_values=True)
            self.assertEqual(result, expect, 'Error parsing %r' % orig)
            expect_without_blanks = {v: expect[v] for v in expect if len(
                expect[v][0])}
            result = urllib.parse.parse_qs(orig, keep_blank_values=False)
            self.assertEqual(result, expect_without_blanks, 
                'Error parsing %r' % orig)

    def test_roundtrips(self):
        str_cases = [('file:///tmp/junk.txt', ('file', '', '/tmp/junk.txt',
            '', '', ''), ('file', '', '/tmp/junk.txt', '', '')), (
            'imap://mail.python.org/mbox1', ('imap', 'mail.python.org',
            '/mbox1', '', '', ''), ('imap', 'mail.python.org', '/mbox1', '',
            '')), ('mms://wms.sys.hinet.net/cts/Drama/09006251100.asf', (
            'mms', 'wms.sys.hinet.net', '/cts/Drama/09006251100.asf', '',
            '', ''), ('mms', 'wms.sys.hinet.net',
            '/cts/Drama/09006251100.asf', '', '')), (
            'nfs://server/path/to/file.txt', ('nfs', 'server',
            '/path/to/file.txt', '', '', ''), ('nfs', 'server',
            '/path/to/file.txt', '', '')), (
            'svn+ssh://svn.zope.org/repos/main/ZConfig/trunk/', ('svn+ssh',
            'svn.zope.org', '/repos/main/ZConfig/trunk/', '', '', ''), (
            'svn+ssh', 'svn.zope.org', '/repos/main/ZConfig/trunk/', '', ''
            )), ('git+ssh://git@github.com/user/project.git', ('git+ssh',
            'git@github.com', '/user/project.git', '', '', ''), ('git+ssh',
            'git@github.com', '/user/project.git', '', ''))]

        def _encode(t):
            return t[0].encode('ascii'), tuple(x.encode('ascii') for x in t[1]
                ), tuple(x.encode('ascii') for x in t[2])
        bytes_cases = [_encode(x) for x in str_cases]
        for url, parsed, split in (str_cases + bytes_cases):
            self.checkRoundtrips(url, parsed, split)

    def test_http_roundtrips(self):
        str_cases = [('://www.python.org', ('www.python.org', '', '', '',
            ''), ('www.python.org', '', '', '')), ('://www.python.org#abc',
            ('www.python.org', '', '', '', 'abc'), ('www.python.org', '',
            '', 'abc')), ('://www.python.org?q=abc', ('www.python.org', '',
            '', 'q=abc', ''), ('www.python.org', '', 'q=abc', '')), (
            '://www.python.org/#abc', ('www.python.org', '/', '', '', 'abc'
            ), ('www.python.org', '/', '', 'abc')), ('://a/b/c/d;p?q#f', (
            'a', '/b/c/d', 'p', 'q', 'f'), ('a', '/b/c/d;p', 'q', 'f'))]

        def _encode(t):
            return t[0].encode('ascii'), tuple(x.encode('ascii') for x in t[1]
                ), tuple(x.encode('ascii') for x in t[2])
        bytes_cases = [_encode(x) for x in str_cases]
        str_schemes = 'http', 'https'
        bytes_schemes = b'http', b'https'
        str_tests = str_schemes, str_cases
        bytes_tests = bytes_schemes, bytes_cases
        for schemes, test_cases in (str_tests, bytes_tests):
            for scheme in schemes:
                for url, parsed, split in test_cases:
                    url = scheme + url
                    parsed = (scheme,) + parsed
                    split = (scheme,) + split
                    self.checkRoundtrips(url, parsed, split)

    def checkJoin(self, base, relurl, expected):
        str_components = base, relurl, expected
        self.assertEqual(urllib.parse.urljoin(base, relurl), expected)
        bytes_components = baseb, relurlb, expectedb = [x.encode('ascii') for
            x in str_components]
        self.assertEqual(urllib.parse.urljoin(baseb, relurlb), expectedb)

    def test_unparse_parse(self):
        str_cases = ['Python', './Python', 'x-newscheme://foo.com/stuff',
            'x://y', 'x:/y', 'x:/', '/']
        bytes_cases = [x.encode('ascii') for x in str_cases]
        for u in (str_cases + bytes_cases):
            self.assertEqual(urllib.parse.urlunsplit(urllib.parse.urlsplit(
                u)), u)
            self.assertEqual(urllib.parse.urlunparse(urllib.parse.urlparse(
                u)), u)

    def test_RFC1808(self):
        self.checkJoin(RFC1808_BASE, 'g:h', 'g:h')
        self.checkJoin(RFC1808_BASE, 'g', 'http://a/b/c/g')
        self.checkJoin(RFC1808_BASE, './g', 'http://a/b/c/g')
        self.checkJoin(RFC1808_BASE, 'g/', 'http://a/b/c/g/')
        self.checkJoin(RFC1808_BASE, '/g', 'http://a/g')
        self.checkJoin(RFC1808_BASE, '//g', 'http://g')
        self.checkJoin(RFC1808_BASE, 'g?y', 'http://a/b/c/g?y')
        self.checkJoin(RFC1808_BASE, 'g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin(RFC1808_BASE, '#s', 'http://a/b/c/d;p?q#s')
        self.checkJoin(RFC1808_BASE, 'g#s', 'http://a/b/c/g#s')
        self.checkJoin(RFC1808_BASE, 'g#s/./x', 'http://a/b/c/g#s/./x')
        self.checkJoin(RFC1808_BASE, 'g?y#s', 'http://a/b/c/g?y#s')
        self.checkJoin(RFC1808_BASE, 'g;x', 'http://a/b/c/g;x')
        self.checkJoin(RFC1808_BASE, 'g;x?y#s', 'http://a/b/c/g;x?y#s')
        self.checkJoin(RFC1808_BASE, '.', 'http://a/b/c/')
        self.checkJoin(RFC1808_BASE, './', 'http://a/b/c/')
        self.checkJoin(RFC1808_BASE, '..', 'http://a/b/')
        self.checkJoin(RFC1808_BASE, '../', 'http://a/b/')
        self.checkJoin(RFC1808_BASE, '../g', 'http://a/b/g')
        self.checkJoin(RFC1808_BASE, '../..', 'http://a/')
        self.checkJoin(RFC1808_BASE, '../../', 'http://a/')
        self.checkJoin(RFC1808_BASE, '../../g', 'http://a/g')
        self.checkJoin(RFC1808_BASE, '', 'http://a/b/c/d;p?q#f')
        self.checkJoin(RFC1808_BASE, 'g.', 'http://a/b/c/g.')
        self.checkJoin(RFC1808_BASE, '.g', 'http://a/b/c/.g')
        self.checkJoin(RFC1808_BASE, 'g..', 'http://a/b/c/g..')
        self.checkJoin(RFC1808_BASE, '..g', 'http://a/b/c/..g')
        self.checkJoin(RFC1808_BASE, './../g', 'http://a/b/g')
        self.checkJoin(RFC1808_BASE, './g/.', 'http://a/b/c/g/')
        self.checkJoin(RFC1808_BASE, 'g/./h', 'http://a/b/c/g/h')
        self.checkJoin(RFC1808_BASE, 'g/../h', 'http://a/b/c/h')

    def test_RFC2368(self):
        self.assertEqual(urllib.parse.urlparse('mailto:1337@example.org'),
            ('mailto', '', '1337@example.org', '', '', ''))

    def test_RFC2396(self):
        self.checkJoin(RFC2396_BASE, 'g:h', 'g:h')
        self.checkJoin(RFC2396_BASE, 'g', 'http://a/b/c/g')
        self.checkJoin(RFC2396_BASE, './g', 'http://a/b/c/g')
        self.checkJoin(RFC2396_BASE, 'g/', 'http://a/b/c/g/')
        self.checkJoin(RFC2396_BASE, '/g', 'http://a/g')
        self.checkJoin(RFC2396_BASE, '//g', 'http://g')
        self.checkJoin(RFC2396_BASE, 'g?y', 'http://a/b/c/g?y')
        self.checkJoin(RFC2396_BASE, '#s', 'http://a/b/c/d;p?q#s')
        self.checkJoin(RFC2396_BASE, 'g#s', 'http://a/b/c/g#s')
        self.checkJoin(RFC2396_BASE, 'g?y#s', 'http://a/b/c/g?y#s')
        self.checkJoin(RFC2396_BASE, 'g;x', 'http://a/b/c/g;x')
        self.checkJoin(RFC2396_BASE, 'g;x?y#s', 'http://a/b/c/g;x?y#s')
        self.checkJoin(RFC2396_BASE, '.', 'http://a/b/c/')
        self.checkJoin(RFC2396_BASE, './', 'http://a/b/c/')
        self.checkJoin(RFC2396_BASE, '..', 'http://a/b/')
        self.checkJoin(RFC2396_BASE, '../', 'http://a/b/')
        self.checkJoin(RFC2396_BASE, '../g', 'http://a/b/g')
        self.checkJoin(RFC2396_BASE, '../..', 'http://a/')
        self.checkJoin(RFC2396_BASE, '../../', 'http://a/')
        self.checkJoin(RFC2396_BASE, '../../g', 'http://a/g')
        self.checkJoin(RFC2396_BASE, '', RFC2396_BASE)
        self.checkJoin(RFC2396_BASE, 'g.', 'http://a/b/c/g.')
        self.checkJoin(RFC2396_BASE, '.g', 'http://a/b/c/.g')
        self.checkJoin(RFC2396_BASE, 'g..', 'http://a/b/c/g..')
        self.checkJoin(RFC2396_BASE, '..g', 'http://a/b/c/..g')
        self.checkJoin(RFC2396_BASE, './../g', 'http://a/b/g')
        self.checkJoin(RFC2396_BASE, './g/.', 'http://a/b/c/g/')
        self.checkJoin(RFC2396_BASE, 'g/./h', 'http://a/b/c/g/h')
        self.checkJoin(RFC2396_BASE, 'g/../h', 'http://a/b/c/h')
        self.checkJoin(RFC2396_BASE, 'g;x=1/./y', 'http://a/b/c/g;x=1/y')
        self.checkJoin(RFC2396_BASE, 'g;x=1/../y', 'http://a/b/c/y')
        self.checkJoin(RFC2396_BASE, 'g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin(RFC2396_BASE, 'g?y/../x', 'http://a/b/c/g?y/../x')
        self.checkJoin(RFC2396_BASE, 'g#s/./x', 'http://a/b/c/g#s/./x')
        self.checkJoin(RFC2396_BASE, 'g#s/../x', 'http://a/b/c/g#s/../x')

    def test_RFC3986(self):
        self.checkJoin(RFC3986_BASE, '?y', 'http://a/b/c/d;p?y')
        self.checkJoin(RFC3986_BASE, ';x', 'http://a/b/c/;x')
        self.checkJoin(RFC3986_BASE, 'g:h', 'g:h')
        self.checkJoin(RFC3986_BASE, 'g', 'http://a/b/c/g')
        self.checkJoin(RFC3986_BASE, './g', 'http://a/b/c/g')
        self.checkJoin(RFC3986_BASE, 'g/', 'http://a/b/c/g/')
        self.checkJoin(RFC3986_BASE, '/g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, '//g', 'http://g')
        self.checkJoin(RFC3986_BASE, '?y', 'http://a/b/c/d;p?y')
        self.checkJoin(RFC3986_BASE, 'g?y', 'http://a/b/c/g?y')
        self.checkJoin(RFC3986_BASE, '#s', 'http://a/b/c/d;p?q#s')
        self.checkJoin(RFC3986_BASE, 'g#s', 'http://a/b/c/g#s')
        self.checkJoin(RFC3986_BASE, 'g?y#s', 'http://a/b/c/g?y#s')
        self.checkJoin(RFC3986_BASE, ';x', 'http://a/b/c/;x')
        self.checkJoin(RFC3986_BASE, 'g;x', 'http://a/b/c/g;x')
        self.checkJoin(RFC3986_BASE, 'g;x?y#s', 'http://a/b/c/g;x?y#s')
        self.checkJoin(RFC3986_BASE, '', 'http://a/b/c/d;p?q')
        self.checkJoin(RFC3986_BASE, '.', 'http://a/b/c/')
        self.checkJoin(RFC3986_BASE, './', 'http://a/b/c/')
        self.checkJoin(RFC3986_BASE, '..', 'http://a/b/')
        self.checkJoin(RFC3986_BASE, '../', 'http://a/b/')
        self.checkJoin(RFC3986_BASE, '../g', 'http://a/b/g')
        self.checkJoin(RFC3986_BASE, '../..', 'http://a/')
        self.checkJoin(RFC3986_BASE, '../../', 'http://a/')
        self.checkJoin(RFC3986_BASE, '../../g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, '../../../g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, '../../../g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, '../../../../g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, '/./g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, '/../g', 'http://a/g')
        self.checkJoin(RFC3986_BASE, 'g.', 'http://a/b/c/g.')
        self.checkJoin(RFC3986_BASE, '.g', 'http://a/b/c/.g')
        self.checkJoin(RFC3986_BASE, 'g..', 'http://a/b/c/g..')
        self.checkJoin(RFC3986_BASE, '..g', 'http://a/b/c/..g')
        self.checkJoin(RFC3986_BASE, './../g', 'http://a/b/g')
        self.checkJoin(RFC3986_BASE, './g/.', 'http://a/b/c/g/')
        self.checkJoin(RFC3986_BASE, 'g/./h', 'http://a/b/c/g/h')
        self.checkJoin(RFC3986_BASE, 'g/../h', 'http://a/b/c/h')
        self.checkJoin(RFC3986_BASE, 'g;x=1/./y', 'http://a/b/c/g;x=1/y')
        self.checkJoin(RFC3986_BASE, 'g;x=1/../y', 'http://a/b/c/y')
        self.checkJoin(RFC3986_BASE, 'g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin(RFC3986_BASE, 'g?y/../x', 'http://a/b/c/g?y/../x')
        self.checkJoin(RFC3986_BASE, 'g#s/./x', 'http://a/b/c/g#s/./x')
        self.checkJoin(RFC3986_BASE, 'g#s/../x', 'http://a/b/c/g#s/../x')
        self.checkJoin(RFC3986_BASE, 'http:g', 'http://a/b/c/g')
        self.checkJoin('http://a/b/c/de', ';x', 'http://a/b/c/;x')

    def test_urljoins(self):
        self.checkJoin(SIMPLE_BASE, 'g:h', 'g:h')
        self.checkJoin(SIMPLE_BASE, 'http:g', 'http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, 'http:', 'http://a/b/c/d')
        self.checkJoin(SIMPLE_BASE, 'g', 'http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, './g', 'http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, 'g/', 'http://a/b/c/g/')
        self.checkJoin(SIMPLE_BASE, '/g', 'http://a/g')
        self.checkJoin(SIMPLE_BASE, '//g', 'http://g')
        self.checkJoin(SIMPLE_BASE, '?y', 'http://a/b/c/d?y')
        self.checkJoin(SIMPLE_BASE, 'g?y', 'http://a/b/c/g?y')
        self.checkJoin(SIMPLE_BASE, 'g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin(SIMPLE_BASE, '.', 'http://a/b/c/')
        self.checkJoin(SIMPLE_BASE, './', 'http://a/b/c/')
        self.checkJoin(SIMPLE_BASE, '..', 'http://a/b/')
        self.checkJoin(SIMPLE_BASE, '../', 'http://a/b/')
        self.checkJoin(SIMPLE_BASE, '../g', 'http://a/b/g')
        self.checkJoin(SIMPLE_BASE, '../..', 'http://a/')
        self.checkJoin(SIMPLE_BASE, '../../g', 'http://a/g')
        self.checkJoin(SIMPLE_BASE, './../g', 'http://a/b/g')
        self.checkJoin(SIMPLE_BASE, './g/.', 'http://a/b/c/g/')
        self.checkJoin(SIMPLE_BASE, 'g/./h', 'http://a/b/c/g/h')
        self.checkJoin(SIMPLE_BASE, 'g/../h', 'http://a/b/c/h')
        self.checkJoin(SIMPLE_BASE, 'http:g', 'http://a/b/c/g')
        self.checkJoin(SIMPLE_BASE, 'http:', 'http://a/b/c/d')
        self.checkJoin(SIMPLE_BASE, 'http:?y', 'http://a/b/c/d?y')
        self.checkJoin(SIMPLE_BASE, 'http:g?y', 'http://a/b/c/g?y')
        self.checkJoin(SIMPLE_BASE, 'http:g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin('http:///', '..', 'http:///')
        self.checkJoin('', 'http://a/b/c/g?y/./x', 'http://a/b/c/g?y/./x')
        self.checkJoin('', 'http://a/./g', 'http://a/./g')
        self.checkJoin('svn://pathtorepo/dir1', 'dir2', 'svn://pathtorepo/dir2'
            )
        self.checkJoin('svn+ssh://pathtorepo/dir1', 'dir2',
            'svn+ssh://pathtorepo/dir2')
        self.checkJoin('ws://a/b', 'g', 'ws://a/g')
        self.checkJoin('wss://a/b', 'g', 'wss://a/g')
        self.checkJoin(SIMPLE_BASE + '/', 'foo', SIMPLE_BASE + '/foo')
        self.checkJoin('http://a/b/c/d/e/', '../../f/g/', 'http://a/b/c/f/g/')
        self.checkJoin('http://a/b/c/d/e', '../../f/g/', 'http://a/b/f/g/')
        self.checkJoin('http://a/b/c/d/e/', '/../../f/g/', 'http://a/f/g/')
        self.checkJoin('http://a/b/c/d/e', '/../../f/g/', 'http://a/f/g/')
        self.checkJoin('http://a/b/c/d/e/', '../../f/g', 'http://a/b/c/f/g')
        self.checkJoin('http://a/b/', '../../f/g/', 'http://a/f/g/')
        self.checkJoin('a', 'b', 'b')

    def test_RFC2732(self):
        str_cases = [('http://Test.python.org:5432/foo/', 'test.python.org',
            5432), ('http://12.34.56.78:5432/foo/', '12.34.56.78', 5432), (
            'http://[::1]:5432/foo/', '::1', 5432), (
            'http://[dead:beef::1]:5432/foo/', 'dead:beef::1', 5432), (
            'http://[dead:beef::]:5432/foo/', 'dead:beef::', 5432), (
            'http://[dead:beef:cafe:5417:affe:8FA3:deaf:feed]:5432/foo/',
            'dead:beef:cafe:5417:affe:8fa3:deaf:feed', 5432), (
            'http://[::12.34.56.78]:5432/foo/', '::12.34.56.78', 5432), (
            'http://[::ffff:12.34.56.78]:5432/foo/', '::ffff:12.34.56.78', 
            5432), ('http://Test.python.org/foo/', 'test.python.org', None),
            ('http://12.34.56.78/foo/', '12.34.56.78', None), (
            'http://[::1]/foo/', '::1', None), (
            'http://[dead:beef::1]/foo/', 'dead:beef::1', None), (
            'http://[dead:beef::]/foo/', 'dead:beef::', None), (
            'http://[dead:beef:cafe:5417:affe:8FA3:deaf:feed]/foo/',
            'dead:beef:cafe:5417:affe:8fa3:deaf:feed', None), (
            'http://[::12.34.56.78]/foo/', '::12.34.56.78', None), (
            'http://[::ffff:12.34.56.78]/foo/', '::ffff:12.34.56.78', None),
            ('http://Test.python.org:/foo/', 'test.python.org', None), (
            'http://12.34.56.78:/foo/', '12.34.56.78', None), (
            'http://[::1]:/foo/', '::1', None), (
            'http://[dead:beef::1]:/foo/', 'dead:beef::1', None), (
            'http://[dead:beef::]:/foo/', 'dead:beef::', None), (
            'http://[dead:beef:cafe:5417:affe:8FA3:deaf:feed]:/foo/',
            'dead:beef:cafe:5417:affe:8fa3:deaf:feed', None), (
            'http://[::12.34.56.78]:/foo/', '::12.34.56.78', None), (
            'http://[::ffff:12.34.56.78]:/foo/', '::ffff:12.34.56.78', None)]

        def _encode(t):
            return t[0].encode('ascii'), t[1].encode('ascii'), t[2]
        bytes_cases = [_encode(x) for x in str_cases]
        for url, hostname, port in (str_cases + bytes_cases):
            urlparsed = urllib.parse.urlparse(url)
            self.assertEqual((urlparsed.hostname, urlparsed.port), (
                hostname, port))
        str_cases = ['http://::12.34.56.78]/', 'http://[::1/foo/',
            'ftp://[::1/foo/bad]/bad', 'http://[::1/foo/bad]/bad',
            'http://[::ffff:12.34.56.78']
        bytes_cases = [x.encode('ascii') for x in str_cases]
        for invalid_url in (str_cases + bytes_cases):
            self.assertRaises(ValueError, urllib.parse.urlparse, invalid_url)

    def test_urldefrag(self):
        str_cases = [('http://python.org#frag', 'http://python.org', 'frag'
            ), ('http://python.org', 'http://python.org', ''), (
            'http://python.org/#frag', 'http://python.org/', 'frag'), (
            'http://python.org/', 'http://python.org/', ''), (
            'http://python.org/?q#frag', 'http://python.org/?q', 'frag'), (
            'http://python.org/?q', 'http://python.org/?q', ''), (
            'http://python.org/p#frag', 'http://python.org/p', 'frag'), (
            'http://python.org/p?q', 'http://python.org/p?q', ''), (
            RFC1808_BASE, 'http://a/b/c/d;p?q', 'f'), (RFC2396_BASE,
            'http://a/b/c/d;p?q', '')]

        def _encode(t):
            return type(t)(x.encode('ascii') for x in t)
        bytes_cases = [_encode(x) for x in str_cases]
        for url, defrag, frag in (str_cases + bytes_cases):
            result = urllib.parse.urldefrag(url)
            self.assertEqual(result.geturl(), url)
            self.assertEqual(result, (defrag, frag))
            self.assertEqual(result.url, defrag)
            self.assertEqual(result.fragment, frag)

    def test_urlsplit_attributes(self):
        url = 'HTTP://WWW.PYTHON.ORG/doc/#frag'
        p = urllib.parse.urlsplit(url)
        self.assertEqual(p.scheme, 'http')
        self.assertEqual(p.netloc, 'WWW.PYTHON.ORG')
        self.assertEqual(p.path, '/doc/')
        self.assertEqual(p.query, '')
        self.assertEqual(p.fragment, 'frag')
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, 'www.python.org')
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl()[4:], url[4:])
        url = 'http://User:Pass@www.python.org:080/doc/?query=yes#frag'
        p = urllib.parse.urlsplit(url)
        self.assertEqual(p.scheme, 'http')
        self.assertEqual(p.netloc, 'User:Pass@www.python.org:080')
        self.assertEqual(p.path, '/doc/')
        self.assertEqual(p.query, 'query=yes')
        self.assertEqual(p.fragment, 'frag')
        self.assertEqual(p.username, 'User')
        self.assertEqual(p.password, 'Pass')
        self.assertEqual(p.hostname, 'www.python.org')
        self.assertEqual(p.port, 80)
        self.assertEqual(p.geturl(), url)
        url = (
            'http://User@example.com:Pass@www.python.org:080/doc/?query=yes#frag'
            )
        p = urllib.parse.urlsplit(url)
        self.assertEqual(p.scheme, 'http')
        self.assertEqual(p.netloc, 'User@example.com:Pass@www.python.org:080')
        self.assertEqual(p.path, '/doc/')
        self.assertEqual(p.query, 'query=yes')
        self.assertEqual(p.fragment, 'frag')
        self.assertEqual(p.username, 'User@example.com')
        self.assertEqual(p.password, 'Pass')
        self.assertEqual(p.hostname, 'www.python.org')
        self.assertEqual(p.port, 80)
        self.assertEqual(p.geturl(), url)
        url = b'HTTP://WWW.PYTHON.ORG/doc/#frag'
        p = urllib.parse.urlsplit(url)
        self.assertEqual(p.scheme, b'http')
        self.assertEqual(p.netloc, b'WWW.PYTHON.ORG')
        self.assertEqual(p.path, b'/doc/')
        self.assertEqual(p.query, b'')
        self.assertEqual(p.fragment, b'frag')
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, b'www.python.org')
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl()[4:], url[4:])
        url = b'http://User:Pass@www.python.org:080/doc/?query=yes#frag'
        p = urllib.parse.urlsplit(url)
        self.assertEqual(p.scheme, b'http')
        self.assertEqual(p.netloc, b'User:Pass@www.python.org:080')
        self.assertEqual(p.path, b'/doc/')
        self.assertEqual(p.query, b'query=yes')
        self.assertEqual(p.fragment, b'frag')
        self.assertEqual(p.username, b'User')
        self.assertEqual(p.password, b'Pass')
        self.assertEqual(p.hostname, b'www.python.org')
        self.assertEqual(p.port, 80)
        self.assertEqual(p.geturl(), url)
        url = (
            b'http://User@example.com:Pass@www.python.org:080/doc/?query=yes#frag'
            )
        p = urllib.parse.urlsplit(url)
        self.assertEqual(p.scheme, b'http')
        self.assertEqual(p.netloc, b'User@example.com:Pass@www.python.org:080')
        self.assertEqual(p.path, b'/doc/')
        self.assertEqual(p.query, b'query=yes')
        self.assertEqual(p.fragment, b'frag')
        self.assertEqual(p.username, b'User@example.com')
        self.assertEqual(p.password, b'Pass')
        self.assertEqual(p.hostname, b'www.python.org')
        self.assertEqual(p.port, 80)
        self.assertEqual(p.geturl(), url)
        url = b'HTTP://WWW.PYTHON.ORG:65536/doc/#frag'
        p = urllib.parse.urlsplit(url)
        with self.assertRaisesRegex(ValueError, 'out of range'):
            p.port

    def test_attributes_bad_port(self):
        """Check handling of invalid ports."""
        for bytes in (False, True):
            for parse in (urllib.parse.urlsplit, urllib.parse.urlparse):
                for port in ('foo', '1.5', '-1', '0x10'):
                    with self.subTest(bytes=bytes, parse=parse, port=port):
                        netloc = 'www.example.net:' + port
                        url = 'http://' + netloc
                        if bytes:
                            netloc = netloc.encode('ascii')
                            url = url.encode('ascii')
                        p = parse(url)
                        self.assertEqual(p.netloc, netloc)
                        with self.assertRaises(ValueError):
                            p.port

    def test_attributes_without_netloc(self):
        uri = 'sip:alice@atlanta.com;maddr=239.255.255.1;ttl=15'
        p = urllib.parse.urlsplit(uri)
        self.assertEqual(p.netloc, '')
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, None)
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl(), uri)
        p = urllib.parse.urlparse(uri)
        self.assertEqual(p.netloc, '')
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, None)
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl(), uri)
        uri = b'sip:alice@atlanta.com;maddr=239.255.255.1;ttl=15'
        p = urllib.parse.urlsplit(uri)
        self.assertEqual(p.netloc, b'')
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, None)
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl(), uri)
        p = urllib.parse.urlparse(uri)
        self.assertEqual(p.netloc, b'')
        self.assertEqual(p.username, None)
        self.assertEqual(p.password, None)
        self.assertEqual(p.hostname, None)
        self.assertEqual(p.port, None)
        self.assertEqual(p.geturl(), uri)

    def test_noslash(self):
        self.assertEqual(urllib.parse.urlparse(
            'http://example.com?blahblah=/foo'), ('http', 'example.com', '',
            '', 'blahblah=/foo', ''))
        self.assertEqual(urllib.parse.urlparse(
            b'http://example.com?blahblah=/foo'), (b'http', b'example.com',
            b'', b'', b'blahblah=/foo', b''))

    def test_withoutscheme(self):
        self.assertEqual(urllib.parse.urlparse('path'), ('', '', 'path', '',
            '', ''))
        self.assertEqual(urllib.parse.urlparse('//www.python.org:80'), ('',
            'www.python.org:80', '', '', '', ''))
        self.assertEqual(urllib.parse.urlparse('http://www.python.org:80'),
            ('http', 'www.python.org:80', '', '', '', ''))
        self.assertEqual(urllib.parse.urlparse(b'path'), (b'', b'', b'path',
            b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(b'//www.python.org:80'), (
            b'', b'www.python.org:80', b'', b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(b'http://www.python.org:80'),
            (b'http', b'www.python.org:80', b'', b'', b'', b''))

    def test_portseparator(self):
        self.assertEqual(urllib.parse.urlparse('path:80'), ('', '',
            'path:80', '', '', ''))
        self.assertEqual(urllib.parse.urlparse('http:'), ('http', '', '',
            '', '', ''))
        self.assertEqual(urllib.parse.urlparse('https:'), ('https', '', '',
            '', '', ''))
        self.assertEqual(urllib.parse.urlparse('http://www.python.org:80'),
            ('http', 'www.python.org:80', '', '', '', ''))
        self.assertEqual(urllib.parse.urlparse(b'path:80'), (b'', b'',
            b'path:80', b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(b'http:'), (b'http', b'',
            b'', b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(b'https:'), (b'https', b'',
            b'', b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(b'http://www.python.org:80'),
            (b'http', b'www.python.org:80', b'', b'', b'', b''))

    def test_usingsys(self):
        self.assertRaises(TypeError, urllib.parse.urlencode, 'foo')

    def test_anyscheme(self):
        self.assertEqual(urllib.parse.urlparse('s3://foo.com/stuff'), ('s3',
            'foo.com', '/stuff', '', '', ''))
        self.assertEqual(urllib.parse.urlparse(
            'x-newscheme://foo.com/stuff'), ('x-newscheme', 'foo.com',
            '/stuff', '', '', ''))
        self.assertEqual(urllib.parse.urlparse(
            'x-newscheme://foo.com/stuff?query#fragment'), ('x-newscheme',
            'foo.com', '/stuff', '', 'query', 'fragment'))
        self.assertEqual(urllib.parse.urlparse(
            'x-newscheme://foo.com/stuff?query'), ('x-newscheme', 'foo.com',
            '/stuff', '', 'query', ''))
        self.assertEqual(urllib.parse.urlparse(b's3://foo.com/stuff'), (
            b's3', b'foo.com', b'/stuff', b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(
            b'x-newscheme://foo.com/stuff'), (b'x-newscheme', b'foo.com',
            b'/stuff', b'', b'', b''))
        self.assertEqual(urllib.parse.urlparse(
            b'x-newscheme://foo.com/stuff?query#fragment'), (b'x-newscheme',
            b'foo.com', b'/stuff', b'', b'query', b'fragment'))
        self.assertEqual(urllib.parse.urlparse(
            b'x-newscheme://foo.com/stuff?query'), (b'x-newscheme',
            b'foo.com', b'/stuff', b'', b'query', b''))

    def test_default_scheme(self):
        for func in (urllib.parse.urlparse, urllib.parse.urlsplit):
            with self.subTest(function=func):
                result = func('http://example.net/', 'ftp')
                self.assertEqual(result.scheme, 'http')
                result = func(b'http://example.net/', b'ftp')
                self.assertEqual(result.scheme, b'http')
                self.assertEqual(func('path', 'ftp').scheme, 'ftp')
                self.assertEqual(func('path', scheme='ftp').scheme, 'ftp')
                self.assertEqual(func(b'path', scheme=b'ftp').scheme, b'ftp')
                self.assertEqual(func('path').scheme, '')
                self.assertEqual(func(b'path').scheme, b'')
                self.assertEqual(func(b'path', '').scheme, b'')

    def test_parse_fragments(self):
        tests = ('http:#frag', 'path', 'frag'), ('//example.net#frag',
            'path', 'frag'), ('index.html#frag', 'path', 'frag'), (';a=b#frag',
            'params', 'frag'), ('?a=b#frag', 'query', 'frag'), ('#frag',
            'path', 'frag'), ('abc#@frag', 'path', '@frag'), ('//abc#@frag',
            'path', '@frag'), ('//abc:80#@frag', 'path', '@frag'), (
            '//abc#@frag:80', 'path', '@frag:80')
        for url, attr, expected_frag in tests:
            for func in (urllib.parse.urlparse, urllib.parse.urlsplit):
                if attr == 'params' and func is urllib.parse.urlsplit:
                    attr = 'path'
                with self.subTest(url=url, function=func):
                    result = func(url, allow_fragments=False)
                    self.assertEqual(result.fragment, '')
                    self.assertTrue(getattr(result, attr).endswith('#' +
                        expected_frag))
                    self.assertEqual(func(url, '', False).fragment, '')
                    result = func(url, allow_fragments=True)
                    self.assertEqual(result.fragment, expected_frag)
                    self.assertFalse(getattr(result, attr).endswith(
                        expected_frag))
                    self.assertEqual(func(url, '', True).fragment,
                        expected_frag)
                    self.assertEqual(func(url).fragment, expected_frag)

    def test_mixed_types_rejected(self):
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlparse('www.python.org', b'http')
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlparse(b'www.python.org', 'http')
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlsplit('www.python.org', b'http')
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlsplit(b'www.python.org', 'http')
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlunparse((b'http', 'www.python.org', '', '', '', '')
                )
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlunparse(('http', b'www.python.org', '', '', '', '')
                )
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlunsplit((b'http', 'www.python.org', '', '', ''))
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urlunsplit(('http', b'www.python.org', '', '', ''))
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urljoin('http://python.org', b'http://python.org')
        with self.assertRaisesRegex(TypeError, 'Cannot mix str'):
            urllib.parse.urljoin(b'http://python.org', 'http://python.org')

    def _check_result_type(self, str_type):
        num_args = len(str_type._fields)
        bytes_type = str_type._encoded_counterpart
        self.assertIs(bytes_type._decoded_counterpart, str_type)
        str_args = ('',) * num_args
        bytes_args = (b'',) * num_args
        str_result = str_type(*str_args)
        bytes_result = bytes_type(*bytes_args)
        encoding = 'ascii'
        errors = 'strict'
        self.assertEqual(str_result, str_args)
        self.assertEqual(bytes_result.decode(), str_args)
        self.assertEqual(bytes_result.decode(), str_result)
        self.assertEqual(bytes_result.decode(encoding), str_args)
        self.assertEqual(bytes_result.decode(encoding), str_result)
        self.assertEqual(bytes_result.decode(encoding, errors), str_args)
        self.assertEqual(bytes_result.decode(encoding, errors), str_result)
        self.assertEqual(bytes_result, bytes_args)
        self.assertEqual(str_result.encode(), bytes_args)
        self.assertEqual(str_result.encode(), bytes_result)
        self.assertEqual(str_result.encode(encoding), bytes_args)
        self.assertEqual(str_result.encode(encoding), bytes_result)
        self.assertEqual(str_result.encode(encoding, errors), bytes_args)
        self.assertEqual(str_result.encode(encoding, errors), bytes_result)

    def test_result_pairs(self):
        result_types = [urllib.parse.DefragResult, urllib.parse.SplitResult,
            urllib.parse.ParseResult]
        for result_type in result_types:
            self._check_result_type(result_type)

    def test_parse_qs_encoding(self):
        result = urllib.parse.parse_qs('key=Ł%E9', encoding='latin-1')
        self.assertEqual(result, {'key': ['Łé']})
        result = urllib.parse.parse_qs('key=Ł%C3%A9', encoding='utf-8')
        self.assertEqual(result, {'key': ['Łé']})
        result = urllib.parse.parse_qs('key=Ł%C3%A9', encoding='ascii')
        self.assertEqual(result, {'key': ['Ł��']})
        result = urllib.parse.parse_qs('key=Ł%E9-', encoding='ascii')
        self.assertEqual(result, {'key': ['Ł�-']})
        result = urllib.parse.parse_qs('key=Ł%E9-', encoding='ascii',
            errors='ignore')
        self.assertEqual(result, {'key': ['Ł-']})

    def test_parse_qsl_encoding(self):
        result = urllib.parse.parse_qsl('key=Ł%E9', encoding='latin-1')
        self.assertEqual(result, [('key', 'Łé')])
        result = urllib.parse.parse_qsl('key=Ł%C3%A9', encoding='utf-8')
        self.assertEqual(result, [('key', 'Łé')])
        result = urllib.parse.parse_qsl('key=Ł%C3%A9', encoding='ascii')
        self.assertEqual(result, [('key', 'Ł��')])
        result = urllib.parse.parse_qsl('key=Ł%E9-', encoding='ascii')
        self.assertEqual(result, [('key', 'Ł�-')])
        result = urllib.parse.parse_qsl('key=Ł%E9-', encoding='ascii',
            errors='ignore')
        self.assertEqual(result, [('key', 'Ł-')])

    def test_urlencode_sequences(self):
        result = urllib.parse.urlencode({'a': [1, 2], 'b': (3, 4, 5)}, True)
        assert set(result.split('&')) == {'a=1', 'a=2', 'b=3', 'b=4', 'b=5'}


        class Trivial:

            def __str__(self):
                return 'trivial'
        result = urllib.parse.urlencode({'a': Trivial()}, True)
        self.assertEqual(result, 'a=trivial')

    def test_urlencode_quote_via(self):
        result = urllib.parse.urlencode({'a': 'some value'})
        self.assertEqual(result, 'a=some+value')
        result = urllib.parse.urlencode({'a': 'some value/another'},
            quote_via=urllib.parse.quote)
        self.assertEqual(result, 'a=some%20value%2Fanother')
        result = urllib.parse.urlencode({'a': 'some value/another'}, safe=
            '/', quote_via=urllib.parse.quote)
        self.assertEqual(result, 'a=some%20value/another')

    def test_quote_from_bytes(self):
        self.assertRaises(TypeError, urllib.parse.quote_from_bytes, 'foo')
        result = urllib.parse.quote_from_bytes(b'archaeological arcana')
        self.assertEqual(result, 'archaeological%20arcana')
        result = urllib.parse.quote_from_bytes(b'')
        self.assertEqual(result, '')

    def test_unquote_to_bytes(self):
        result = urllib.parse.unquote_to_bytes('abc%20def')
        self.assertEqual(result, b'abc def')
        result = urllib.parse.unquote_to_bytes('')
        self.assertEqual(result, b'')

    def test_quote_errors(self):
        self.assertRaises(TypeError, urllib.parse.quote, b'foo', encoding=
            'utf-8')
        self.assertRaises(TypeError, urllib.parse.quote, b'foo', errors=
            'strict')

    def test_issue14072(self):
        p1 = urllib.parse.urlsplit('tel:+31-641044153')
        self.assertEqual(p1.scheme, 'tel')
        self.assertEqual(p1.path, '+31-641044153')
        p2 = urllib.parse.urlsplit('tel:+31641044153')
        self.assertEqual(p2.scheme, 'tel')
        self.assertEqual(p2.path, '+31641044153')
        p1 = urllib.parse.urlparse('tel:+31-641044153')
        self.assertEqual(p1.scheme, 'tel')
        self.assertEqual(p1.path, '+31-641044153')
        p2 = urllib.parse.urlparse('tel:+31641044153')
        self.assertEqual(p2.scheme, 'tel')
        self.assertEqual(p2.path, '+31641044153')

    def test_telurl_params(self):
        p1 = urllib.parse.urlparse('tel:123-4;phone-context=+1-650-516')
        self.assertEqual(p1.scheme, 'tel')
        self.assertEqual(p1.path, '123-4')
        self.assertEqual(p1.params, 'phone-context=+1-650-516')
        p1 = urllib.parse.urlparse('tel:+1-201-555-0123')
        self.assertEqual(p1.scheme, 'tel')
        self.assertEqual(p1.path, '+1-201-555-0123')
        self.assertEqual(p1.params, '')
        p1 = urllib.parse.urlparse('tel:7042;phone-context=example.com')
        self.assertEqual(p1.scheme, 'tel')
        self.assertEqual(p1.path, '7042')
        self.assertEqual(p1.params, 'phone-context=example.com')
        p1 = urllib.parse.urlparse('tel:863-1234;phone-context=+1-914-555')
        self.assertEqual(p1.scheme, 'tel')
        self.assertEqual(p1.path, '863-1234')
        self.assertEqual(p1.params, 'phone-context=+1-914-555')

    def test_Quoter_repr(self):
        quoter = urllib.parse.Quoter(urllib.parse._ALWAYS_SAFE)
        self.assertIn('Quoter', repr(quoter))

    def test_all(self):
        expected = []
        undocumented = {'splitattr', 'splithost', 'splitnport',
            'splitpasswd', 'splitport', 'splitquery', 'splittag',
            'splittype', 'splituser', 'splitvalue', 'Quoter', 'ResultBase',
            'clear_cache', 'to_bytes', 'unwrap'}
        for name in dir(urllib.parse):
            if name.startswith('_') or name in undocumented:
                continue
            object = getattr(urllib.parse, name)
            if getattr(object, '__module__', None) == 'urllib.parse':
                expected.append(name)
        self.assertCountEqual(urllib.parse.__all__, expected)


class Utility_Tests(unittest.TestCase):
    """Testcase to test the various utility functions in the urllib."""

    def test_splittype(self):
        splittype = urllib.parse.splittype
        self.assertEqual(splittype('type:opaquestring'), ('type',
            'opaquestring'))
        self.assertEqual(splittype('opaquestring'), (None, 'opaquestring'))
        self.assertEqual(splittype(':opaquestring'), (None, ':opaquestring'))
        self.assertEqual(splittype('type:'), ('type', ''))
        self.assertEqual(splittype('type:opaque:string'), ('type',
            'opaque:string'))

    def test_splithost(self):
        splithost = urllib.parse.splithost
        self.assertEqual(splithost('//www.example.org:80/foo/bar/baz.html'),
            ('www.example.org:80', '/foo/bar/baz.html'))
        self.assertEqual(splithost('//www.example.org:80'), (
            'www.example.org:80', ''))
        self.assertEqual(splithost('/foo/bar/baz.html'), (None,
            '/foo/bar/baz.html'))
        self.assertEqual(splithost('//127.0.0.1#@host.com'), ('127.0.0.1',
            '/#@host.com'))
        self.assertEqual(splithost('//127.0.0.1#@host.com:80'), (
            '127.0.0.1', '/#@host.com:80'))
        self.assertEqual(splithost('//127.0.0.1:80#@host.com'), (
            '127.0.0.1:80', '/#@host.com'))
        self.assertEqual(splithost('///file'), ('', '/file'))
        self.assertEqual(splithost('//example.net/file;'), ('example.net',
            '/file;'))
        self.assertEqual(splithost('//example.net/file?'), ('example.net',
            '/file?'))
        self.assertEqual(splithost('//example.net/file#'), ('example.net',
            '/file#'))

    def test_splituser(self):
        splituser = urllib.parse.splituser
        self.assertEqual(splituser('User:Pass@www.python.org:080'), (
            'User:Pass', 'www.python.org:080'))
        self.assertEqual(splituser('@www.python.org:080'), ('',
            'www.python.org:080'))
        self.assertEqual(splituser('www.python.org:080'), (None,
            'www.python.org:080'))
        self.assertEqual(splituser('User:Pass@'), ('User:Pass', ''))
        self.assertEqual(splituser(
            'User@example.com:Pass@www.python.org:080'), (
            'User@example.com:Pass', 'www.python.org:080'))

    def test_splitpasswd(self):
        splitpasswd = urllib.parse.splitpasswd
        self.assertEqual(splitpasswd('user:ab'), ('user', 'ab'))
        self.assertEqual(splitpasswd('user:a\nb'), ('user', 'a\nb'))
        self.assertEqual(splitpasswd('user:a\tb'), ('user', 'a\tb'))
        self.assertEqual(splitpasswd('user:a\rb'), ('user', 'a\rb'))
        self.assertEqual(splitpasswd('user:a\x0cb'), ('user', 'a\x0cb'))
        self.assertEqual(splitpasswd('user:a\x0bb'), ('user', 'a\x0bb'))
        self.assertEqual(splitpasswd('user:a:b'), ('user', 'a:b'))
        self.assertEqual(splitpasswd('user:a b'), ('user', 'a b'))
        self.assertEqual(splitpasswd('user 2:ab'), ('user 2', 'ab'))
        self.assertEqual(splitpasswd('user+1:a+b'), ('user+1', 'a+b'))
        self.assertEqual(splitpasswd('user:'), ('user', ''))
        self.assertEqual(splitpasswd('user'), ('user', None))
        self.assertEqual(splitpasswd(':ab'), ('', 'ab'))

    def test_splitport(self):
        splitport = urllib.parse.splitport
        self.assertEqual(splitport('parrot:88'), ('parrot', '88'))
        self.assertEqual(splitport('parrot'), ('parrot', None))
        self.assertEqual(splitport('parrot:'), ('parrot', None))
        self.assertEqual(splitport('127.0.0.1'), ('127.0.0.1', None))
        self.assertEqual(splitport('parrot:cheese'), ('parrot:cheese', None))
        self.assertEqual(splitport('[::1]:88'), ('[::1]', '88'))
        self.assertEqual(splitport('[::1]'), ('[::1]', None))
        self.assertEqual(splitport(':88'), ('', '88'))

    def test_splitnport(self):
        splitnport = urllib.parse.splitnport
        self.assertEqual(splitnport('parrot:88'), ('parrot', 88))
        self.assertEqual(splitnport('parrot'), ('parrot', -1))
        self.assertEqual(splitnport('parrot', 55), ('parrot', 55))
        self.assertEqual(splitnport('parrot:'), ('parrot', -1))
        self.assertEqual(splitnport('parrot:', 55), ('parrot', 55))
        self.assertEqual(splitnport('127.0.0.1'), ('127.0.0.1', -1))
        self.assertEqual(splitnport('127.0.0.1', 55), ('127.0.0.1', 55))
        self.assertEqual(splitnport('parrot:cheese'), ('parrot', None))
        self.assertEqual(splitnport('parrot:cheese', 55), ('parrot', None))

    def test_splitquery(self):
        splitquery = urllib.parse.splitquery
        self.assertEqual(splitquery('http://python.org/fake?foo=bar'), (
            'http://python.org/fake', 'foo=bar'))
        self.assertEqual(splitquery('http://python.org/fake?foo=bar?'), (
            'http://python.org/fake?foo=bar', ''))
        self.assertEqual(splitquery('http://python.org/fake'), (
            'http://python.org/fake', None))
        self.assertEqual(splitquery('?foo=bar'), ('', 'foo=bar'))

    def test_splittag(self):
        splittag = urllib.parse.splittag
        self.assertEqual(splittag('http://example.com?foo=bar#baz'), (
            'http://example.com?foo=bar', 'baz'))
        self.assertEqual(splittag('http://example.com?foo=bar#'), (
            'http://example.com?foo=bar', ''))
        self.assertEqual(splittag('#baz'), ('', 'baz'))
        self.assertEqual(splittag('http://example.com?foo=bar'), (
            'http://example.com?foo=bar', None))
        self.assertEqual(splittag('http://example.com?foo=bar#baz#boo'), (
            'http://example.com?foo=bar#baz', 'boo'))

    def test_splitattr(self):
        splitattr = urllib.parse.splitattr
        self.assertEqual(splitattr('/path;attr1=value1;attr2=value2'), (
            '/path', ['attr1=value1', 'attr2=value2']))
        self.assertEqual(splitattr('/path;'), ('/path', ['']))
        self.assertEqual(splitattr(';attr1=value1;attr2=value2'), ('', [
            'attr1=value1', 'attr2=value2']))
        self.assertEqual(splitattr('/path'), ('/path', []))

    def test_splitvalue(self):
        splitvalue = urllib.parse.splitvalue
        self.assertEqual(splitvalue('foo=bar'), ('foo', 'bar'))
        self.assertEqual(splitvalue('foo='), ('foo', ''))
        self.assertEqual(splitvalue('=bar'), ('', 'bar'))
        self.assertEqual(splitvalue('foobar'), ('foobar', None))
        self.assertEqual(splitvalue('foo=bar=baz'), ('foo', 'bar=baz'))

    def test_to_bytes(self):
        result = urllib.parse.to_bytes('http://www.python.org')
        self.assertEqual(result, 'http://www.python.org')
        self.assertRaises(UnicodeError, urllib.parse.to_bytes,
            'http://www.python.org/mediæval')

    def test_unwrap(self):
        url = urllib.parse.unwrap('<URL:type://host/path>')
        self.assertEqual(url, 'type://host/path')


if __name__ == '__main__':
    unittest.main()
