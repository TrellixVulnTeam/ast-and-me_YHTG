import io
import linecache
import queue
import sys
import time
import traceback
import _thread as thread
import threading
import warnings
import tkinter
from idlelib import autocomplete
from idlelib import calltips
from idlelib import debugger_r
from idlelib import debugobj_r
from idlelib import iomenu
from idlelib import rpc
from idlelib import stackviewer
import __main__
for mod in ('simpledialog', 'messagebox', 'font', 'dialog', 'filedialog',
    'commondialog', 'ttk'):
    delattr(tkinter, mod)
    del sys.modules['tkinter.' + mod]
LOCALHOST = '127.0.0.1'


def idle_formatwarning(message, category, filename, lineno, line=None):
    """Format warnings the IDLE way."""
    s = '\nWarning (from warnings module):\n'
    s += '  File "%s", line %s\n' % (filename, lineno)
    if line is None:
        line = linecache.getline(filename, lineno)
    line = line.strip()
    if line:
        s += '    %s\n' % line
    s += '%s: %s\n' % (category.__name__, message)
    return s


def idle_showwarning_subproc(message, category, filename, lineno, file=None,
    line=None):
    """Show Idle-format warning after replacing warnings.showwarning.

    The only difference is the formatter called.
    """
    if file is None:
        file = sys.stderr
    try:
        file.write(idle_formatwarning(message, category, filename, lineno,
            line))
    except OSError:
        pass


_warnings_showwarning = None


def capture_warnings(capture):
    """Replace warning.showwarning with idle_showwarning_subproc, or reverse."""
    global _warnings_showwarning
    if capture:
        if _warnings_showwarning is None:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = idle_showwarning_subproc
    elif _warnings_showwarning is not None:
        warnings.showwarning = _warnings_showwarning
        _warnings_showwarning = None


capture_warnings(True)
tcl = tkinter.Tcl()


def handle_tk_events(tcl=tcl):
    """Process any tk events that are ready to be dispatched if tkinter
    has been imported, a tcl interpreter has been created and tk has been
    loaded."""
    tcl.eval('update')


exit_now = False
quitting = False
interruptable = False


def main(del_exitfunc=False):
    """Start the Python execution server in a subprocess

    In the Python subprocess, RPCServer is instantiated with handlerclass
    MyHandler, which inherits register/unregister methods from RPCHandler via
    the mix-in class SocketIO.

    When the RPCServer 'server' is instantiated, the TCPServer initialization
    creates an instance of run.MyHandler and calls its handle() method.
    handle() instantiates a run.Executive object, passing it a reference to the
    MyHandler object.  That reference is saved as attribute rpchandler of the
    Executive instance.  The Executive methods have access to the reference and
    can pass it on to entities that they command
    (e.g. debugger_r.Debugger.start_debugger()).  The latter, in turn, can
    call MyHandler(SocketIO) register/unregister methods via the reference to
    register and unregister themselves.

    """
    global exit_now
    global quitting
    global no_exitfunc
    no_exitfunc = del_exitfunc
    try:
        assert len(sys.argv) > 1
        port = int(sys.argv[-1])
    except:
        print('IDLE Subprocess: no IP port passed in sys.argv.', file=sys.
            __stderr__)
        return
    capture_warnings(True)
    sys.argv[:] = ['']
    sockthread = threading.Thread(target=manage_socket, name='SockThread',
        args=((LOCALHOST, port),))
    sockthread.daemon = True
    sockthread.start()
    while 1:
        try:
            if exit_now:
                try:
                    exit()
                except KeyboardInterrupt:
                    continue
            try:
                seq, request = rpc.request_queue.get(block=True, timeout=0.05)
            except queue.Empty:
                handle_tk_events()
                continue
            method, args, kwargs = request
            ret = method(*args, **kwargs)
            rpc.response_queue.put((seq, ret))
        except KeyboardInterrupt:
            if quitting:
                exit_now = True
            continue
        except SystemExit:
            capture_warnings(False)
            raise
        except:
            type, value, tb = sys.exc_info()
            try:
                print_exception()
                rpc.response_queue.put((seq, None))
            except:
                traceback.print_exception(type, value, tb, file=sys.__stderr__)
                exit()
            else:
                continue


def manage_socket(address):
    for i in range(3):
        time.sleep(i)
        try:
            server = MyRPCServer(address, MyHandler)
            break
        except OSError as err:
            print('IDLE Subprocess: OSError: ' + err.args[1] +
                ', retrying....', file=sys.__stderr__)
            socket_error = err
    else:
        print('IDLE Subprocess: Connection to IDLE GUI failed, exiting.',
            file=sys.__stderr__)
        show_socket_error(socket_error, address)
        global exit_now
        exit_now = True
        return
    server.handle_request()


