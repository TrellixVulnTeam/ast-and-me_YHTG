"""Complete the current word before the cursor with words in the editor.

Each menu selection or shortcut key selection replaces the word with a
different word with the same prefix. The search for matches begins
before the target and moves toward the top of the editor. It then starts
after the cursor and moves down. It then returns to the original word and
the cycle starts again.

Changing the current text line or leaving the cursor in a different
place before requesting the next selection causes AutoExpand to reset
its state.

This is an extension file and there is only one instance of AutoExpand.
"""
import re
import string


class AutoExpand:
    menudefs = [('edit', [('E_xpand Word', '<<expand-word>>')])]
    wordchars = string.ascii_letters + string.digits + '_'

    def __init__(self, editwin):
        self.text = editwin.text
        self.bell = self.text.bell
        self.state = None

    def expand_word_event(self, event):
        """Replace the current word with the next expansion."""
        curinsert = self.text.index('insert')
        curline = self.text.get('insert linestart', 'insert lineend')
        if not self.state:
            words = self.getwords()
            index = 0
        else:
            words, index, insert, line = self.state
            if insert != curinsert or line != curline:
                words = self.getwords()
                index = 0
        if not words:
            self.bell()
            return 'break'
        word = self.getprevword()
        self.text.delete('insert - %d chars' % len(word), 'insert')
        newword = words[index]
        index = (index + 1) % len(words)
        if index == 0:
            self.bell()
        self.text.insert('insert', newword)
        curinsert = self.text.index('insert')
        curline = self.text.get('insert linestart', 'insert lineend')
        self.state = words, index, curinsert, curline
        return 'break'

    def getwords(self):
        """Return a list of words that match the prefix before the cursor."""
        word = self.getprevword()
        if not word:
            return []
        before = self.text.get('1.0', 'insert wordstart')
        wbefore = re.findall('\\b' + word + '\\w+\\b', before)
        del before
        after = self.text.get('insert wordend', 'end')
        wafter = re.findall('\\b' + word + '\\w+\\b', after)
        del after
        if not wbefore and not wafter:
            return []
        words = []
        dict = {}
        wbefore.reverse()
        for w in wbefore:
            if dict.get(w):
                continue
            words.append(w)
            dict[w] = w
        for w in wafter:
            if dict.get(w):
                continue
            words.append(w)
            dict[w] = w
        words.append(word)
        return words

    def getprevword(self):
        """Return the word prefix before the cursor."""
        line = self.text.get('insert linestart', 'insert')
        i = len(line)
        while i > 0 and line[i - 1] in self.wordchars:
            i = i - 1
        return line[i:]


if __name__ == '__main__':
    import unittest
    unittest.main('idlelib.idle_test.test_autoexpand', verbosity=2)
