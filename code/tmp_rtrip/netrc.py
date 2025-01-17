"""An object-oriented interface to .netrc files."""
import os, shlex, stat
__all__ = ['netrc', 'NetrcParseError']


class NetrcParseError(Exception):
    """Exception raised on syntax errors in the .netrc file."""

    def __init__(self, msg, filename=None, lineno=None):
        self.filename = filename
        self.lineno = lineno
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return '%s (%s, line %s)' % (self.msg, self.filename, self.lineno)


class netrc:

    def __init__(self, file=None):
        default_netrc = file is None
        if file is None:
            try:
                file = os.path.join(os.environ['HOME'], '.netrc')
            except KeyError:
                raise OSError('Could not find .netrc: $HOME is not set')
        self.hosts = {}
        self.macros = {}
        with open(file) as fp:
            self._parse(file, fp, default_netrc)

    def _parse(self, file, fp, default_netrc):
        lexer = shlex.shlex(fp)
        lexer.wordchars += '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        lexer.commenters = lexer.commenters.replace('#', '')
        while 1:
            saved_lineno = lexer.lineno
            toplevel = tt = lexer.get_token()
            if not tt:
                break
            elif tt[0] == '#':
                if lexer.lineno == saved_lineno and len(tt) == 1:
                    lexer.instream.readline()
                continue
            elif tt == 'machine':
                entryname = lexer.get_token()
            elif tt == 'default':
                entryname = 'default'
            elif tt == 'macdef':
                entryname = lexer.get_token()
                self.macros[entryname] = []
                lexer.whitespace = ' \t'
                while 1:
                    line = lexer.instream.readline()
                    if not line or line == '\n':
                        lexer.whitespace = ' \t\r\n'
                        break
                    self.macros[entryname].append(line)
                continue
            else:
                raise NetrcParseError('bad toplevel token %r' % tt, file,
                    lexer.lineno)
            login = ''
            account = password = None
            self.hosts[entryname] = {}
            while 1:
                tt = lexer.get_token()
                if tt.startswith('#') or tt in {'', 'machine', 'default',
                    'macdef'}:
                    if password:
                        self.hosts[entryname] = login, account, password
                        lexer.push_token(tt)
                        break
                    else:
                        raise NetrcParseError(
                            'malformed %s entry %s terminated by %s' % (
                            toplevel, entryname, repr(tt)), file, lexer.lineno)
                elif tt == 'login' or tt == 'user':
                    login = lexer.get_token()
                elif tt == 'account':
                    account = lexer.get_token()
                elif tt == 'password':
                    if os.name == 'posix' and default_netrc:
                        prop = os.fstat(fp.fileno())
                        if prop.st_uid != os.getuid():
                            import pwd
                            try:
                                fowner = pwd.getpwuid(prop.st_uid)[0]
                            except KeyError:
                                fowner = 'uid %s' % prop.st_uid
                            try:
                                user = pwd.getpwuid(os.getuid())[0]
                            except KeyError:
                                user = 'uid %s' % os.getuid()
                            raise NetrcParseError(
                                '~/.netrc file owner (%s) does not match current user (%s)'
                                 % (fowner, user), file, lexer.lineno)
                        if prop.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                            raise NetrcParseError(
                                '~/.netrc access too permissive: access permissions must restrict access to only the owner'
                                , file, lexer.lineno)
                    password = lexer.get_token()
                else:
                    raise NetrcParseError('bad follower token %r' % tt,
                        file, lexer.lineno)

    def authenticators(self, host):
        """Return a (user, account, password) tuple for given host."""
        if host in self.hosts:
            return self.hosts[host]
        elif 'default' in self.hosts:
            return self.hosts['default']
        else:
            return None

    def __repr__(self):
        """Dump the class data in the format of a .netrc file."""
        rep = ''
        for host in self.hosts.keys():
            attrs = self.hosts[host]
            rep = rep + 'machine ' + host + '\n\tlogin ' + repr(attrs[0]
                ) + '\n'
            if attrs[1]:
                rep = rep + 'account ' + repr(attrs[1])
            rep = rep + '\tpassword ' + repr(attrs[2]) + '\n'
        for macro in self.macros.keys():
            rep = rep + 'macdef ' + macro + '\n'
            for line in self.macros[macro]:
                rep = rep + line
            rep = rep + '\n'
        return rep


if __name__ == '__main__':
    print(netrc())
