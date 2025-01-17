import os
import itertools
import sys
import weakref
import atexit
import threading
from subprocess import _args_from_interpreter_flags
from . import process
__all__ = ['sub_debug', 'debug', 'info', 'sub_warning', 'get_logger',
    'log_to_stderr', 'get_temp_dir', 'register_after_fork', 'is_exiting',
    'Finalize', 'ForkAwareThreadLock', 'ForkAwareLocal',
    'close_all_fds_except', 'SUBDEBUG', 'SUBWARNING']
NOTSET = 0
SUBDEBUG = 5
DEBUG = 10
INFO = 20
SUBWARNING = 25
LOGGER_NAME = 'multiprocessing'
DEFAULT_LOGGING_FORMAT = '[%(levelname)s/%(processName)s] %(message)s'
_logger = None
_log_to_stderr = False


def sub_debug(msg, *args):
    if _logger:
        _logger.log(SUBDEBUG, msg, *args)


def debug(msg, *args):
    if _logger:
        _logger.log(DEBUG, msg, *args)


def info(msg, *args):
    if _logger:
        _logger.log(INFO, msg, *args)


def sub_warning(msg, *args):
    if _logger:
        _logger.log(SUBWARNING, msg, *args)


def get_logger():
    """
    Returns logger used by multiprocessing
    """
    global _logger
    import logging
    logging._acquireLock()
    try:
        if not _logger:
            _logger = logging.getLogger(LOGGER_NAME)
            _logger.propagate = 0
            if hasattr(atexit, 'unregister'):
                atexit.unregister(_exit_function)
                atexit.register(_exit_function)
            else:
                atexit._exithandlers.remove((_exit_function, (), {}))
                atexit._exithandlers.append((_exit_function, (), {}))
    finally:
        logging._releaseLock()
    return _logger


