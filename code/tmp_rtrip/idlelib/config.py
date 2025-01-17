"""idlelib.config -- Manage IDLE configuration information.

The comments at the beginning of config-main.def describe the
configuration files and the design implemented to update user
configuration information.  In particular, user configuration choices
which duplicate the defaults will be removed from the user's
configuration files, and if a user file becomes empty, it will be
deleted.

The configuration database maps options to values.  Comceptually, the
database keys are tuples (config-type, section, item).  As implemented,
there are  separate dicts for default and user values.  Each has
config-type keys 'main', 'extensions', 'highlight', and 'keys'.  The
value for each key is a ConfigParser instance that maps section and item
to values.  For 'main' and 'extenstons', user values override
default values.  For 'highlight' and 'keys', user sections augment the
default sections (and must, therefore, have distinct names).

Throughout this module there is an emphasis on returning useable defaults
when a problem occurs in returning a requested configuration value back to
idle. This is to allow IDLE to continue to function in spite of errors in
the retrieval of config information. When a default is returned instead of
a requested config value, a message is printed to stderr to aid in
configuration problem notification and resolution.
"""
from configparser import ConfigParser
import os
import sys
from tkinter.font import Font


class InvalidConfigType(Exception):
    pass


class InvalidConfigSet(Exception):
    pass


class InvalidFgBg(Exception):
    pass


class InvalidTheme(Exception):
    pass


class IdleConfParser(ConfigParser):
    """
    A ConfigParser specialised for idle configuration file handling
    """

    def __init__(self, cfgFile, cfgDefaults=None):
        """
        cfgFile - string, fully specified configuration file name
        """
        self.file = cfgFile
        ConfigParser.__init__(self, defaults=cfgDefaults, strict=False)

    def Get(self, section, option, type=None, default=None, raw=False):
        """
        Get an option value for given section/option or return default.
        If type is specified, return as type.
        """
        if not self.has_option(section, option):
            return default
        if type == 'bool':
            return self.getboolean(section, option)
        elif type == 'int':
            return self.getint(section, option)
        else:
            return self.get(section, option, raw=raw)

    def GetOptionList(self, section):
        """Return a list of options for given section, else []."""
        if self.has_section(section):
            return self.options(section)
        else:
            return []

    def Load(self):
        """Load the configuration file from disk."""
        self.read(self.file)


class IdleUserConfParser(IdleConfParser):
    """
    IdleConfigParser specialised for user configuration handling.
    """

    def AddSection(self, section):
        """If section doesn't exist, add it."""
        if not self.has_section(section):
            self.add_section(section)

    def RemoveEmptySections(self):
        """Remove any sections that have no options."""
        for section in self.sections():
            if not self.GetOptionList(section):
                self.remove_section(section)

    def IsEmpty(self):
        """Return True if no sections after removing empty sections."""
        self.RemoveEmptySections()
        return not self.sections()

    def RemoveOption(self, section, option):
        """Return True if option is removed from section, else False.

        False if either section does not exist or did not have option.
        """
        if self.has_section(section):
            return self.remove_option(section, option)
        return False

    def SetOption(self, section, option, value):
        """Return True if option is added or changed to value, else False.

        Add section if required.  False means option already had value.
        """
        if self.has_option(section, option):
            if self.get(section, option) == value:
                return False
            else:
                self.set(section, option, value)
                return True
        else:
            if not self.has_section(section):
                self.add_section(section)
            self.set(section, option, value)
            return True

    def RemoveFile(self):
        """Remove user config file self.file from disk if it exists."""
        if os.path.exists(self.file):
            os.remove(self.file)

    def Save(self):
        """Update user configuration file.

        Remove empty sections. If resulting config isn't empty, write the file
        to disk. If config is empty, remove the file from disk if it exists.

        """
        if not self.IsEmpty():
            fname = self.file
            try:
                cfgFile = open(fname, 'w')
            except OSError:
                os.unlink(fname)
                cfgFile = open(fname, 'w')
            with cfgFile:
                self.write(cfgFile)
        else:
            self.RemoveFile()


