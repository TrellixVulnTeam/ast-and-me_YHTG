"""IDLE Configuration Dialog: support user customization of IDLE by GUI

Customize font faces, sizes, and colorization attributes.  Set indentation
defaults.  Customize keybindings.  Colorization and keybindings can be
saved as user defined sets.  Select startup options including shell/editor
and default window size.  Define additional help sources.

Note that tab width in IDLE is currently fixed at eight due to Tk issues.
Refer to comments in EditorWindow autoindent code for details.

"""
from tkinter import *
from tkinter.ttk import Scrollbar
import tkinter.colorchooser as tkColorChooser
import tkinter.font as tkFont
import tkinter.messagebox as tkMessageBox
from idlelib.config import idleConf
from idlelib.config_key import GetKeysDialog
from idlelib.dynoption import DynOptionMenu
from idlelib import macosx
from idlelib.query import SectionName, HelpSource
from idlelib.tabbedpages import TabbedPageSet
from idlelib.textview import view_text


class ConfigDialog(Toplevel):

    def __init__(self, parent, title='', _htest=False, _utest=False):
        """
        _htest - bool, change box location when running htest
        _utest - bool, don't wait_window when running unittest
        """
        Toplevel.__init__(self, parent)
        self.parent = parent
        if _htest:
            parent.instance_dict = {}
        self.wm_withdraw()
        self.configure(borderwidth=5)
        self.title(title or 'IDLE Preferences')
        self.geometry('+%d+%d' % (parent.winfo_rootx() + 20, parent.
            winfo_rooty() + (30 if not _htest else 150)))
        self.themeElements = {'Normal Text': ('normal', '00'),
            'Python Keywords': ('keyword', '01'), 'Python Definitions': (
            'definition', '02'), 'Python Builtins': ('builtin', '03'),
            'Python Comments': ('comment', '04'), 'Python Strings': (
            'string', '05'), 'Selected Text': ('hilite', '06'),
            'Found Text': ('hit', '07'), 'Cursor': ('cursor', '08'),
            'Editor Breakpoint': ('break', '09'), 'Shell Normal Text': (
            'console', '10'), 'Shell Error Text': ('error', '11'),
            'Shell Stdout Text': ('stdout', '12'), 'Shell Stderr Text': (
            'stderr', '13')}
        self.ResetChangedItems()
        self.CreateWidgets()
        self.resizable(height=FALSE, width=FALSE)
        self.transient(parent)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.Cancel)
        self.tabPages.focus_set()
        self.LoadConfigs()
        self.AttachVarCallbacks()
        if not _utest:
            self.wm_deiconify()
            self.wait_window()

    def CreateWidgets(self):
        self.tabPages = TabbedPageSet(self, page_names=['Fonts/Tabs',
            'Highlighting', 'Keys', 'General', 'Extensions'])
        self.tabPages.pack(side=TOP, expand=TRUE, fill=BOTH)
        self.CreatePageFontTab()
        self.CreatePageHighlight()
        self.CreatePageKeys()
        self.CreatePageGeneral()
        self.CreatePageExtensions()
        self.create_action_buttons().pack(side=BOTTOM)

    def create_action_buttons(self):
        if macosx.isAquaTk():
            paddingArgs = {}
        else:
            paddingArgs = {'padx': 6, 'pady': 3}
        outer = Frame(self, pady=2)
        buttons = Frame(outer, pady=2)
        for txt, cmd in (('Ok', self.Ok), ('Apply', self.Apply), ('Cancel',
            self.Cancel), ('Help', self.Help)):
            Button(buttons, text=txt, command=cmd, takefocus=FALSE, **
                paddingArgs).pack(side=LEFT, padx=5)
        Frame(outer, height=2, borderwidth=0).pack(side=TOP)
        buttons.pack(side=BOTTOM)
        return outer

    def CreatePageFontTab(self):
        parent = self.parent
        self.fontSize = StringVar(parent)
        self.fontBold = BooleanVar(parent)
        self.fontName = StringVar(parent)
        self.spaceNum = IntVar(parent)
        self.editFont = tkFont.Font(parent, ('courier', 10, 'normal'))
        frame = self.tabPages.pages['Fonts/Tabs'].frame
        frameFont = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Base Editor Font ')
        frameIndent = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Indentation Width ')
        frameFontName = Frame(frameFont)
        frameFontParam = Frame(frameFont)
        labelFontNameTitle = Label(frameFontName, justify=LEFT, text=
            'Font Face :')
        self.listFontName = Listbox(frameFontName, height=5, takefocus=
            FALSE, exportselection=FALSE)
        self.listFontName.bind('<ButtonRelease-1>', self.
            OnListFontButtonRelease)
        scrollFont = Scrollbar(frameFontName)
        scrollFont.config(command=self.listFontName.yview)
        self.listFontName.config(yscrollcommand=scrollFont.set)
        labelFontSizeTitle = Label(frameFontParam, text='Size :')
        self.optMenuFontSize = DynOptionMenu(frameFontParam, self.fontSize,
            None, command=self.SetFontSample)
        checkFontBold = Checkbutton(frameFontParam, variable=self.fontBold,
            onvalue=1, offvalue=0, text='Bold', command=self.SetFontSample)
        frameFontSample = Frame(frameFont, relief=SOLID, borderwidth=1)
        self.labelFontSample = Label(frameFontSample, justify=LEFT, font=
            self.editFont, text=
            """AaBbCcDdEe
FfGgHhIiJjK
1234567890
#:+=(){}[]""")
        frameIndentSize = Frame(frameIndent)
        labelSpaceNumTitle = Label(frameIndentSize, justify=LEFT, text=
            'Python Standard: 4 Spaces!')
        self.scaleSpaceNum = Scale(frameIndentSize, variable=self.spaceNum,
            orient='horizontal', tickinterval=2, from_=2, to=16)
        frameFont.pack(side=LEFT, padx=5, pady=5, expand=TRUE, fill=BOTH)
        frameIndent.pack(side=LEFT, padx=5, pady=5, fill=Y)
        frameFontName.pack(side=TOP, padx=5, pady=5, fill=X)
        frameFontParam.pack(side=TOP, padx=5, pady=5, fill=X)
        labelFontNameTitle.pack(side=TOP, anchor=W)
        self.listFontName.pack(side=LEFT, expand=TRUE, fill=X)
        scrollFont.pack(side=LEFT, fill=Y)
        labelFontSizeTitle.pack(side=LEFT, anchor=W)
        self.optMenuFontSize.pack(side=LEFT, anchor=W)
        checkFontBold.pack(side=LEFT, anchor=W, padx=20)
        frameFontSample.pack(side=TOP, padx=5, pady=5, expand=TRUE, fill=BOTH)
        self.labelFontSample.pack(expand=TRUE, fill=BOTH)
        frameIndentSize.pack(side=TOP, fill=X)
        labelSpaceNumTitle.pack(side=TOP, anchor=W, padx=5)
        self.scaleSpaceNum.pack(side=TOP, padx=5, fill=X)
        return frame

    def CreatePageHighlight(self):
        parent = self.parent
        self.builtinTheme = StringVar(parent)
        self.customTheme = StringVar(parent)
        self.fgHilite = BooleanVar(parent)
        self.colour = StringVar(parent)
        self.fontName = StringVar(parent)
        self.themeIsBuiltin = BooleanVar(parent)
        self.highlightTarget = StringVar(parent)
        frame = self.tabPages.pages['Highlighting'].frame
        frameCustom = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Custom Highlighting ')
        frameTheme = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Highlighting Theme ')
        self.textHighlightSample = Text(frameCustom, relief=SOLID,
            borderwidth=1, font=('courier', 12, ''), cursor='hand2', width=
            21, height=11, takefocus=FALSE, highlightthickness=0, wrap=NONE)
        text = self.textHighlightSample
        text.bind('<Double-Button-1>', lambda e: 'break')
        text.bind('<B1-Motion>', lambda e: 'break')
        textAndTags = ('#you can click here', 'comment'), ('\n', 'normal'), (
            '#to choose items', 'comment'), ('\n', 'normal'), ('def', 'keyword'
            ), (' ', 'normal'), ('func', 'definition'), ('(param):\n  ',
            'normal'), ('"""string"""', 'string'), ('\n  var0 = ', 'normal'), (
            "'string'", 'string'), ('\n  var1 = ', 'normal'), ("'selected'",
            'hilite'), ('\n  var2 = ', 'normal'), ("'found'", 'hit'), (
            '\n  var3 = ', 'normal'), ('list', 'builtin'), ('(', 'normal'), (
            'None', 'keyword'), (')\n', 'normal'), ('  breakpoint("line")',
            'break'), ('\n\n', 'normal'), (' error ', 'error'), (' ', 'normal'
            ), ('cursor |', 'cursor'), ('\n ', 'normal'), ('shell', 'console'
            ), (' ', 'normal'), ('stdout', 'stdout'), (' ', 'normal'), (
            'stderr', 'stderr'), ('\n', 'normal')
        for txTa in textAndTags:
            text.insert(END, txTa[0], txTa[1])
        for element in self.themeElements:

            def tem(event, elem=element):
                event.widget.winfo_toplevel().highlightTarget.set(elem)
            text.tag_bind(self.themeElements[element][0], '<ButtonPress-1>',
                tem)
        text.config(state=DISABLED)
        self.frameColourSet = Frame(frameCustom, relief=SOLID, borderwidth=1)
        frameFgBg = Frame(frameCustom)
        buttonSetColour = Button(self.frameColourSet, text=
            'Choose Colour for :', command=self.GetColour, highlightthickness=0
            )
        self.optMenuHighlightTarget = DynOptionMenu(self.frameColourSet,
            self.highlightTarget, None, highlightthickness=0)
        self.radioFg = Radiobutton(frameFgBg, variable=self.fgHilite, value
            =1, text='Foreground', command=self.SetColourSampleBinding)
        self.radioBg = Radiobutton(frameFgBg, variable=self.fgHilite, value
            =0, text='Background', command=self.SetColourSampleBinding)
        self.fgHilite.set(1)
        buttonSaveCustomTheme = Button(frameCustom, text=
            'Save as New Custom Theme', command=self.SaveAsNewTheme)
        labelTypeTitle = Label(frameTheme, text='Select : ')
        self.radioThemeBuiltin = Radiobutton(frameTheme, variable=self.
            themeIsBuiltin, value=1, command=self.SetThemeType, text=
            'a Built-in Theme')
        self.radioThemeCustom = Radiobutton(frameTheme, variable=self.
            themeIsBuiltin, value=0, command=self.SetThemeType, text=
            'a Custom Theme')
        self.optMenuThemeBuiltin = DynOptionMenu(frameTheme, self.
            builtinTheme, None, command=None)
        self.optMenuThemeCustom = DynOptionMenu(frameTheme, self.
            customTheme, None, command=None)
        self.buttonDeleteCustomTheme = Button(frameTheme, text=
            'Delete Custom Theme', command=self.DeleteCustomTheme)
        self.new_custom_theme = Label(frameTheme, bd=2)
        frameCustom.pack(side=LEFT, padx=5, pady=5, expand=TRUE, fill=BOTH)
        frameTheme.pack(side=LEFT, padx=5, pady=5, fill=Y)
        self.frameColourSet.pack(side=TOP, padx=5, pady=5, expand=TRUE, fill=X)
        frameFgBg.pack(side=TOP, padx=5, pady=0)
        self.textHighlightSample.pack(side=TOP, padx=5, pady=5, expand=TRUE,
            fill=BOTH)
        buttonSetColour.pack(side=TOP, expand=TRUE, fill=X, padx=8, pady=4)
        self.optMenuHighlightTarget.pack(side=TOP, expand=TRUE, fill=X,
            padx=8, pady=3)
        self.radioFg.pack(side=LEFT, anchor=E)
        self.radioBg.pack(side=RIGHT, anchor=W)
        buttonSaveCustomTheme.pack(side=BOTTOM, fill=X, padx=5, pady=5)
        labelTypeTitle.pack(side=TOP, anchor=W, padx=5, pady=5)
        self.radioThemeBuiltin.pack(side=TOP, anchor=W, padx=5)
        self.radioThemeCustom.pack(side=TOP, anchor=W, padx=5, pady=2)
        self.optMenuThemeBuiltin.pack(side=TOP, fill=X, padx=5, pady=5)
        self.optMenuThemeCustom.pack(side=TOP, fill=X, anchor=W, padx=5, pady=5
            )
        self.buttonDeleteCustomTheme.pack(side=TOP, fill=X, padx=5, pady=5)
        self.new_custom_theme.pack(side=TOP, fill=X, pady=5)
        return frame

    def CreatePageKeys(self):
        parent = self.parent
        self.bindingTarget = StringVar(parent)
        self.builtinKeys = StringVar(parent)
        self.customKeys = StringVar(parent)
        self.keysAreBuiltin = BooleanVar(parent)
        self.keyBinding = StringVar(parent)
        frame = self.tabPages.pages['Keys'].frame
        frameCustom = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Custom Key Bindings ')
        frameKeySets = LabelFrame(frame, borderwidth=2, relief=GROOVE, text
            =' Key Set ')
        frameTarget = Frame(frameCustom)
        labelTargetTitle = Label(frameTarget, text='Action - Key(s)')
        scrollTargetY = Scrollbar(frameTarget)
        scrollTargetX = Scrollbar(frameTarget, orient=HORIZONTAL)
        self.listBindings = Listbox(frameTarget, takefocus=FALSE,
            exportselection=FALSE)
        self.listBindings.bind('<ButtonRelease-1>', self.KeyBindingSelected)
        scrollTargetY.config(command=self.listBindings.yview)
        scrollTargetX.config(command=self.listBindings.xview)
        self.listBindings.config(yscrollcommand=scrollTargetY.set)
        self.listBindings.config(xscrollcommand=scrollTargetX.set)
        self.buttonNewKeys = Button(frameCustom, text=
            'Get New Keys for Selection', command=self.GetNewKeys, state=
            DISABLED)
        frames = [Frame(frameKeySets, padx=2, pady=2, borderwidth=0) for i in
            range(2)]
        self.radioKeysBuiltin = Radiobutton(frames[0], variable=self.
            keysAreBuiltin, value=1, command=self.SetKeysType, text=
            'Use a Built-in Key Set')
        self.radioKeysCustom = Radiobutton(frames[0], variable=self.
            keysAreBuiltin, value=0, command=self.SetKeysType, text=
            'Use a Custom Key Set')
        self.optMenuKeysBuiltin = DynOptionMenu(frames[0], self.builtinKeys,
            None, command=None)
        self.optMenuKeysCustom = DynOptionMenu(frames[0], self.customKeys,
            None, command=None)
        self.buttonDeleteCustomKeys = Button(frames[1], text=
            'Delete Custom Key Set', command=self.DeleteCustomKeys)
        buttonSaveCustomKeys = Button(frames[1], text=
            'Save as New Custom Key Set', command=self.SaveAsNewKeySet)
        self.new_custom_keys = Label(frames[0], bd=2)
        frameCustom.pack(side=BOTTOM, padx=5, pady=5, expand=TRUE, fill=BOTH)
        frameKeySets.pack(side=BOTTOM, padx=5, pady=5, fill=BOTH)
        self.buttonNewKeys.pack(side=BOTTOM, fill=X, padx=5, pady=5)
        frameTarget.pack(side=LEFT, padx=5, pady=5, expand=TRUE, fill=BOTH)
        frameTarget.columnconfigure(0, weight=1)
        frameTarget.rowconfigure(1, weight=1)
        labelTargetTitle.grid(row=0, column=0, columnspan=2, sticky=W)
        self.listBindings.grid(row=1, column=0, sticky=NSEW)
        scrollTargetY.grid(row=1, column=1, sticky=NS)
        scrollTargetX.grid(row=2, column=0, sticky=EW)
        self.radioKeysBuiltin.grid(row=0, column=0, sticky=W + NS)
        self.radioKeysCustom.grid(row=1, column=0, sticky=W + NS)
        self.optMenuKeysBuiltin.grid(row=0, column=1, sticky=NSEW)
        self.optMenuKeysCustom.grid(row=1, column=1, sticky=NSEW)
        self.new_custom_keys.grid(row=0, column=2, sticky=NSEW, padx=5, pady=5)
        self.buttonDeleteCustomKeys.pack(side=LEFT, fill=X, expand=True, padx=2
            )
        buttonSaveCustomKeys.pack(side=LEFT, fill=X, expand=True, padx=2)
        frames[0].pack(side=TOP, fill=BOTH, expand=True)
        frames[1].pack(side=TOP, fill=X, expand=True, pady=2)
        return frame

    def CreatePageGeneral(self):
        parent = self.parent
        self.winWidth = StringVar(parent)
        self.winHeight = StringVar(parent)
        self.startupEdit = IntVar(parent)
        self.autoSave = IntVar(parent)
        self.encoding = StringVar(parent)
        self.userHelpBrowser = BooleanVar(parent)
        self.helpBrowser = StringVar(parent)
        frame = self.tabPages.pages['General'].frame
        frameRun = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Startup Preferences ')
        frameSave = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Autosave Preferences ')
        frameWinSize = Frame(frame, borderwidth=2, relief=GROOVE)
        frameHelp = LabelFrame(frame, borderwidth=2, relief=GROOVE, text=
            ' Additional Help Sources ')
        labelRunChoiceTitle = Label(frameRun, text='At Startup')
        self.radioStartupEdit = Radiobutton(frameRun, variable=self.
            startupEdit, value=1, text='Open Edit Window')
        self.radioStartupShell = Radiobutton(frameRun, variable=self.
            startupEdit, value=0, text='Open Shell Window')
        labelRunSaveTitle = Label(frameSave, text='At Start of Run (F5)  ')
        self.radioSaveAsk = Radiobutton(frameSave, variable=self.autoSave,
            value=0, text='Prompt to Save')
        self.radioSaveAuto = Radiobutton(frameSave, variable=self.autoSave,
            value=1, text='No Prompt')
        labelWinSizeTitle = Label(frameWinSize, text=
            'Initial Window Size  (in characters)')
        labelWinWidthTitle = Label(frameWinSize, text='Width')
        self.entryWinWidth = Entry(frameWinSize, textvariable=self.winWidth,
            width=3)
        labelWinHeightTitle = Label(frameWinSize, text='Height')
        self.entryWinHeight = Entry(frameWinSize, textvariable=self.
            winHeight, width=3)
        frameHelpList = Frame(frameHelp)
        frameHelpListButtons = Frame(frameHelpList)
        scrollHelpList = Scrollbar(frameHelpList)
        self.listHelp = Listbox(frameHelpList, height=5, takefocus=FALSE,
            exportselection=FALSE)
        scrollHelpList.config(command=self.listHelp.yview)
        self.listHelp.config(yscrollcommand=scrollHelpList.set)
        self.listHelp.bind('<ButtonRelease-1>', self.HelpSourceSelected)
        self.buttonHelpListEdit = Button(frameHelpListButtons, text='Edit',
            state=DISABLED, width=8, command=self.HelpListItemEdit)
        self.buttonHelpListAdd = Button(frameHelpListButtons, text='Add',
            width=8, command=self.HelpListItemAdd)
        self.buttonHelpListRemove = Button(frameHelpListButtons, text=
            'Remove', state=DISABLED, width=8, command=self.HelpListItemRemove)
        frameRun.pack(side=TOP, padx=5, pady=5, fill=X)
        frameSave.pack(side=TOP, padx=5, pady=5, fill=X)
        frameWinSize.pack(side=TOP, padx=5, pady=5, fill=X)
        frameHelp.pack(side=TOP, padx=5, pady=5, expand=TRUE, fill=BOTH)
        labelRunChoiceTitle.pack(side=LEFT, anchor=W, padx=5, pady=5)
        self.radioStartupShell.pack(side=RIGHT, anchor=W, padx=5, pady=5)
        self.radioStartupEdit.pack(side=RIGHT, anchor=W, padx=5, pady=5)
        labelRunSaveTitle.pack(side=LEFT, anchor=W, padx=5, pady=5)
        self.radioSaveAuto.pack(side=RIGHT, anchor=W, padx=5, pady=5)
        self.radioSaveAsk.pack(side=RIGHT, anchor=W, padx=5, pady=5)
        labelWinSizeTitle.pack(side=LEFT, anchor=W, padx=5, pady=5)
        self.entryWinHeight.pack(side=RIGHT, anchor=E, padx=10, pady=5)
        labelWinHeightTitle.pack(side=RIGHT, anchor=E, pady=5)
        self.entryWinWidth.pack(side=RIGHT, anchor=E, padx=10, pady=5)
        labelWinWidthTitle.pack(side=RIGHT, anchor=E, pady=5)
        frameHelpListButtons.pack(side=RIGHT, padx=5, pady=5, fill=Y)
        frameHelpList.pack(side=TOP, padx=5, pady=5, expand=TRUE, fill=BOTH)
        scrollHelpList.pack(side=RIGHT, anchor=W, fill=Y)
        self.listHelp.pack(side=LEFT, anchor=E, expand=TRUE, fill=BOTH)
        self.buttonHelpListEdit.pack(side=TOP, anchor=W, pady=5)
        self.buttonHelpListAdd.pack(side=TOP, anchor=W)
        self.buttonHelpListRemove.pack(side=TOP, anchor=W, pady=5)
        return frame

    def AttachVarCallbacks(self):
        self.fontSize.trace_add('write', self.VarChanged_font)
        self.fontName.trace_add('write', self.VarChanged_font)
        self.fontBold.trace_add('write', self.VarChanged_font)
        self.spaceNum.trace_add('write', self.VarChanged_spaceNum)
        self.colour.trace_add('write', self.VarChanged_colour)
        self.builtinTheme.trace_add('write', self.VarChanged_builtinTheme)
        self.customTheme.trace_add('write', self.VarChanged_customTheme)
        self.themeIsBuiltin.trace_add('write', self.VarChanged_themeIsBuiltin)
        self.highlightTarget.trace_add('write', self.VarChanged_highlightTarget
            )
        self.keyBinding.trace_add('write', self.VarChanged_keyBinding)
        self.builtinKeys.trace_add('write', self.VarChanged_builtinKeys)
        self.customKeys.trace_add('write', self.VarChanged_customKeys)
        self.keysAreBuiltin.trace_add('write', self.VarChanged_keysAreBuiltin)
        self.winWidth.trace_add('write', self.VarChanged_winWidth)
        self.winHeight.trace_add('write', self.VarChanged_winHeight)
        self.startupEdit.trace_add('write', self.VarChanged_startupEdit)
        self.autoSave.trace_add('write', self.VarChanged_autoSave)
        self.encoding.trace_add('write', self.VarChanged_encoding)

    def remove_var_callbacks(self):
        """Remove callbacks to prevent memory leaks."""
        for var in (self.fontSize, self.fontName, self.fontBold, self.
            spaceNum, self.colour, self.builtinTheme, self.customTheme,
            self.themeIsBuiltin, self.highlightTarget, self.keyBinding,
            self.builtinKeys, self.customKeys, self.keysAreBuiltin, self.
            winWidth, self.winHeight, self.startupEdit, self.autoSave, self
            .encoding):
            var.trace_remove('write', var.trace_info()[0][1])

    def VarChanged_font(self, *params):
        """When one font attribute changes, save them all, as they are
        not independent from each other. In particular, when we are
        overriding the default font, we need to write out everything.
        """
        value = self.fontName.get()
        self.AddChangedItem('main', 'EditorWindow', 'font', value)
        value = self.fontSize.get()
        self.AddChangedItem('main', 'EditorWindow', 'font-size', value)
        value = self.fontBold.get()
        self.AddChangedItem('main', 'EditorWindow', 'font-bold', value)

    def VarChanged_spaceNum(self, *params):
        value = self.spaceNum.get()
        self.AddChangedItem('main', 'Indent', 'num-spaces', value)

    def VarChanged_colour(self, *params):
        self.OnNewColourSet()

    def VarChanged_builtinTheme(self, *params):
        oldthemes = 'IDLE Classic', 'IDLE New'
        value = self.builtinTheme.get()
        if value not in oldthemes:
            if idleConf.GetOption('main', 'Theme', 'name') not in oldthemes:
                self.AddChangedItem('main', 'Theme', 'name', oldthemes[0])
            self.AddChangedItem('main', 'Theme', 'name2', value)
            self.new_custom_theme.config(text='New theme, see Help', fg=
                '#500000')
        else:
            self.AddChangedItem('main', 'Theme', 'name', value)
            self.AddChangedItem('main', 'Theme', 'name2', '')
            self.new_custom_theme.config(text='', fg='black')
        self.PaintThemeSample()

    def VarChanged_customTheme(self, *params):
        value = self.customTheme.get()
        if value != '- no custom themes -':
            self.AddChangedItem('main', 'Theme', 'name', value)
            self.PaintThemeSample()

    def VarChanged_themeIsBuiltin(self, *params):
        value = self.themeIsBuiltin.get()
        self.AddChangedItem('main', 'Theme', 'default', value)
        if value:
            self.VarChanged_builtinTheme()
        else:
            self.VarChanged_customTheme()

    def VarChanged_highlightTarget(self, *params):
        self.SetHighlightTarget()

    def VarChanged_keyBinding(self, *params):
        value = self.keyBinding.get()
        keySet = self.customKeys.get()
        event = self.listBindings.get(ANCHOR).split()[0]
        if idleConf.IsCoreBinding(event):
            self.AddChangedItem('keys', keySet, event, value)
        else:
            extName = idleConf.GetExtnNameForEvent(event)
            extKeybindSection = extName + '_cfgBindings'
            self.AddChangedItem('extensions', extKeybindSection, event, value)

    def VarChanged_builtinKeys(self, *params):
        oldkeys = ('IDLE Classic Windows', 'IDLE Classic Unix',
            'IDLE Classic Mac', 'IDLE Classic OSX')
        value = self.builtinKeys.get()
        if value not in oldkeys:
            if idleConf.GetOption('main', 'Keys', 'name') not in oldkeys:
                self.AddChangedItem('main', 'Keys', 'name', oldkeys[0])
            self.AddChangedItem('main', 'Keys', 'name2', value)
            self.new_custom_keys.config(text='New key set, see Help', fg=
                '#500000')
        else:
            self.AddChangedItem('main', 'Keys', 'name', value)
            self.AddChangedItem('main', 'Keys', 'name2', '')
            self.new_custom_keys.config(text='', fg='black')
        self.LoadKeysList(value)

    def VarChanged_customKeys(self, *params):
        value = self.customKeys.get()
        if value != '- no custom keys -':
            self.AddChangedItem('main', 'Keys', 'name', value)
            self.LoadKeysList(value)

    def VarChanged_keysAreBuiltin(self, *params):
        value = self.keysAreBuiltin.get()
        self.AddChangedItem('main', 'Keys', 'default', value)
        if value:
            self.VarChanged_builtinKeys()
        else:
            self.VarChanged_customKeys()

    def VarChanged_winWidth(self, *params):
        value = self.winWidth.get()
        self.AddChangedItem('main', 'EditorWindow', 'width', value)

    def VarChanged_winHeight(self, *params):
        value = self.winHeight.get()
        self.AddChangedItem('main', 'EditorWindow', 'height', value)

    def VarChanged_startupEdit(self, *params):
        value = self.startupEdit.get()
        self.AddChangedItem('main', 'General', 'editor-on-startup', value)

    def VarChanged_autoSave(self, *params):
        value = self.autoSave.get()
        self.AddChangedItem('main', 'General', 'autosave', value)

    def VarChanged_encoding(self, *params):
        value = self.encoding.get()
        self.AddChangedItem('main', 'EditorWindow', 'encoding', value)

    def ResetChangedItems(self):
        self.changedItems = {'main': {}, 'highlight': {}, 'keys': {},
            'extensions': {}}

    def AddChangedItem(self, typ, section, item, value):
        value = str(value)
        if section not in self.changedItems[typ]:
            self.changedItems[typ][section] = {}
        self.changedItems[typ][section][item] = value

    def GetDefaultItems(self):
        dItems = {'main': {}, 'highlight': {}, 'keys': {}, 'extensions': {}}
        for configType in dItems:
            sections = idleConf.GetSectionList('default', configType)
            for section in sections:
                dItems[configType][section] = {}
                options = idleConf.defaultCfg[configType].GetOptionList(section
                    )
                for option in options:
                    dItems[configType][section][option] = idleConf.defaultCfg[
                        configType].Get(section, option)
        return dItems

    def SetThemeType(self):
        if self.themeIsBuiltin.get():
            self.optMenuThemeBuiltin.config(state=NORMAL)
            self.optMenuThemeCustom.config(state=DISABLED)
            self.buttonDeleteCustomTheme.config(state=DISABLED)
        else:
            self.optMenuThemeBuiltin.config(state=DISABLED)
            self.radioThemeCustom.config(state=NORMAL)
            self.optMenuThemeCustom.config(state=NORMAL)
            self.buttonDeleteCustomTheme.config(state=NORMAL)

    def SetKeysType(self):
        if self.keysAreBuiltin.get():
            self.optMenuKeysBuiltin.config(state=NORMAL)
            self.optMenuKeysCustom.config(state=DISABLED)
            self.buttonDeleteCustomKeys.config(state=DISABLED)
        else:
            self.optMenuKeysBuiltin.config(state=DISABLED)
            self.radioKeysCustom.config(state=NORMAL)
            self.optMenuKeysCustom.config(state=NORMAL)
            self.buttonDeleteCustomKeys.config(state=NORMAL)

    def GetNewKeys(self):
        listIndex = self.listBindings.index(ANCHOR)
        binding = self.listBindings.get(listIndex)
        bindName = binding.split()[0]
        if self.keysAreBuiltin.get():
            currentKeySetName = self.builtinKeys.get()
        else:
            currentKeySetName = self.customKeys.get()
        currentBindings = idleConf.GetCurrentKeySet()
        if currentKeySetName in self.changedItems['keys']:
            keySetChanges = self.changedItems['keys'][currentKeySetName]
            for event in keySetChanges:
                currentBindings[event] = keySetChanges[event].split()
        currentKeySequences = list(currentBindings.values())
        newKeys = GetKeysDialog(self, 'Get New Keys', bindName,
            currentKeySequences).result
        if newKeys:
            if self.keysAreBuiltin.get():
                message = (
                    'Your changes will be saved as a new Custom Key Set. Enter a name for your new Custom Key Set below.'
                    )
                newKeySet = self.GetNewKeysName(message)
                if not newKeySet:
                    self.listBindings.select_set(listIndex)
                    self.listBindings.select_anchor(listIndex)
                    return
                else:
                    self.CreateNewKeySet(newKeySet)
            self.listBindings.delete(listIndex)
            self.listBindings.insert(listIndex, bindName + ' - ' + newKeys)
            self.listBindings.select_set(listIndex)
            self.listBindings.select_anchor(listIndex)
            self.keyBinding.set(newKeys)
        else:
            self.listBindings.select_set(listIndex)
            self.listBindings.select_anchor(listIndex)

    def GetNewKeysName(self, message):
        usedNames = idleConf.GetSectionList('user', 'keys'
            ) + idleConf.GetSectionList('default', 'keys')
        newKeySet = SectionName(self, 'New Custom Key Set', message, usedNames
            ).result
        return newKeySet

    def SaveAsNewKeySet(self):
        newKeysName = self.GetNewKeysName('New Key Set Name:')
        if newKeysName:
            self.CreateNewKeySet(newKeysName)

    def KeyBindingSelected(self, event):
        self.buttonNewKeys.config(state=NORMAL)

    def CreateNewKeySet(self, newKeySetName):
        if self.keysAreBuiltin.get():
            prevKeySetName = self.builtinKeys.get()
        else:
            prevKeySetName = self.customKeys.get()
        prevKeys = idleConf.GetCoreKeys(prevKeySetName)
        newKeys = {}
        for event in prevKeys:
            eventName = event[2:-2]
            binding = ' '.join(prevKeys[event])
            newKeys[eventName] = binding
        if prevKeySetName in self.changedItems['keys']:
            keySetChanges = self.changedItems['keys'][prevKeySetName]
            for event in keySetChanges:
                newKeys[event] = keySetChanges[event]
        self.SaveNewKeySet(newKeySetName, newKeys)
        customKeyList = idleConf.GetSectionList('user', 'keys')
        customKeyList.sort()
        self.optMenuKeysCustom.SetMenu(customKeyList, newKeySetName)
        self.keysAreBuiltin.set(0)
        self.SetKeysType()

    def LoadKeysList(self, keySetName):
        reselect = 0
        newKeySet = 0
        if self.listBindings.curselection():
            reselect = 1
            listIndex = self.listBindings.index(ANCHOR)
        keySet = idleConf.GetKeySet(keySetName)
        bindNames = list(keySet.keys())
        bindNames.sort()
        self.listBindings.delete(0, END)
        for bindName in bindNames:
            key = ' '.join(keySet[bindName])
            bindName = bindName[2:-2]
            if keySetName in self.changedItems['keys']:
                if bindName in self.changedItems['keys'][keySetName]:
                    key = self.changedItems['keys'][keySetName][bindName]
            self.listBindings.insert(END, bindName + ' - ' + key)
        if reselect:
            self.listBindings.see(listIndex)
            self.listBindings.select_set(listIndex)
            self.listBindings.select_anchor(listIndex)

    def DeleteCustomKeys(self):
        keySetName = self.customKeys.get()
        delmsg = 'Are you sure you wish to delete the key set %r ?'
        if not tkMessageBox.askyesno('Delete Key Set', delmsg % keySetName,
            parent=self):
            return
        self.DeactivateCurrentConfig()
        idleConf.userCfg['keys'].remove_section(keySetName)
        if keySetName in self.changedItems['keys']:
            del self.changedItems['keys'][keySetName]
        idleConf.userCfg['keys'].Save()
        itemList = idleConf.GetSectionList('user', 'keys')
        itemList.sort()
        if not itemList:
            self.radioKeysCustom.config(state=DISABLED)
            self.optMenuKeysCustom.SetMenu(itemList, '- no custom keys -')
        else:
            self.optMenuKeysCustom.SetMenu(itemList, itemList[0])
        self.keysAreBuiltin.set(idleConf.defaultCfg['main'].Get('Keys',
            'default'))
        self.builtinKeys.set(idleConf.defaultCfg['main'].Get('Keys', 'name'
            ) or idleConf.default_keys())
        self.SaveAllChangedConfigs()
        self.ActivateConfigChanges()
        self.SetKeysType()

    def DeleteCustomTheme(self):
        themeName = self.customTheme.get()
        delmsg = 'Are you sure you wish to delete the theme %r ?'
        if not tkMessageBox.askyesno('Delete Theme', delmsg % themeName,
            parent=self):
            return
        self.DeactivateCurrentConfig()
        idleConf.userCfg['highlight'].remove_section(themeName)
        if themeName in self.changedItems['highlight']:
            del self.changedItems['highlight'][themeName]
        idleConf.userCfg['highlight'].Save()
        itemList = idleConf.GetSectionList('user', 'highlight')
        itemList.sort()
        if not itemList:
            self.radioThemeCustom.config(state=DISABLED)
            self.optMenuThemeCustom.SetMenu(itemList, '- no custom themes -')
        else:
            self.optMenuThemeCustom.SetMenu(itemList, itemList[0])
        self.themeIsBuiltin.set(idleConf.defaultCfg['main'].Get('Theme',
            'default'))
        self.builtinTheme.set(idleConf.defaultCfg['main'].Get('Theme', 'name'))
        self.SaveAllChangedConfigs()
        self.ActivateConfigChanges()
        self.SetThemeType()

    def GetColour(self):
        target = self.highlightTarget.get()
        prevColour = self.frameColourSet.cget('bg')
        rgbTuplet, colourString = tkColorChooser.askcolor(parent=self,
            title='Pick new colour for : ' + target, initialcolor=prevColour)
        if colourString and colourString != prevColour:
            if self.themeIsBuiltin.get():
                message = (
                    'Your changes will be saved as a new Custom Theme. Enter a name for your new Custom Theme below.'
                    )
                newTheme = self.GetNewThemeName(message)
                if not newTheme:
                    return
                else:
                    self.CreateNewTheme(newTheme)
                    self.colour.set(colourString)
            else:
                self.colour.set(colourString)

    def OnNewColourSet(self):
        newColour = self.colour.get()
        self.frameColourSet.config(bg=newColour)
        plane = 'foreground' if self.fgHilite.get() else 'background'
        sampleElement = self.themeElements[self.highlightTarget.get()][0]
        self.textHighlightSample.tag_config(sampleElement, **{plane: newColour}
            )
        theme = self.customTheme.get()
        themeElement = sampleElement + '-' + plane
        self.AddChangedItem('highlight', theme, themeElement, newColour)

    def GetNewThemeName(self, message):
        usedNames = idleConf.GetSectionList('user', 'highlight'
            ) + idleConf.GetSectionList('default', 'highlight')
        newTheme = SectionName(self, 'New Custom Theme', message, usedNames
            ).result
        return newTheme

    def SaveAsNewTheme(self):
        newThemeName = self.GetNewThemeName('New Theme Name:')
        if newThemeName:
            self.CreateNewTheme(newThemeName)

    def CreateNewTheme(self, newThemeName):
        if self.themeIsBuiltin.get():
            themeType = 'default'
            themeName = self.builtinTheme.get()
        else:
            themeType = 'user'
            themeName = self.customTheme.get()
        newTheme = idleConf.GetThemeDict(themeType, themeName)
        if themeName in self.changedItems['highlight']:
            themeChanges = self.changedItems['highlight'][themeName]
            for element in themeChanges:
                newTheme[element] = themeChanges[element]
        self.SaveNewTheme(newThemeName, newTheme)
        customThemeList = idleConf.GetSectionList('user', 'highlight')
        customThemeList.sort()
        self.optMenuThemeCustom.SetMenu(customThemeList, newThemeName)
        self.themeIsBuiltin.set(0)
        self.SetThemeType()

    def OnListFontButtonRelease(self, event):
        font = self.listFontName.get(ANCHOR)
        self.fontName.set(font.lower())
        self.SetFontSample()

    def SetFontSample(self, event=None):
        fontName = self.fontName.get()
        fontWeight = tkFont.BOLD if self.fontBold.get() else tkFont.NORMAL
        newFont = fontName, self.fontSize.get(), fontWeight
        self.labelFontSample.config(font=newFont)
        self.textHighlightSample.configure(font=newFont)

    def SetHighlightTarget(self):
        if self.highlightTarget.get() == 'Cursor':
            self.radioFg.config(state=DISABLED)
            self.radioBg.config(state=DISABLED)
            self.fgHilite.set(1)
        else:
            self.radioFg.config(state=NORMAL)
            self.radioBg.config(state=NORMAL)
            self.fgHilite.set(1)
        self.SetColourSample()

    def SetColourSampleBinding(self, *args):
        self.SetColourSample()

    def SetColourSample(self):
        tag = self.themeElements[self.highlightTarget.get()][0]
        plane = 'foreground' if self.fgHilite.get() else 'background'
        colour = self.textHighlightSample.tag_cget(tag, plane)
        self.frameColourSet.config(bg=colour)

    def PaintThemeSample(self):
        if self.themeIsBuiltin.get():
            theme = self.builtinTheme.get()
        else:
            theme = self.customTheme.get()
        for elementTitle in self.themeElements:
            element = self.themeElements[elementTitle][0]
            colours = idleConf.GetHighlight(theme, element)
            if element == 'cursor':
                colours['background'] = idleConf.GetHighlight(theme,
                    'normal', fgBg='bg')
            if theme in self.changedItems['highlight']:
                themeDict = self.changedItems['highlight'][theme]
                if element + '-foreground' in themeDict:
                    colours['foreground'] = themeDict[element + '-foreground']
                if element + '-background' in themeDict:
                    colours['background'] = themeDict[element + '-background']
            self.textHighlightSample.tag_config(element, **colours)
        self.SetColourSample()

    def HelpSourceSelected(self, event):
        self.SetHelpListButtonStates()

    def SetHelpListButtonStates(self):
        if self.listHelp.size() < 1:
            self.buttonHelpListEdit.config(state=DISABLED)
            self.buttonHelpListRemove.config(state=DISABLED)
        elif self.listHelp.curselection():
            self.buttonHelpListEdit.config(state=NORMAL)
            self.buttonHelpListRemove.config(state=NORMAL)
        else:
            self.buttonHelpListEdit.config(state=DISABLED)
            self.buttonHelpListRemove.config(state=DISABLED)

    def HelpListItemAdd(self):
        helpSource = HelpSource(self, 'New Help Source').result
        if helpSource:
            self.userHelpList.append((helpSource[0], helpSource[1]))
            self.listHelp.insert(END, helpSource[0])
            self.UpdateUserHelpChangedItems()
        self.SetHelpListButtonStates()

    def HelpListItemEdit(self):
        itemIndex = self.listHelp.index(ANCHOR)
        helpSource = self.userHelpList[itemIndex]
        newHelpSource = HelpSource(self, 'Edit Help Source', menuitem=
            helpSource[0], filepath=helpSource[1]).result
        if newHelpSource and newHelpSource != helpSource:
            self.userHelpList[itemIndex] = newHelpSource
            self.listHelp.delete(itemIndex)
            self.listHelp.insert(itemIndex, newHelpSource[0])
            self.UpdateUserHelpChangedItems()
            self.SetHelpListButtonStates()

    def HelpListItemRemove(self):
        itemIndex = self.listHelp.index(ANCHOR)
        del self.userHelpList[itemIndex]
        self.listHelp.delete(itemIndex)
        self.UpdateUserHelpChangedItems()
        self.SetHelpListButtonStates()

    def UpdateUserHelpChangedItems(self):
        """Clear and rebuild the HelpFiles section in self.changedItems"""
        self.changedItems['main']['HelpFiles'] = {}
        for num in range(1, len(self.userHelpList) + 1):
            self.AddChangedItem('main', 'HelpFiles', str(num), ';'.join(
                self.userHelpList[num - 1][:2]))

    def LoadFontCfg(self):
        fonts = list(tkFont.families(self))
        fonts.sort()
        for font in fonts:
            self.listFontName.insert(END, font)
        configuredFont = idleConf.GetFont(self, 'main', 'EditorWindow')
        fontName = configuredFont[0].lower()
        fontSize = configuredFont[1]
        fontBold = configuredFont[2] == 'bold'
        self.fontName.set(fontName)
        lc_fonts = [s.lower() for s in fonts]
        try:
            currentFontIndex = lc_fonts.index(fontName)
            self.listFontName.see(currentFontIndex)
            self.listFontName.select_set(currentFontIndex)
            self.listFontName.select_anchor(currentFontIndex)
        except ValueError:
            pass
        self.optMenuFontSize.SetMenu(('7', '8', '9', '10', '11', '12', '13',
            '14', '16', '18', '20', '22', '25', '29', '34', '40'), fontSize)
        self.fontBold.set(fontBold)
        self.SetFontSample()

    def LoadTabCfg(self):
        spaceNum = idleConf.GetOption('main', 'Indent', 'num-spaces',
            default=4, type='int')
        self.spaceNum.set(spaceNum)

    def LoadThemeCfg(self):
        self.themeIsBuiltin.set(idleConf.GetOption('main', 'Theme',
            'default', type='bool', default=1))
        currentOption = idleConf.CurrentTheme()
        if self.themeIsBuiltin.get():
            itemList = idleConf.GetSectionList('default', 'highlight')
            itemList.sort()
            self.optMenuThemeBuiltin.SetMenu(itemList, currentOption)
            itemList = idleConf.GetSectionList('user', 'highlight')
            itemList.sort()
            if not itemList:
                self.radioThemeCustom.config(state=DISABLED)
                self.customTheme.set('- no custom themes -')
            else:
                self.optMenuThemeCustom.SetMenu(itemList, itemList[0])
        else:
            itemList = idleConf.GetSectionList('user', 'highlight')
            itemList.sort()
            self.optMenuThemeCustom.SetMenu(itemList, currentOption)
            itemList = idleConf.GetSectionList('default', 'highlight')
            itemList.sort()
            self.optMenuThemeBuiltin.SetMenu(itemList, itemList[0])
        self.SetThemeType()
        themeNames = list(self.themeElements.keys())
        themeNames.sort(key=lambda x: self.themeElements[x][1])
        self.optMenuHighlightTarget.SetMenu(themeNames, themeNames[0])
        self.PaintThemeSample()
        self.SetHighlightTarget()

    def LoadKeyCfg(self):
        self.keysAreBuiltin.set(idleConf.GetOption('main', 'Keys',
            'default', type='bool', default=1))
        currentOption = idleConf.CurrentKeys()
        if self.keysAreBuiltin.get():
            itemList = idleConf.GetSectionList('default', 'keys')
            itemList.sort()
            self.optMenuKeysBuiltin.SetMenu(itemList, currentOption)
            itemList = idleConf.GetSectionList('user', 'keys')
            itemList.sort()
            if not itemList:
                self.radioKeysCustom.config(state=DISABLED)
                self.customKeys.set('- no custom keys -')
            else:
                self.optMenuKeysCustom.SetMenu(itemList, itemList[0])
        else:
            itemList = idleConf.GetSectionList('user', 'keys')
            itemList.sort()
            self.optMenuKeysCustom.SetMenu(itemList, currentOption)
            itemList = idleConf.GetSectionList('default', 'keys')
            itemList.sort()
            self.optMenuKeysBuiltin.SetMenu(itemList, idleConf.default_keys())
        self.SetKeysType()
        keySetName = idleConf.CurrentKeys()
        self.LoadKeysList(keySetName)

    def LoadGeneralCfg(self):
        self.startupEdit.set(idleConf.GetOption('main', 'General',
            'editor-on-startup', default=1, type='bool'))
        self.autoSave.set(idleConf.GetOption('main', 'General', 'autosave',
            default=0, type='bool'))
        self.winWidth.set(idleConf.GetOption('main', 'EditorWindow',
            'width', type='int'))
        self.winHeight.set(idleConf.GetOption('main', 'EditorWindow',
            'height', type='int'))
        self.encoding.set(idleConf.GetOption('main', 'EditorWindow',
            'encoding', default='none'))
        self.userHelpList = idleConf.GetAllExtraHelpSourcesList()
        for helpItem in self.userHelpList:
            self.listHelp.insert(END, helpItem[0])
        self.SetHelpListButtonStates()

    def LoadConfigs(self):
        """
        load configuration from default and user config files and populate
        the widgets on the config dialog pages.
        """
        self.LoadFontCfg()
        self.LoadTabCfg()
        self.LoadThemeCfg()
        self.LoadKeyCfg()
        self.LoadGeneralCfg()

    def SaveNewKeySet(self, keySetName, keySet):
        """
        save a newly created core key set.
        keySetName - string, the name of the new key set
        keySet - dictionary containing the new key set
        """
        if not idleConf.userCfg['keys'].has_section(keySetName):
            idleConf.userCfg['keys'].add_section(keySetName)
        for event in keySet:
            value = keySet[event]
            idleConf.userCfg['keys'].SetOption(keySetName, event, value)

    def SaveNewTheme(self, themeName, theme):
        """
        save a newly created theme.
        themeName - string, the name of the new theme
        theme - dictionary containing the new theme
        """
        if not idleConf.userCfg['highlight'].has_section(themeName):
            idleConf.userCfg['highlight'].add_section(themeName)
        for element in theme:
            value = theme[element]
            idleConf.userCfg['highlight'].SetOption(themeName, element, value)

    def SetUserValue(self, configType, section, item, value):
        if idleConf.defaultCfg[configType].has_option(section, item):
            if idleConf.defaultCfg[configType].Get(section, item) == value:
                return idleConf.userCfg[configType].RemoveOption(section, item)
        return idleConf.userCfg[configType].SetOption(section, item, value)

    def SaveAllChangedConfigs(self):
        """Save configuration changes to the user config file."""
        idleConf.userCfg['main'].Save()
        for configType in self.changedItems:
            cfgTypeHasChanges = False
            for section in self.changedItems[configType]:
                if section == 'HelpFiles':
                    idleConf.userCfg['main'].remove_section('HelpFiles')
                    cfgTypeHasChanges = True
                for item in self.changedItems[configType][section]:
                    value = self.changedItems[configType][section][item]
                    if self.SetUserValue(configType, section, item, value):
                        cfgTypeHasChanges = True
            if cfgTypeHasChanges:
                idleConf.userCfg[configType].Save()
        for configType in ['keys', 'highlight']:
            idleConf.userCfg[configType].Save()
        self.ResetChangedItems()
        self.save_all_changed_extensions()

    def DeactivateCurrentConfig(self):
        winInstances = self.parent.instance_dict.keys()
        for instance in winInstances:
            instance.RemoveKeybindings()

    def ActivateConfigChanges(self):
        """Dynamically apply configuration changes"""
        winInstances = self.parent.instance_dict.keys()
        for instance in winInstances:
            instance.ResetColorizer()
            instance.ResetFont()
            instance.set_notabs_indentwidth()
            instance.ApplyKeybindings()
            instance.reset_help_menu_entries()

    def Cancel(self):
        self.destroy()

    def Ok(self):
        self.Apply()
        self.destroy()

    def Apply(self):
        self.DeactivateCurrentConfig()
        self.SaveAllChangedConfigs()
        self.ActivateConfigChanges()

    def Help(self):
        page = self.tabPages._current_page
        view_text(self, title='Help for IDLE preferences', text=help_common +
            help_pages.get(page, ''))

    def CreatePageExtensions(self):
        """Part of the config dialog used for configuring IDLE extensions.

        This code is generic - it works for any and all IDLE extensions.

        IDLE extensions save their configuration options using idleConf.
        This code reads the current configuration using idleConf, supplies a
        GUI interface to change the configuration values, and saves the
        changes using idleConf.

        Not all changes take effect immediately - some may require restarting IDLE.
        This depends on each extension's implementation.

        All values are treated as text, and it is up to the user to supply
        reasonable values. The only exception to this are the 'enable*' options,
        which are boolean, and can be toggled with a True/False button.
        """
        parent = self.parent
        frame = self.tabPages.pages['Extensions'].frame
        self.ext_defaultCfg = idleConf.defaultCfg['extensions']
        self.ext_userCfg = idleConf.userCfg['extensions']
        self.is_int = self.register(is_int)
        self.load_extensions()
        self.extension_names = StringVar(self)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        self.extension_list = Listbox(frame, listvariable=self.
            extension_names, selectmode='browse')
        self.extension_list.bind('<<ListboxSelect>>', self.extension_selected)
        scroll = Scrollbar(frame, command=self.extension_list.yview)
        self.extension_list.yscrollcommand = scroll.set
        self.details_frame = LabelFrame(frame, width=250, height=250)
        self.extension_list.grid(column=0, row=0, sticky='nws')
        scroll.grid(column=1, row=0, sticky='ns')
        self.details_frame.grid(column=2, row=0, sticky='nsew', padx=[10, 0])
        frame.configure(padx=10, pady=10)
        self.config_frame = {}
        self.current_extension = None
        self.outerframe = self
        self.tabbed_page_set = self.extension_list
        ext_names = ''
        for ext_name in sorted(self.extensions):
            self.create_extension_frame(ext_name)
            ext_names = ext_names + '{' + ext_name + '} '
        self.extension_names.set(ext_names)
        self.extension_list.selection_set(0)
        self.extension_selected(None)

    def load_extensions(self):
        """Fill self.extensions with data from the default and user configs."""
        self.extensions = {}
        for ext_name in idleConf.GetExtensions(active_only=False):
            self.extensions[ext_name] = []
        for ext_name in self.extensions:
            opt_list = sorted(self.ext_defaultCfg.GetOptionList(ext_name))
            enables = [opt_name for opt_name in opt_list if opt_name.
                startswith('enable')]
            for opt_name in enables:
                opt_list.remove(opt_name)
            opt_list = enables + opt_list
            for opt_name in opt_list:
                def_str = self.ext_defaultCfg.Get(ext_name, opt_name, raw=True)
                try:
                    def_obj = {'True': True, 'False': False}[def_str]
                    opt_type = 'bool'
                except KeyError:
                    try:
                        def_obj = int(def_str)
                        opt_type = 'int'
                    except ValueError:
                        def_obj = def_str
                        opt_type = None
                try:
                    value = self.ext_userCfg.Get(ext_name, opt_name, type=
                        opt_type, raw=True, default=def_obj)
                except ValueError:
                    value = def_obj
                var = StringVar(self)
                var.set(str(value))
                self.extensions[ext_name].append({'name': opt_name, 'type':
                    opt_type, 'default': def_str, 'value': value, 'var': var})

    def extension_selected(self, event):
        newsel = self.extension_list.curselection()
        if newsel:
            newsel = self.extension_list.get(newsel)
        if newsel is None or newsel != self.current_extension:
            if self.current_extension:
                self.details_frame.config(text='')
                self.config_frame[self.current_extension].grid_forget()
                self.current_extension = None
        if newsel:
            self.details_frame.config(text=newsel)
            self.config_frame[newsel].grid(column=0, row=0, sticky='nsew')
            self.current_extension = newsel

    def create_extension_frame(self, ext_name):
        """Create a frame holding the widgets to configure one extension"""
        f = VerticalScrolledFrame(self.details_frame, height=250, width=250)
        self.config_frame[ext_name] = f
        entry_area = f.interior
        for row, opt in enumerate(self.extensions[ext_name]):
            label = Label(entry_area, text=opt['name'])
            label.grid(row=row, column=0, sticky=NW)
            var = opt['var']
            if opt['type'] == 'bool':
                Checkbutton(entry_area, textvariable=var, variable=var,
                    onvalue='True', offvalue='False', indicatoron=FALSE,
                    selectcolor='', width=8).grid(row=row, column=1, sticky
                    =W, padx=7)
            elif opt['type'] == 'int':
                Entry(entry_area, textvariable=var, validate='key',
                    validatecommand=(self.is_int, '%P')).grid(row=row,
                    column=1, sticky=NSEW, padx=7)
            else:
                Entry(entry_area, textvariable=var).grid(row=row, column=1,
                    sticky=NSEW, padx=7)
        return

    def set_extension_value(self, section, opt):
        name = opt['name']
        default = opt['default']
        value = opt['var'].get().strip() or default
        opt['var'].set(value)
        if value == default:
            return self.ext_userCfg.RemoveOption(section, name)
        return self.ext_userCfg.SetOption(section, name, value)

    def save_all_changed_extensions(self):
        """Save configuration changes to the user config file."""
        has_changes = False
        for ext_name in self.extensions:
            options = self.extensions[ext_name]
            for opt in options:
                if self.set_extension_value(ext_name, opt):
                    has_changes = True
        if has_changes:
            self.ext_userCfg.Save()


