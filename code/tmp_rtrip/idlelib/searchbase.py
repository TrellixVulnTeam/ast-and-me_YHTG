"""Define SearchDialogBase used by Search, Replace, and Grep dialogs."""
from tkinter import Toplevel, Frame
from tkinter.ttk import Entry, Label, Button, Checkbutton, Radiobutton


class SearchDialogBase:
    """Create most of a 3 or 4 row, 3 column search dialog.

    The left and wide middle column contain:
    1 or 2 labeled text entry lines (make_entry, create_entries);
    a row of standard Checkbuttons (make_frame, create_option_buttons),
    each of which corresponds to a search engine Variable;
    a row of dialog-specific Check/Radiobuttons (create_other_buttons).

    The narrow right column contains command buttons
    (make_button, create_command_buttons).
    These are bound to functions that execute the command.

    Except for command buttons, this base class is not limited to items
    common to all three subclasses.  Rather, it is the Find dialog minus
    the "Find Next" command, its execution function, and the
    default_command attribute needed in create_widgets. The other
    dialogs override attributes and methods, the latter to replace and
    add widgets.
    """
    title = 'Search Dialog'
    icon = 'Search'
    needwrapbutton = 1

    def __init__(self, root, engine):
        """Initialize root, engine, and top attributes.

        top (level widget): set in create_widgets() called from open().
        text (Text searched): set in open(), only used in subclasses().
        ent (ry): created in make_entry() called from create_entry().
        row (of grid): 0 in create_widgets(), +1 in make_entry/frame().
        default_command: set in subclasses, used in create_widgers().

        title (of dialog): class attribute, override in subclasses.
        icon (of dialog): ditto, use unclear if cannot minimize dialog.
        """
        self.root = root
        self.engine = engine
        self.top = None

    def open(self, text, searchphrase=None):
        """Make dialog visible on top of others and ready to use."""
        self.text = text
        if not self.top:
            self.create_widgets()
        else:
            self.top.deiconify()
            self.top.tkraise()
        if searchphrase:
            self.ent.delete(0, 'end')
            self.ent.insert('end', searchphrase)
        self.ent.focus_set()
        self.ent.selection_range(0, 'end')
        self.ent.icursor(0)
        self.top.grab_set()

    def close(self, event=None):
        """Put dialog away for later use."""
        if self.top:
            self.top.grab_release()
            self.top.withdraw()

    def create_widgets(self):
        """Create basic 3 row x 3 col search (find) dialog.

        Other dialogs override subsidiary create_x methods as needed.
        Replace and Find-in-Files add another entry row.
        """
        top = Toplevel(self.root)
        top.bind('<Return>', self.default_command)
        top.bind('<Escape>', self.close)
        top.protocol('WM_DELETE_WINDOW', self.close)
        top.wm_title(self.title)
        top.wm_iconname(self.icon)
        self.top = top
        self.bell = top.bell
        self.row = 0
        self.top.grid_columnconfigure(0, pad=2, weight=0)
        self.top.grid_columnconfigure(1, pad=2, minsize=100, weight=100)
        self.create_entries()
        self.create_option_buttons()
        self.create_other_buttons()
        self.create_command_buttons()

    def make_entry(self, label_text, var):
        """Return (entry, label), .

        entry - gridded labeled Entry for text entry.
        label - Label widget, returned for testing.
        """
        label = Label(self.top, text=label_text)
        label.grid(row=self.row, column=0, sticky='nw')
        entry = Entry(self.top, textvariable=var, exportselection=0)
        entry.grid(row=self.row, column=1, sticky='nwe')
        self.row = self.row + 1
        return entry, label

    def create_entries(self):
        """Create one or more entry lines with make_entry."""
        self.ent = self.make_entry('Find:', self.engine.patvar)[0]

    def make_frame(self, labeltext=None):
        """Return (frame, label).

        frame - gridded labeled Frame for option or other buttons.
        label - Label widget, returned for testing.
        """
        if labeltext:
            label = Label(self.top, text=labeltext)
            label.grid(row=self.row, column=0, sticky='nw')
        else:
            label = ''
        frame = Frame(self.top)
        frame.grid(row=self.row, column=1, columnspan=1, sticky='nwe')
        self.row = self.row + 1
        return frame, label

    def create_option_buttons(self):
        """Return (filled frame, options) for testing.

        Options is a list of searchengine booleanvar, label pairs.
        A gridded frame from make_frame is filled with a Checkbutton
        for each pair, bound to the var, with the corresponding label.
        """
        frame = self.make_frame('Options')[0]
        engine = self.engine
        options = [(engine.revar, 'Regular expression'), (engine.casevar,
            'Match case'), (engine.wordvar, 'Whole word')]
        if self.needwrapbutton:
            options.append((engine.wrapvar, 'Wrap around'))
        for var, label in options:
            btn = Checkbutton(frame, variable=var, text=label)
            btn.pack(side='left', fill='both')
        return frame, options

    def create_other_buttons(self):
        """Return (frame, others) for testing.

        Others is a list of value, label pairs.
        A gridded frame from make_frame is filled with radio buttons.
        """
        frame = self.make_frame('Direction')[0]
        var = self.engine.backvar
        others = [(1, 'Up'), (0, 'Down')]
        for val, label in others:
            btn = Radiobutton(frame, variable=var, value=val, text=label)
            btn.pack(side='left', fill='both')
        return frame, others

    def make_button(self, label, command, isdef=0):
        """Return command button gridded in command frame."""
        b = Button(self.buttonframe, text=label, command=command, default=
            isdef and 'active' or 'normal')
        cols, rows = self.buttonframe.grid_size()
        b.grid(pady=1, row=rows, column=0, sticky='ew')
        self.buttonframe.grid(rowspan=rows + 1)
        return b

    def create_command_buttons(self):
        """Place buttons in vertical command frame gridded on right."""
        f = self.buttonframe = Frame(self.top)
        f.grid(row=0, column=2, padx=2, pady=2, ipadx=2, ipady=2)
        b = self.make_button('close', self.close)
        b.lower()


class _searchbase(SearchDialogBase):
    """Create auto-opening dialog with no text connection."""

    def __init__(self, parent):
        import re
        from idlelib import searchengine
        self.root = parent
        self.engine = searchengine.get(parent)
        self.create_widgets()
        print(parent.geometry())
        width, height, x, y = list(map(int, re.split('[x+]', parent.
            geometry())))
        self.top.geometry('+%d+%d' % (x + 40, y + 175))

    def default_command(self, dummy):
        pass


if __name__ == '__main__':
    import unittest
    unittest.main('idlelib.idle_test.test_searchbase', verbosity=2, exit=False)
    from idlelib.idle_test.htest import run
    run(_searchbase)