class IdleConf:
    """Hold config parsers for all idle config files in singleton instance.

    Default config files, self.defaultCfg --
        for config_type in self.config_types:
            (idle install dir)/config-{config-type}.def

    User config files, self.userCfg --
        for config_type in self.config_types:
        (user home dir)/.idlerc/config-{config-type}.cfg
    """

    def __init__(self):
        self.config_types = 'main', 'extensions', 'highlight', 'keys'
        self.defaultCfg = {}
        self.userCfg = {}
        self.cfg = {}
        self.CreateConfigHandlers()
        self.LoadCfgFiles()

    def CreateConfigHandlers(self):
        """Populate default and user config parser dictionaries."""
        if __name__ != '__main__':
            idleDir = os.path.dirname(__file__)
        else:
            idleDir = os.path.abspath(sys.path[0])
        userDir = self.GetUserCfgDir()
        defCfgFiles = {}
        usrCfgFiles = {}
        for cfgType in self.config_types:
            defCfgFiles[cfgType] = os.path.join(idleDir, 'config-' +
                cfgType + '.def')
            usrCfgFiles[cfgType] = os.path.join(userDir, 'config-' +
                cfgType + '.cfg')
        for cfgType in self.config_types:
            self.defaultCfg[cfgType] = IdleConfParser(defCfgFiles[cfgType])
            self.userCfg[cfgType] = IdleUserConfParser(usrCfgFiles[cfgType])

    def GetUserCfgDir(self):
        """Return a filesystem directory for storing user config files.

        Creates it if required.
        """
        cfgDir = '.idlerc'
        userDir = os.path.expanduser('~')
        if userDir != '~':
            if not os.path.exists(userDir):
                warn = '\n Warning: os.path.expanduser("~") points to\n ' + userDir + """,
 but the path does not exist."""
                try:
                    print(warn, file=sys.stderr)
                except OSError:
                    pass
                userDir = '~'
        if userDir == '~':
            userDir = os.getcwd()
        userDir = os.path.join(userDir, cfgDir)
        if not os.path.exists(userDir):
            try:
                os.mkdir(userDir)
            except OSError:
                warn = '\n Warning: unable to create user config directory\n' + userDir + """
 Check path and permissions.
 Exiting!
"""
                print(warn, file=sys.stderr)
                raise SystemExit
        return userDir

    def GetOption(self, configType, section, option, default=None, type=
        None, warn_on_default=True, raw=False):
        """Return a value for configType section option, or default.

        If type is not None, return a value of that type.  Also pass raw
        to the config parser.  First try to return a valid value
        (including type) from a user configuration. If that fails, try
        the default configuration. If that fails, return default, with a
        default of None.

        Warn if either user or default configurations have an invalid value.
        Warn if default is returned and warn_on_default is True.
        """
        try:
            if self.userCfg[configType].has_option(section, option):
                return self.userCfg[configType].Get(section, option, type=
                    type, raw=raw)
        except ValueError:
            warning = (
                """
 Warning: config.py - IdleConf.GetOption -
 invalid %r value for configuration option %r
 from section %r: %r"""
                 % (type, option, section, self.userCfg[configType].Get(
                section, option, raw=raw)))
            _warn(warning, configType, section, option)
        try:
            if self.defaultCfg[configType].has_option(section, option):
                return self.defaultCfg[configType].Get(section, option,
                    type=type, raw=raw)
        except ValueError:
            pass
        if warn_on_default:
            warning = (
                """
 Warning: config.py - IdleConf.GetOption -
 problem retrieving configuration option %r
 from section %r.
 returning default value: %r"""
                 % (option, section, default))
            _warn(warning, configType, section, option)
        return default

    def SetOption(self, configType, section, option, value):
        """Set section option to value in user config file."""
        self.userCfg[configType].SetOption(section, option, value)

    def GetSectionList(self, configSet, configType):
        """Return sections for configSet configType configuration.

        configSet must be either 'user' or 'default'
        configType must be in self.config_types.
        """
        if not configType in self.config_types:
            raise InvalidConfigType('Invalid configType specified')
        if configSet == 'user':
            cfgParser = self.userCfg[configType]
        elif configSet == 'default':
            cfgParser = self.defaultCfg[configType]
        else:
            raise InvalidConfigSet('Invalid configSet specified')
        return cfgParser.sections()

    def GetHighlight(self, theme, element, fgBg=None):
        """Return individual theme element highlight color(s).

        fgBg - string ('fg' or 'bg') or None.
        If None, return a dictionary containing fg and bg colors with
        keys 'foreground' and 'background'.  Otherwise, only return
        fg or bg color, as specified.  Colors are intended to be
        appropriate for passing to Tkinter in, e.g., a tag_config call).
        """
        if self.defaultCfg['highlight'].has_section(theme):
            themeDict = self.GetThemeDict('default', theme)
        else:
            themeDict = self.GetThemeDict('user', theme)
        fore = themeDict[element + '-foreground']
        if element == 'cursor':
            back = themeDict['normal-background']
        else:
            back = themeDict[element + '-background']
        highlight = {'foreground': fore, 'background': back}
        if not fgBg:
            return highlight
        else:
            if fgBg == 'fg':
                return highlight['foreground']
            if fgBg == 'bg':
                return highlight['background']
            else:
                raise InvalidFgBg('Invalid fgBg specified')

    def GetThemeDict(self, type, themeName):
        """Return {option:value} dict for elements in themeName.

        type - string, 'default' or 'user' theme type
        themeName - string, theme name
        Values are loaded over ultimate fallback defaults to guarantee
        that all theme elements are present in a newly created theme.
        """
        if type == 'user':
            cfgParser = self.userCfg['highlight']
        elif type == 'default':
            cfgParser = self.defaultCfg['highlight']
        else:
            raise InvalidTheme('Invalid theme type specified')
        theme = {'normal-foreground': '#000000', 'normal-background':
            '#ffffff', 'keyword-foreground': '#000000',
            'keyword-background': '#ffffff', 'builtin-foreground':
            '#000000', 'builtin-background': '#ffffff',
            'comment-foreground': '#000000', 'comment-background':
            '#ffffff', 'string-foreground': '#000000', 'string-background':
            '#ffffff', 'definition-foreground': '#000000',
            'definition-background': '#ffffff', 'hilite-foreground':
            '#000000', 'hilite-background': 'gray', 'break-foreground':
            '#ffffff', 'break-background': '#000000', 'hit-foreground':
            '#ffffff', 'hit-background': '#000000', 'error-foreground':
            '#ffffff', 'error-background': '#000000', 'cursor-foreground':
            '#000000', 'stdout-foreground': '#000000', 'stdout-background':
            '#ffffff', 'stderr-foreground': '#000000', 'stderr-background':
            '#ffffff', 'console-foreground': '#000000',
            'console-background': '#ffffff'}
        for element in theme:
            if not cfgParser.has_option(themeName, element):
                warning = (
                    """
 Warning: config.IdleConf.GetThemeDict -
 problem retrieving theme element %r
 from theme %r.
 returning default color: %r"""
                     % (element, themeName, theme[element]))
                _warn(warning, 'highlight', themeName, element)
            theme[element] = cfgParser.Get(themeName, element, default=
                theme[element])
        return theme

    def CurrentTheme(self):
        """Return the name of the currently active text color theme."""
        return self.current_colors_and_keys('Theme')

    def CurrentKeys(self):
        """Return the name of the currently active key set."""
        return self.current_colors_and_keys('Keys')

    def current_colors_and_keys(self, section):
        """Return the currently active name for Theme or Keys section.

        idlelib.config-main.def ('default') includes these sections

        [Theme]
        default= 1
        name= IDLE Classic
        name2=

        [Keys]
        default= 1
        name=
        name2=

        Item 'name2', is used for built-in ('default') themes and keys
        added after 2015 Oct 1 and 2016 July 1.  This kludge is needed
        because setting 'name' to a builtin not defined in older IDLEs
        to display multiple error messages or quit.
        See https://bugs.python.org/issue25313.
        When default = True, 'name2' takes precedence over 'name',
        while older IDLEs will just use name.  When default = False,
        'name2' may still be set, but it is ignored.
        """
        cfgname = 'highlight' if section == 'Theme' else 'keys'
        default = self.GetOption('main', section, 'default', type='bool',
            default=True)
        name = ''
        if default:
            name = self.GetOption('main', section, 'name2', default='')
        if not name:
            name = self.GetOption('main', section, 'name', default='')
        if name:
            source = self.defaultCfg if default else self.userCfg
            if source[cfgname].has_section(name):
                return name
        return 'IDLE Classic' if section == 'Theme' else self.default_keys()

    @staticmethod
    def default_keys():
        if sys.platform[:3] == 'win':
            return 'IDLE Classic Windows'
        elif sys.platform == 'darwin':
            return 'IDLE Classic OSX'
        else:
            return 'IDLE Modern Unix'

    def GetExtensions(self, active_only=True, editor_only=False, shell_only
        =False):
        """Return extensions in default and user config-extensions files.

        If active_only True, only return active (enabled) extensions
        and optionally only editor or shell extensions.
        If active_only False, return all extensions.
        """
        extns = self.RemoveKeyBindNames(self.GetSectionList('default',
            'extensions'))
        userExtns = self.RemoveKeyBindNames(self.GetSectionList('user',
            'extensions'))
        for extn in userExtns:
            if extn not in extns:
                extns.append(extn)
        if active_only:
            activeExtns = []
            for extn in extns:
                if self.GetOption('extensions', extn, 'enable', default=
                    True, type='bool'):
                    if editor_only or shell_only:
                        if editor_only:
                            option = 'enable_editor'
                        else:
                            option = 'enable_shell'
                        if self.GetOption('extensions', extn, option,
                            default=True, type='bool', warn_on_default=False):
                            activeExtns.append(extn)
                    else:
                        activeExtns.append(extn)
            return activeExtns
        else:
            return extns

    def RemoveKeyBindNames(self, extnNameList):
        """Return extnNameList with keybinding section names removed."""
        names = extnNameList
        kbNameIndicies = []
        for name in names:
            if name.endswith(('_bindings', '_cfgBindings')):
                kbNameIndicies.append(names.index(name))
        kbNameIndicies.sort(reverse=True)
        for index in kbNameIndicies:
            del names[index]
        return names

    def GetExtnNameForEvent(self, virtualEvent):
        """Return the name of the extension binding virtualEvent, or None.

        virtualEvent - string, name of the virtual event to test for,
                       without the enclosing '<< >>'
        """
        extName = None
        vEvent = '<<' + virtualEvent + '>>'
        for extn in self.GetExtensions(active_only=0):
            for event in self.GetExtensionKeys(extn):
                if event == vEvent:
                    extName = extn
        return extName

    def GetExtensionKeys(self, extensionName):
        """Return dict: {configurable extensionName event : active keybinding}.

        Events come from default config extension_cfgBindings section.
        Keybindings come from GetCurrentKeySet() active key dict,
        where previously used bindings are disabled.
        """
        keysName = extensionName + '_cfgBindings'
        activeKeys = self.GetCurrentKeySet()
        extKeys = {}
        if self.defaultCfg['extensions'].has_section(keysName):
            eventNames = self.defaultCfg['extensions'].GetOptionList(keysName)
            for eventName in eventNames:
                event = '<<' + eventName + '>>'
                binding = activeKeys[event]
                extKeys[event] = binding
        return extKeys

    def __GetRawExtensionKeys(self, extensionName):
        """Return dict {configurable extensionName event : keybinding list}.

        Events come from default config extension_cfgBindings section.
        Keybindings list come from the splitting of GetOption, which
        tries user config before default config.
        """
        keysName = extensionName + '_cfgBindings'
        extKeys = {}
        if self.defaultCfg['extensions'].has_section(keysName):
            eventNames = self.defaultCfg['extensions'].GetOptionList(keysName)
            for eventName in eventNames:
                binding = self.GetOption('extensions', keysName, eventName,
                    default='').split()
                event = '<<' + eventName + '>>'
                extKeys[event] = binding
        return extKeys

    def GetExtensionBindings(self, extensionName):
        """Return dict {extensionName event : active or defined keybinding}.

        Augment self.GetExtensionKeys(extensionName) with mapping of non-
        configurable events (from default config) to GetOption splits,
        as in self.__GetRawExtensionKeys.
        """
        bindsName = extensionName + '_bindings'
        extBinds = self.GetExtensionKeys(extensionName)
        if self.defaultCfg['extensions'].has_section(bindsName):
            eventNames = self.defaultCfg['extensions'].GetOptionList(bindsName)
            for eventName in eventNames:
                binding = self.GetOption('extensions', bindsName, eventName,
                    default='').split()
                event = '<<' + eventName + '>>'
                extBinds[event] = binding
        return extBinds

    def GetKeyBinding(self, keySetName, eventStr):
        """Return the keybinding list for keySetName eventStr.

        keySetName - name of key binding set (config-keys section).
        eventStr - virtual event, including brackets, as in '<<event>>'.
        """
        eventName = eventStr[2:-2]
        binding = self.GetOption('keys', keySetName, eventName, default='',
            warn_on_default=False).split()
        return binding

    def GetCurrentKeySet(self):
        """Return CurrentKeys with 'darwin' modifications."""
        result = self.GetKeySet(self.CurrentKeys())
        if sys.platform == 'darwin':
            for k, v in result.items():
                v2 = [x.replace('<Alt-', '<Option-') for x in v]
                if v != v2:
                    result[k] = v2
        return result

    def GetKeySet(self, keySetName):
        """Return event-key dict for keySetName core plus active extensions.

        If a binding defined in an extension is already in use, the
        extension binding is disabled by being set to ''
        """
        keySet = self.GetCoreKeys(keySetName)
        activeExtns = self.GetExtensions(active_only=1)
        for extn in activeExtns:
            extKeys = self.__GetRawExtensionKeys(extn)
            if extKeys:
                for event in extKeys:
                    if extKeys[event] in keySet.values():
                        extKeys[event] = ''
                    keySet[event] = extKeys[event]
        return keySet

    def IsCoreBinding(self, virtualEvent):
        """Return True if the virtual event is one of the core idle key events.

        virtualEvent - string, name of the virtual event to test for,
                       without the enclosing '<< >>'
        """
        return '<<' + virtualEvent + '>>' in self.GetCoreKeys()

    def GetCoreKeys(self, keySetName=None):
        """Return dict of core virtual-key keybindings for keySetName.

        The default keySetName None corresponds to the keyBindings base
        dict. If keySetName is not None, bindings from the config
        file(s) are loaded _over_ these defaults, so if there is a
        problem getting any core binding there will be an 'ultimate last
        resort fallback' to the CUA-ish bindings defined here.
        """
        keyBindings = {'<<copy>>': ['<Control-c>', '<Control-C>'],
            '<<cut>>': ['<Control-x>', '<Control-X>'], '<<paste>>': [
            '<Control-v>', '<Control-V>'], '<<beginning-of-line>>': [
            '<Control-a>', '<Home>'], '<<center-insert>>': ['<Control-l>'],
            '<<close-all-windows>>': ['<Control-q>'], '<<close-window>>': [
            '<Alt-F4>'], '<<do-nothing>>': ['<Control-x>'],
            '<<end-of-file>>': ['<Control-d>'], '<<python-docs>>': ['<F1>'],
            '<<python-context-help>>': ['<Shift-F1>'], '<<history-next>>':
            ['<Alt-n>'], '<<history-previous>>': ['<Alt-p>'],
            '<<interrupt-execution>>': ['<Control-c>'], '<<view-restart>>':
            ['<F6>'], '<<restart-shell>>': ['<Control-F6>'],
            '<<open-class-browser>>': ['<Alt-c>'], '<<open-module>>': [
            '<Alt-m>'], '<<open-new-window>>': ['<Control-n>'],
            '<<open-window-from-file>>': ['<Control-o>'],
            '<<plain-newline-and-indent>>': ['<Control-j>'],
            '<<print-window>>': ['<Control-p>'], '<<redo>>': ['<Control-y>'
            ], '<<remove-selection>>': ['<Escape>'],
            '<<save-copy-of-window-as-file>>': ['<Alt-Shift-S>'],
            '<<save-window-as-file>>': ['<Alt-s>'], '<<save-window>>': [
            '<Control-s>'], '<<select-all>>': ['<Alt-a>'],
            '<<toggle-auto-coloring>>': ['<Control-slash>'], '<<undo>>': [
            '<Control-z>'], '<<find-again>>': ['<Control-g>', '<F3>'],
            '<<find-in-files>>': ['<Alt-F3>'], '<<find-selection>>': [
            '<Control-F3>'], '<<find>>': ['<Control-f>'], '<<replace>>': [
            '<Control-h>'], '<<goto-line>>': ['<Alt-g>'],
            '<<smart-backspace>>': ['<Key-BackSpace>'],
            '<<newline-and-indent>>': ['<Key-Return>', '<Key-KP_Enter>'],
            '<<smart-indent>>': ['<Key-Tab>'], '<<indent-region>>': [
            '<Control-Key-bracketright>'], '<<dedent-region>>': [
            '<Control-Key-bracketleft>'], '<<comment-region>>': [
            '<Alt-Key-3>'], '<<uncomment-region>>': ['<Alt-Key-4>'],
            '<<tabify-region>>': ['<Alt-Key-5>'], '<<untabify-region>>': [
            '<Alt-Key-6>'], '<<toggle-tabs>>': ['<Alt-Key-t>'],
            '<<change-indentwidth>>': ['<Alt-Key-u>'], '<<del-word-left>>':
            ['<Control-Key-BackSpace>'], '<<del-word-right>>': [
            '<Control-Key-Delete>']}
        if keySetName:
            if not (self.userCfg['keys'].has_section(keySetName) or self.
                defaultCfg['keys'].has_section(keySetName)):
                warning = (
                    """
 Warning: config.py - IdleConf.GetCoreKeys -
 key set %r is not defined, using default bindings."""
                     % (keySetName,))
                _warn(warning, 'keys', keySetName)
            else:
                for event in keyBindings:
                    binding = self.GetKeyBinding(keySetName, event)
                    if binding:
                        keyBindings[event] = binding
                    else:
                        warning = (
                            """
 Warning: config.py - IdleConf.GetCoreKeys -
 problem retrieving key binding for event %r
 from key set %r.
 returning default value: %r"""
                             % (event, keySetName, keyBindings[event]))
                        _warn(warning, 'keys', keySetName, event)
        return keyBindings

    def GetExtraHelpSourceList(self, configSet):
        """Return list of extra help sources from a given configSet.

        Valid configSets are 'user' or 'default'.  Return a list of tuples of
        the form (menu_item , path_to_help_file , option), or return the empty
        list.  'option' is the sequence number of the help resource.  'option'
        values determine the position of the menu items on the Help menu,
        therefore the returned list must be sorted by 'option'.

        """
        helpSources = []
        if configSet == 'user':
            cfgParser = self.userCfg['main']
        elif configSet == 'default':
            cfgParser = self.defaultCfg['main']
        else:
            raise InvalidConfigSet('Invalid configSet specified')
        options = cfgParser.GetOptionList('HelpFiles')
        for option in options:
            value = cfgParser.Get('HelpFiles', option, default=';')
            if value.find(';') == -1:
                menuItem = ''
                helpPath = ''
            else:
                value = value.split(';')
                menuItem = value[0].strip()
                helpPath = value[1].strip()
            if menuItem and helpPath:
                helpSources.append((menuItem, helpPath, option))
        helpSources.sort(key=lambda x: x[2])
        return helpSources

    def GetAllExtraHelpSourcesList(self):
        """Return a list of the details of all additional help sources.

        Tuples in the list are those of GetExtraHelpSourceList.
        """
        allHelpSources = self.GetExtraHelpSourceList('default'
            ) + self.GetExtraHelpSourceList('user')
        return allHelpSources

    def GetFont(self, root, configType, section):
        """Retrieve a font from configuration (font, font-size, font-bold)
        Intercept the special value 'TkFixedFont' and substitute
        the actual font, factoring in some tweaks if needed for
        appearance sakes.

        The 'root' parameter can normally be any valid Tkinter widget.

        Return a tuple (family, size, weight) suitable for passing
        to tkinter.Font
        """
        family = self.GetOption(configType, section, 'font', default='courier')
        size = self.GetOption(configType, section, 'font-size', type='int',
            default='10')
        bold = self.GetOption(configType, section, 'font-bold', default=0,
            type='bool')
        if family == 'TkFixedFont':
            f = Font(name='TkFixedFont', exists=True, root=root)
            actualFont = Font.actual(f)
            family = actualFont['family']
            size = actualFont['size']
            if size <= 0:
                size = 10
            bold = actualFont['weight'] == 'bold'
        return family, size, 'bold' if bold else 'normal'

    def LoadCfgFiles(self):
        """Load all configuration files."""
        for key in self.defaultCfg:
            self.defaultCfg[key].Load()
            self.userCfg[key].Load()

    def SaveUserCfgFiles(self):
        """Write all loaded user configuration files to disk."""
        for key in self.userCfg:
            self.userCfg[key].Save()


idleConf = IdleConf()
_warned = set()


def _warn(msg, *key):
    key = (msg,) + key
    if key not in _warned:
        try:
            print(msg, file=sys.stderr)
        except OSError:
            pass
        _warned.add(key)


if __name__ == '__main__':
    from zlib import crc32
    line, crc = 0, 0

    def sprint(obj):
        global line, crc
        txt = str(obj)
        line += 1
        crc = crc32(txt.encode(encoding='utf-8'), crc)
        print(txt)

    def dumpCfg(cfg):
        print('\n', cfg, '\n')
        for key in sorted(cfg.keys()):
            sections = cfg[key].sections()
            sprint(key)
            sprint(sections)
            for section in sections:
                options = cfg[key].options(section)
                sprint(section)
                sprint(options)
                for option in options:
                    sprint(option + ' = ' + cfg[key].Get(section, option))
    dumpCfg(idleConf.defaultCfg)
    dumpCfg(idleConf.userCfg)
    print('\nlines = ', line, ', crc = ', crc, sep='')