help_common = """When you click either the Apply or Ok buttons, settings in this
dialog that are different from IDLE's default are saved in
a .idlerc directory in your home directory. Except as noted,
these changes apply to all versions of IDLE installed on this
machine. Some do not take affect until IDLE is restarted.
[Cancel] only cancels changes made since the last save.
"""
help_pages = {'Highlighting':
    """
Highlighting:
The IDLE Dark color theme is new in October 2015.  It can only
be used with older IDLE releases if it is saved as a custom
theme, with a different name.
"""
    , 'Keys':
    """
Keys:
The IDLE Modern Unix key set is new in June 2016.  It can only
be used with older IDLE releases if it is saved as a custom
key set, with a different name.
"""
    }


def is_int(s):
    """Return 's is blank or represents an int'"""
    if not s:
        return True
    try:
        int(s)
        return True
    except ValueError:
        return False


class VerticalScrolledFrame(Frame):
    """A pure Tkinter vertically scrollable frame.

    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """

    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=
            vscrollbar.set, width=240)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        def _configure_interior(event):
            size = interior.winfo_reqwidth(), interior.winfo_reqheight()
            canvas.config(scrollregion='0 0 %s %s' % size)
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)
        return


if __name__ == '__main__':
    import unittest
    unittest.main('idlelib.idle_test.test_configdialog', verbosity=2, exit=
        False)
    from idlelib.idle_test.htest import run
    run(ConfigDialog)