def log_to_stderr(level=None):
    """
    Turn on logging and add a handler which prints to stderr
    """
    global _log_to_stderr
    import logging
    logger = get_logger()
    formatter = logging.Formatter(DEFAULT_LOGGING_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if level:
        logger.setLevel(level)
    _log_to_stderr = True
    return _logger


def get_temp_dir():
    tempdir = process.current_process()._config.get('tempdir')
    if tempdir is None:
        import shutil, tempfile
        tempdir = tempfile.mkdtemp(prefix='pymp-')
        info('created temp directory %s', tempdir)
        Finalize(None, shutil.rmtree, args=[tempdir], exitpriority=-100)
        process.current_process()._config['tempdir'] = tempdir
    return tempdir


_afterfork_registry = weakref.WeakValueDictionary()
_afterfork_counter = itertools.count()


def _run_after_forkers():
    items = list(_afterfork_registry.items())
    items.sort()
    for (index, ident, func), obj in items:
        try:
            func(obj)
        except Exception as e:
            info('after forker raised exception %s', e)


def register_after_fork(obj, func):
    _afterfork_registry[next(_afterfork_counter), id(obj), func] = obj


_finalizer_registry = {}
_finalizer_counter = itertools.count()


class Finalize(object):
    """
    Class which supports object finalization using weakrefs
    """

    def __init__(self, obj, callback, args=(), kwargs=None, exitpriority=None):
        assert exitpriority is None or type(exitpriority) is int
        if obj is not None:
            self._weakref = weakref.ref(obj, self)
        else:
            assert exitpriority is not None
        self._callback = callback
        self._args = args
        self._kwargs = kwargs or {}
        self._key = exitpriority, next(_finalizer_counter)
        self._pid = os.getpid()
        _finalizer_registry[self._key] = self

    def __call__(self, wr=None, _finalizer_registry=_finalizer_registry,
        sub_debug=sub_debug, getpid=os.getpid):
        """
        Run the callback unless it has already been called or cancelled
        """
        try:
            del _finalizer_registry[self._key]
        except KeyError:
            sub_debug('finalizer no longer registered')
        else:
            if self._pid != getpid():
                sub_debug('finalizer ignored because different process')
                res = None
            else:
                sub_debug('finalizer calling %s with args %s and kwargs %s',
                    self._callback, self._args, self._kwargs)
                res = self._callback(*self._args, **self._kwargs)
            (self._weakref) = (self._callback) = (self._args) = (self._kwargs
                ) = (self._key) = None
            return res

    def cancel(self):
        """
        Cancel finalization of the object
        """
        try:
            del _finalizer_registry[self._key]
        except KeyError:
            pass
        else:
            (self._weakref) = (self._callback) = (self._args) = (self._kwargs
                ) = (self._key) = None

    def still_active(self):
        """
        Return whether this finalizer is still waiting to invoke callback
        """
        return self._key in _finalizer_registry

    def __repr__(self):
        try:
            obj = self._weakref()
        except (AttributeError, TypeError):
            obj = None
        if obj is None:
            return '<%s object, dead>' % self.__class__.__name__
        x = '<%s object, callback=%s' % (self.__class__.__name__, getattr(
            self._callback, '__name__', self._callback))
        if self._args:
            x += ', args=' + str(self._args)
        if self._kwargs:
            x += ', kwargs=' + str(self._kwargs)
        if self._key[0] is not None:
            x += ', exitprority=' + str(self._key[0])
        return x + '>'


def _run_finalizers(minpriority=None):
    """
    Run all finalizers whose exit priority is not None and at least minpriority

    Finalizers with highest priority are called first; finalizers with
    the same priority will be called in reverse order of creation.
    """
    if _finalizer_registry is None:
        return
    if minpriority is None:
        f = lambda p: p[0] is not None
    else:
        f = lambda p: p[0] is not None and p[0] >= minpriority
    keys = [key for key in list(_finalizer_registry) if f(key)]
    keys.sort(reverse=True)
    for key in keys:
        finalizer = _finalizer_registry.get(key)
        if finalizer is not None:
            sub_debug('calling %s', finalizer)
            try:
                finalizer()
            except Exception:
                import traceback
                traceback.print_exc()
    if minpriority is None:
        _finalizer_registry.clear()


def is_exiting():
    """
    Returns true if the process is shutting down
    """
    return _exiting or _exiting is None


_exiting = False


def _exit_function(info=info, debug=debug, _run_finalizers=_run_finalizers,
    active_children=process.active_children, current_process=process.
    current_process):
    global _exiting
    if not _exiting:
        _exiting = True
        info('process shutting down')
        debug('running all "atexit" finalizers with priority >= 0')
        _run_finalizers(0)
        if current_process() is not None:
            for p in active_children():
                if p.daemon:
                    info('calling terminate() for daemon %s', p.name)
                    p._popen.terminate()
            for p in active_children():
                info('calling join() for process %s', p.name)
                p.join()
        debug('running the remaining "atexit" finalizers')
        _run_finalizers()


atexit.register(_exit_function)


class ForkAwareThreadLock(object):

    def __init__(self):
        self._reset()
        register_after_fork(self, ForkAwareThreadLock._reset)

    def _reset(self):
        self._lock = threading.Lock()
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)


class ForkAwareLocal(threading.local):

    def __init__(self):
        register_after_fork(self, lambda obj: obj.__dict__.clear())

    def __reduce__(self):
        return type(self), ()


try:
    MAXFD = os.sysconf('SC_OPEN_MAX')
except Exception:
    MAXFD = 256


def close_all_fds_except(fds):
    fds = list(fds) + [-1, MAXFD]
    fds.sort()
    assert fds[-1] == MAXFD, 'fd too large'
    for i in range(len(fds) - 1):
        os.closerange(fds[i] + 1, fds[i + 1])


def _close_stdin():
    if sys.stdin is None:
        return
    try:
        sys.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        fd = os.open(os.devnull, os.O_RDONLY)
        try:
            sys.stdin = open(fd, closefd=False)
        except:
            os.close(fd)
            raise
    except (OSError, ValueError):
        pass


def spawnv_passfds(path, args, passfds):
    import _posixsubprocess
    passfds = tuple(sorted(map(int, passfds)))
    errpipe_read, errpipe_write = os.pipe()
    try:
        return _posixsubprocess.fork_exec(args, [os.fsencode(path)], True,
            passfds, None, None, -1, -1, -1, -1, -1, -1, errpipe_read,
            errpipe_write, False, False, None)
    finally:
        os.close(errpipe_read)
        os.close(errpipe_write)