def show_socket_error(err, address):
    """Display socket error from manage_socket."""
    import tkinter
    from tkinter.messagebox import showerror
    root = tkinter.Tk()
    root.withdraw()
    msg = f"""IDLE's subprocess can't connect to {address[0]}:{address[1]}.
Fatal OSError #{err.errno}: {err.strerror}.
See the 'Startup failure' section of the IDLE doc, online at
https://docs.python.org/3/library/idle.html#startup-failure"""
    showerror('IDLE Subprocess Error', msg, parent=root)
    root.destroy()


def print_exception():
    import linecache
    linecache.checkcache()
    flush_stdout()
    efile = sys.stderr
    typ, val, tb = excinfo = sys.exc_info()
    sys.last_type, sys.last_value, sys.last_traceback = excinfo
    seen = set()

    def print_exc(typ, exc, tb):
        seen.add(exc)
        context = exc.__context__
        cause = exc.__cause__
        if cause is not None and cause not in seen:
            print_exc(type(cause), cause, cause.__traceback__)
            print(
                '\nThe above exception was the direct cause of the following exception:\n'
                , file=efile)
        elif context is not None and not exc.__suppress_context__ and context not in seen:
            print_exc(type(context), context, context.__traceback__)
            print(
                '\nDuring handling of the above exception, another exception occurred:\n'
                , file=efile)
        if tb:
            tbe = traceback.extract_tb(tb)
            print('Traceback (most recent call last):', file=efile)
            exclude = ('run.py', 'rpc.py', 'threading.py', 'queue.py',
                'debugger_r.py', 'bdb.py')
            cleanup_traceback(tbe, exclude)
            traceback.print_list(tbe, file=efile)
        lines = traceback.format_exception_only(typ, exc)
        for line in lines:
            print(line, end='', file=efile)
    print_exc(typ, val, tb)


def cleanup_traceback(tb, exclude):
    """Remove excluded traces from beginning/end of tb; get cached lines"""
    orig_tb = tb[:]
    while tb:
        for rpcfile in exclude:
            if tb[0][0].count(rpcfile):
                break
        else:
            break
        del tb[0]
    while tb:
        for rpcfile in exclude:
            if tb[-1][0].count(rpcfile):
                break
        else:
            break
        del tb[-1]
    if len(tb) == 0:
        tb[:] = orig_tb[:]
        print('** IDLE Internal Exception: ', file=sys.stderr)
    rpchandler = rpc.objecttable['exec'].rpchandler
    for i in range(len(tb)):
        fn, ln, nm, line = tb[i]
        if nm == '?':
            nm = '-toplevel-'
        if not line and fn.startswith('<pyshell#'):
            line = rpchandler.remotecall('linecache', 'getline', (fn, ln), {})
        tb[i] = fn, ln, nm, line


def flush_stdout():
    """XXX How to do this now?"""


def exit():
    """Exit subprocess, possibly after first clearing exit functions.

    If config-main.cfg/.def 'General' 'delete-exitfunc' is True, then any
    functions registered with atexit will be removed before exiting.
    (VPython support)

    """
    if no_exitfunc:
        import atexit
        atexit._clear()
    capture_warnings(False)
    sys.exit(0)


class MyRPCServer(rpc.RPCServer):

    def handle_error(self, request, client_address):
        """Override RPCServer method for IDLE

        Interrupt the MainThread and exit server if link is dropped.

        """
        global quitting
        try:
            raise
        except SystemExit:
            raise
        except EOFError:
            global exit_now
            exit_now = True
            thread.interrupt_main()
        except:
            erf = sys.__stderr__
            print('\n' + '-' * 40, file=erf)
            print('Unhandled server exception!', file=erf)
            print('Thread: %s' % threading.current_thread().name, file=erf)
            print('Client Address: ', client_address, file=erf)
            print('Request: ', repr(request), file=erf)
            traceback.print_exc(file=erf)
            print('\n*** Unrecoverable, server exiting!', file=erf)
            print('-' * 40, file=erf)
            quitting = True
            thread.interrupt_main()


class PseudoFile(io.TextIOBase):

    def __init__(self, shell, tags, encoding=None):
        self.shell = shell
        self.tags = tags
        self._encoding = encoding

    @property
    def encoding(self):
        return self._encoding

    @property
    def name(self):
        return '<%s>' % self.tags

    def isatty(self):
        return True


