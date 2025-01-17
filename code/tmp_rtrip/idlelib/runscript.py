"""Extension to execute code outside the Python shell window.

This adds the following commands:

- Check module does a full syntax check of the current module.
  It also runs the tabnanny to catch any inconsistent tabs.

- Run module executes the module's code in the __main__ namespace.  The window
  must have been saved previously. The module is added to sys.modules, and is
  also added to the __main__ namespace.

XXX GvR Redesign this interface (yet again) as follows:

- Present a dialog box for ``Run Module''

- Allow specify command line arguments in the dialog box

"""
import os
import tabnanny
import tokenize
import tkinter.messagebox as tkMessageBox
from idlelib.config import idleConf
from idlelib import macosx
from idlelib import pyshell
indent_message = """Error: Inconsistent indentation detected!

1) Your indentation is outright incorrect (easy to fix), OR

2) Your indentation mixes tabs and spaces.

To fix case 2, change all tabs to spaces by using Edit->Select All followed by Format->Untabify Region and specify the number of columns used by each tab.
"""


class ScriptBinding:
    menudefs = [('run', [None, ('Check Module', '<<check-module>>'), (
        'Run Module', '<<run-module>>')])]

    def __init__(self, editwin):
        self.editwin = editwin
        self.flist = self.editwin.flist
        self.root = self.editwin.root
        if macosx.isCocoaTk():
            self.editwin.text_frame.bind('<<run-module-event-2>>', self.
                _run_module_event)

    def check_module_event(self, event):
        filename = self.getfilename()
        if not filename:
            return 'break'
        if not self.checksyntax(filename):
            return 'break'
        if not self.tabnanny(filename):
            return 'break'

    def tabnanny(self, filename):
        with tokenize.open(filename) as f:
            try:
                tabnanny.process_tokens(tokenize.generate_tokens(f.readline))
            except tokenize.TokenError as msg:
                msgtxt, (lineno, start) = msg.args
                self.editwin.gotoline(lineno)
                self.errorbox('Tabnanny Tokenizing Error', 
                    'Token Error: %s' % msgtxt)
                return False
            except tabnanny.NannyNag as nag:
                self.editwin.gotoline(nag.get_lineno())
                self.errorbox('Tab/space error', indent_message)
                return False
        return True

    def checksyntax(self, filename):
        self.shell = shell = self.flist.open_shell()
        saved_stream = shell.get_warning_stream()
        shell.set_warning_stream(shell.stderr)
        with open(filename, 'rb') as f:
            source = f.read()
        if b'\r' in source:
            source = source.replace(b'\r\n', b'\n')
            source = source.replace(b'\r', b'\n')
        if source and source[-1] != ord(b'\n'):
            source = source + b'\n'
        editwin = self.editwin
        text = editwin.text
        text.tag_remove('ERROR', '1.0', 'end')
        try:
            return compile(source, filename, 'exec')
        except (SyntaxError, OverflowError, ValueError) as value:
            msg = getattr(value, 'msg', '') or value or '<no detail available>'
            lineno = getattr(value, 'lineno', '') or 1
            offset = getattr(value, 'offset', '') or 0
            if offset == 0:
                lineno += 1
            pos = '0.0 + %d lines + %d chars' % (lineno - 1, offset - 1)
            editwin.colorize_syntax_error(text, pos)
            self.errorbox('SyntaxError', '%-20s' % msg)
            return False
        finally:
            shell.set_warning_stream(saved_stream)

    def run_module_event(self, event):
        if macosx.isCocoaTk():
            self.editwin.text_frame.after(200, lambda : self.editwin.
                text_frame.event_generate('<<run-module-event-2>>'))
            return 'break'
        else:
            return self._run_module_event(event)

    def _run_module_event(self, event):
        """Run the module after setting up the environment.

        First check the syntax.  If OK, make sure the shell is active and
        then transfer the arguments, set the run environment's working
        directory to the directory of the module being executed and also
        add that directory to its sys.path if not already included.
        """
        filename = self.getfilename()
        if not filename:
            return 'break'
        code = self.checksyntax(filename)
        if not code:
            return 'break'
        if not self.tabnanny(filename):
            return 'break'
        interp = self.shell.interp
        if pyshell.use_subprocess:
            interp.restart_subprocess(with_cwd=False, filename=self.editwin
                ._filename_to_unicode(filename))
        dirname = os.path.dirname(filename)
        interp.runcommand(
            """if 1:
            __file__ = {filename!r}
            import sys as _sys
            from os.path import basename as _basename
            if (not _sys.argv or
                _basename(_sys.argv[0]) != _basename(__file__)):
                _sys.argv = [__file__]
            import os as _os
            _os.chdir({dirname!r})
            del _sys, _basename, _os
            
"""
            .format(filename=filename, dirname=dirname))
        interp.prepend_syspath(filename)
        interp.runcode(code)
        return 'break'

    def getfilename(self):
        """Get source filename.  If not saved, offer to save (or create) file

        The debugger requires a source file.  Make sure there is one, and that
        the current version of the source buffer has been saved.  If the user
        declines to save or cancels the Save As dialog, return None.

        If the user has configured IDLE for Autosave, the file will be
        silently saved if it already exists and is dirty.

        """
        filename = self.editwin.io.filename
        if not self.editwin.get_saved():
            autosave = idleConf.GetOption('main', 'General', 'autosave',
                type='bool')
            if autosave and filename:
                self.editwin.io.save(None)
            else:
                confirm = self.ask_save_dialog()
                self.editwin.text.focus_set()
                if confirm:
                    self.editwin.io.save(None)
                    filename = self.editwin.io.filename
                else:
                    filename = None
        return filename

    def ask_save_dialog(self):
        msg = 'Source Must Be Saved\n' + 5 * ' ' + 'OK to Save?'
        confirm = tkMessageBox.askokcancel(title='Save Before Run or Check',
            message=msg, default=tkMessageBox.OK, parent=self.editwin.text)
        return confirm

    def errorbox(self, title, message):
        tkMessageBox.showerror(title, message, parent=self.editwin.text)
        self.editwin.text.focus_set()