class PseudoOutputFile(PseudoFile):

    def writable(self):
        return True

    def write(self, s):
        if self.closed:
            raise ValueError('write to closed file')
        if type(s) is not str:
            if not isinstance(s, str):
                raise TypeError('must be str, not ' + type(s).__name__)
            s = str.__str__(s)
        return self.shell.write(s, self.tags)


class PseudoInputFile(PseudoFile):

    def __init__(self, shell, tags, encoding=None):
        PseudoFile.__init__(self, shell, tags, encoding)
        self._line_buffer = ''

    def readable(self):
        return True

    def read(self, size=-1):
        if self.closed:
            raise ValueError('read from closed file')
        if size is None:
            size = -1
        elif not isinstance(size, int):
            raise TypeError('must be int, not ' + type(size).__name__)
        result = self._line_buffer
        self._line_buffer = ''
        if size < 0:
            while True:
                line = self.shell.readline()
                if not line:
                    break
                result += line
        else:
            while len(result) < size:
                line = self.shell.readline()
                if not line:
                    break
                result += line
            self._line_buffer = result[size:]
            result = result[:size]
        return result

    def readline(self, size=-1):
        if self.closed:
            raise ValueError('read from closed file')
        if size is None:
            size = -1
        elif not isinstance(size, int):
            raise TypeError('must be int, not ' + type(size).__name__)
        line = self._line_buffer or self.shell.readline()
        if size < 0:
            size = len(line)
        eol = line.find('\n', 0, size)
        if eol >= 0:
            size = eol + 1
        self._line_buffer = line[size:]
        return line[:size]

    def close(self):
        self.shell.close()


class MyHandler(rpc.RPCHandler):

    def handle(self):
        """Override base method"""
        executive = Executive(self)
        self.register('exec', executive)
        self.console = self.get_remote_proxy('console')
        sys.stdin = PseudoInputFile(self.console, 'stdin', iomenu.encoding)
        sys.stdout = PseudoOutputFile(self.console, 'stdout', iomenu.encoding)
        sys.stderr = PseudoOutputFile(self.console, 'stderr', iomenu.encoding)
        sys.displayhook = rpc.displayhook
        import pydoc
        pydoc.pager = pydoc.plainpager
        self._keep_stdin = sys.stdin
        self.interp = self.get_remote_proxy('interp')
        rpc.RPCHandler.getresponse(self, myseq=None, wait=0.05)

    def exithook(self):
        """override SocketIO method - wait for MainThread to shut us down"""
        time.sleep(10)

    def EOFhook(self):
        """Override SocketIO method - terminate wait on callback and exit thread"""
        global quitting
        quitting = True
        thread.interrupt_main()

    def decode_interrupthook(self):
        """interrupt awakened thread"""
        global quitting
        quitting = True
        thread.interrupt_main()


class Executive(object):

    def __init__(self, rpchandler):
        self.rpchandler = rpchandler
        self.locals = __main__.__dict__
        self.calltip = calltips.CallTips()
        self.autocomplete = autocomplete.AutoComplete()

    def runcode(self, code):
        global interruptable
        try:
            self.usr_exc_info = None
            interruptable = True
            try:
                exec(code, self.locals)
            finally:
                interruptable = False
        except SystemExit:
            pass
        except:
            self.usr_exc_info = sys.exc_info()
            if quitting:
                exit()
            print_exception()
            jit = self.rpchandler.console.getvar('<<toggle-jit-stack-viewer>>')
            if jit:
                self.rpchandler.interp.open_remote_stack_viewer()
        else:
            flush_stdout()

    def interrupt_the_server(self):
        if interruptable:
            thread.interrupt_main()

    def start_the_debugger(self, gui_adap_oid):
        return debugger_r.start_debugger(self.rpchandler, gui_adap_oid)

    def stop_the_debugger(self, idb_adap_oid):
        """Unregister the Idb Adapter.  Link objects and Idb then subject to GC"""
        self.rpchandler.unregister(idb_adap_oid)

    def get_the_calltip(self, name):
        return self.calltip.fetch_tip(name)

    def get_the_completion_list(self, what, mode):
        return self.autocomplete.fetch_completions(what, mode)

    def stackviewer(self, flist_oid=None):
        if self.usr_exc_info:
            typ, val, tb = self.usr_exc_info
        else:
            return None
        flist = None
        if flist_oid is not None:
            flist = self.rpchandler.get_remote_proxy(flist_oid)
        while tb and tb.tb_frame.f_globals['__name__'] in ['rpc', 'run']:
            tb = tb.tb_next
        sys.last_type = typ
        sys.last_value = val
        item = stackviewer.StackTreeItem(flist, tb)
        return debugobj_r.remote_object_tree_item(item)


capture_warnings(False)
