"""PyUnit testing against strptime"""
import unittest
import time
import locale
import re
import os
from test import support
from datetime import date as datetime_date
import _strptime


class getlang_Tests(unittest.TestCase):
    """Test _getlang"""

    def test_basic(self):
        self.assertEqual(_strptime._getlang(), locale.getlocale(locale.LC_TIME)
            )


class LocaleTime_Tests(unittest.TestCase):
    """Tests for _strptime.LocaleTime.

    All values are lower-cased when stored in LocaleTime, so make sure to
    compare values after running ``lower`` on them.

    """

    def setUp(self):
        """Create time tuple based on current time."""
        self.time_tuple = time.localtime()
        self.LT_ins = _strptime.LocaleTime()

    def compare_against_time(self, testing, directive, tuple_position,
        error_msg):
        """Helper method that tests testing against directive based on the
        tuple_position of time_tuple.  Uses error_msg as error message.

        """
        strftime_output = time.strftime(directive, self.time_tuple).lower()
        comparison = testing[self.time_tuple[tuple_position]]
        self.assertIn(strftime_output, testing, '%s: not found in tuple' %
            error_msg)
        self.assertEqual(comparison, strftime_output, 
            '%s: position within tuple incorrect; %s != %s' % (error_msg,
            comparison, strftime_output))

    def test_weekday(self):
        self.compare_against_time(self.LT_ins.f_weekday, '%A', 6,
            'Testing of full weekday name failed')
        self.compare_against_time(self.LT_ins.a_weekday, '%a', 6,
            'Testing of abbreviated weekday name failed')

    def test_month(self):
        self.compare_against_time(self.LT_ins.f_month, '%B', 1,
            'Testing against full month name failed')
        self.compare_against_time(self.LT_ins.a_month, '%b', 1,
            'Testing against abbreviated month name failed')

    def test_am_pm(self):
        strftime_output = time.strftime('%p', self.time_tuple).lower()
        self.assertIn(strftime_output, self.LT_ins.am_pm,
            'AM/PM representation not in tuple')
        if self.time_tuple[3] < 12:
            position = 0
        else:
            position = 1
        self.assertEqual(self.LT_ins.am_pm[position], strftime_output,
            'AM/PM representation in the wrong position within the tuple')

    def test_timezone(self):
        timezone = time.strftime('%Z', self.time_tuple).lower()
        if timezone:
            self.assertTrue(timezone in self.LT_ins.timezone[0] or timezone in
                self.LT_ins.timezone[1], 'timezone %s not found in %s' % (
                timezone, self.LT_ins.timezone))

    def test_date_time(self):
        magic_date = 1999, 3, 17, 22, 44, 55, 2, 76, 0
        strftime_output = time.strftime('%c', magic_date)
        self.assertEqual(time.strftime(self.LT_ins.LC_date_time, magic_date
            ), strftime_output, 'LC_date_time incorrect')
        strftime_output = time.strftime('%x', magic_date)
        self.assertEqual(time.strftime(self.LT_ins.LC_date, magic_date),
            strftime_output, 'LC_date incorrect')
        strftime_output = time.strftime('%X', magic_date)
        self.assertEqual(time.strftime(self.LT_ins.LC_time, magic_date),
            strftime_output, 'LC_time incorrect')
        LT = _strptime.LocaleTime()
        LT.am_pm = '', ''
        self.assertTrue(LT.LC_time,
            "LocaleTime's LC directives cannot handle empty strings")

    def test_lang(self):
        self.assertEqual(self.LT_ins.lang, _strptime._getlang())


class TimeRETests(unittest.TestCase):
    """Tests for TimeRE."""

    def setUp(self):
        """Construct generic TimeRE object."""
        self.time_re = _strptime.TimeRE()
        self.locale_time = _strptime.LocaleTime()

    def test_pattern(self):
        pattern_string = self.time_re.pattern('%a %A %d')
        self.assertTrue(pattern_string.find(self.locale_time.a_weekday[2]) !=
            -1, "did not find abbreviated weekday in pattern string '%s'" %
            pattern_string)
        self.assertTrue(pattern_string.find(self.locale_time.f_weekday[4]) !=
            -1, "did not find full weekday in pattern string '%s'" %
            pattern_string)
        self.assertTrue(pattern_string.find(self.time_re['d']) != -1, 
            "did not find 'd' directive pattern string '%s'" % pattern_string)

    def test_pattern_escaping(self):
        pattern_string = self.time_re.pattern('\\d+')
        self.assertIn('\\\\d\\+', pattern_string, 
            '%s does not have re characters escaped properly' % pattern_string)

    def test_compile(self):
        found = self.time_re.compile('%A').match(self.locale_time.f_weekday[6])
        self.assertTrue(found and found.group('A') == self.locale_time.
            f_weekday[6], "re object for '%A' failed")
        compiled = self.time_re.compile('%a %b')
        found = compiled.match('%s %s' % (self.locale_time.a_weekday[4],
            self.locale_time.a_month[4]))
        self.assertTrue(found, 
            "Match failed with '%s' regex and '%s' string" % (compiled.
            pattern, '%s %s' % (self.locale_time.a_weekday[4], self.
            locale_time.a_month[4])))
        self.assertTrue(found.group('a') == self.locale_time.a_weekday[4] and
            found.group('b') == self.locale_time.a_month[4], 
            "re object couldn't find the abbreviated weekday month in '%s' using '%s'; group 'a' = '%s', group 'b' = %s'"
             % (found.string, found.re.pattern, found.group('a'), found.
            group('b')))
        for directive in ('a', 'A', 'b', 'B', 'c', 'd', 'G', 'H', 'I', 'j',
            'm', 'M', 'p', 'S', 'u', 'U', 'V', 'w', 'W', 'x', 'X', 'y', 'Y',
            'Z', '%'):
            compiled = self.time_re.compile('%' + directive)
            found = compiled.match(time.strftime('%' + directive))
            self.assertTrue(found, 
                "Matching failed on '%s' using '%s' regex" % (time.strftime
                ('%' + directive), compiled.pattern))

    def test_blankpattern(self):
        test_locale = _strptime.LocaleTime()
        test_locale.timezone = frozenset(), frozenset()
        self.assertEqual(_strptime.TimeRE(test_locale).pattern('%Z'), '',
            "with timezone == ('',''), TimeRE().pattern('%Z') != ''")

    def test_matching_with_escapes(self):
        compiled_re = self.time_re.compile('\\w+ %m')
        found = compiled_re.match('\\w+ 10')
        self.assertTrue(found, "Escaping failed of format '\\w+ 10'")

    def test_locale_data_w_regex_metacharacters(self):
        locale_time = _strptime.LocaleTime()
        locale_time.timezone = frozenset(('utc', 'gmt',
            'Tokyo (standard time)')), frozenset('Tokyo (daylight time)')
        time_re = _strptime.TimeRE(locale_time)
        self.assertTrue(time_re.compile('%Z').match('Tokyo (standard time)'
            ),
            'locale data that contains regex metacharacters is not properly escaped'
            )

    def test_whitespace_substitution(self):
        pattern = self.time_re.pattern('%j %H')
        self.assertFalse(re.match(pattern, '180'))
        self.assertTrue(re.match(pattern, '18 0'))


class StrptimeTests(unittest.TestCase):
    """Tests for _strptime.strptime."""

    def setUp(self):
        """Create testing time tuple."""
        self.time_tuple = time.gmtime()

    def test_ValueError(self):
        self.assertRaises(ValueError, _strptime._strptime_time, data_string
            ='%d', format='%A')
        for bad_format in ('%', '% ', '%e'):
            try:
                _strptime._strptime_time('2005', bad_format)
            except ValueError:
                continue
            except Exception as err:
                self.fail("'%s' raised %s, not ValueError" % (bad_format,
                    err.__class__.__name__))
            else:
                self.fail("'%s' did not raise ValueError" % bad_format)
        with self.assertRaises(ValueError):
            _strptime._strptime('1999 50', '%Y %V')
        with self.assertRaises(ValueError):
            _strptime._strptime('1999 51', '%G %V')
        for w in ('A', 'a', 'w', 'u'):
            with self.assertRaises(ValueError):
                _strptime._strptime('1999 51', '%G %{}'.format(w))
        with self.assertRaises(ValueError):
            _strptime._strptime('2015', '%G')
        with self.assertRaises(ValueError):
            _strptime._strptime('1999 256', '%G %j')

    def test_strptime_exception_context(self):
        with self.assertRaises(ValueError) as e:
            _strptime._strptime_time('', '%D')
        self.assertIs(e.exception.__suppress_context__, True)
        with self.assertRaises(ValueError) as e:
            _strptime._strptime_time('19', '%Y %')
        self.assertIs(e.exception.__suppress_context__, True)

    def test_unconverteddata(self):
        self.assertRaises(ValueError, _strptime._strptime_time, '10 12', '%m')

    def helper(self, directive, position):
        """Helper fxn in testing."""
        strf_output = time.strftime('%' + directive, self.time_tuple)
        strp_output = _strptime._strptime_time(strf_output, '%' + directive)
        self.assertTrue(strp_output[position] == self.time_tuple[position],
            "testing of '%s' directive failed; '%s' -> %s != %s" % (
            directive, strf_output, strp_output[position], self.time_tuple[
            position]))

    def test_year(self):
        for directive in ('y', 'Y'):
            self.helper(directive, 0)
        for century, bounds in ((1900, ('69', '99')), (2000, ('00', '68'))):
            for bound in bounds:
                strp_output = _strptime._strptime_time(bound, '%y')
                expected_result = century + int(bound)
                self.assertTrue(strp_output[0] == expected_result, 
                    "'y' test failed; passed in '%s' and returned '%s'" % (
                    bound, strp_output[0]))

    def test_month(self):
        for directive in ('B', 'b', 'm'):
            self.helper(directive, 1)

    def test_day(self):
        self.helper('d', 2)

    def test_hour(self):
        self.helper('H', 3)
        strf_output = time.strftime('%I %p', self.time_tuple)
        strp_output = _strptime._strptime_time(strf_output, '%I %p')
        self.assertTrue(strp_output[3] == self.time_tuple[3], 
            "testing of '%%I %%p' directive failed; '%s' -> %s != %s" % (
            strf_output, strp_output[3], self.time_tuple[3]))

    def test_minute(self):
        self.helper('M', 4)

    def test_second(self):
        self.helper('S', 5)

    def test_fraction(self):
        import datetime
        d = datetime.datetime(2012, 12, 20, 12, 34, 56, 78987)
        tup, frac = _strptime._strptime(str(d), format='%Y-%m-%d %H:%M:%S.%f')
        self.assertEqual(frac, d.microsecond)

    def test_weekday(self):
        for directive in ('A', 'a', 'w', 'u'):
            self.helper(directive, 6)

    def test_julian(self):
        self.helper('j', 7)

    def test_timezone(self):
        strp_output = _strptime._strptime_time('UTC', '%Z')
        self.assertEqual(strp_output.tm_isdst, 0)
        strp_output = _strptime._strptime_time('GMT', '%Z')
        self.assertEqual(strp_output.tm_isdst, 0)
        time_tuple = time.localtime()
        strf_output = time.strftime('%Z')
        strp_output = _strptime._strptime_time(strf_output, '%Z')
        locale_time = _strptime.LocaleTime()
        if time.tzname[0] != time.tzname[1] or not time.daylight:
            self.assertTrue(strp_output[8] == time_tuple[8], 
                "timezone check failed; '%s' -> %s != %s" % (strf_output,
                strp_output[8], time_tuple[8]))
        else:
            self.assertTrue(strp_output[8] == -1,
                'LocaleTime().timezone has duplicate values and time.daylight but timezone value not set to -1'
                )

    def test_bad_timezone(self):
        tz_name = time.tzname[0]
        if tz_name.upper() in ('UTC', 'GMT'):
            self.skipTest('need non-UTC/GMT timezone')
        with support.swap_attr(time, 'tzname', (tz_name, tz_name)
            ), support.swap_attr(time, 'daylight', 1), support.swap_attr(time,
            'tzset', lambda : None):
            time.tzname = tz_name, tz_name
            time.daylight = 1
            tz_value = _strptime._strptime_time(tz_name, '%Z')[8]
            self.assertEqual(tz_value, -1, 
                '%s lead to a timezone value of %s instead of -1 when time.daylight set to %s and passing in %s'
                 % (time.tzname, tz_value, time.daylight, tz_name))

    def test_date_time(self):
        for position in range(6):
            self.helper('c', position)

    def test_date(self):
        for position in range(0, 3):
            self.helper('x', position)

    def test_time(self):
        for position in range(3, 6):
            self.helper('X', position)

    def test_percent(self):
        strf_output = time.strftime('%m %% %Y', self.time_tuple)
        strp_output = _strptime._strptime_time(strf_output, '%m %% %Y')
        self.assertTrue(strp_output[0] == self.time_tuple[0] and 
            strp_output[1] == self.time_tuple[1],
            'handling of percent sign failed')

    def test_caseinsensitive(self):
        strf_output = time.strftime('%B', self.time_tuple)
        self.assertTrue(_strptime._strptime_time(strf_output.upper(), '%B'),
            'strptime does not handle ALL-CAPS names properly')
        self.assertTrue(_strptime._strptime_time(strf_output.lower(), '%B'),
            'strptime does not handle lowercase names properly')
        self.assertTrue(_strptime._strptime_time(strf_output.capitalize(),
            '%B'), 'strptime does not handle capword names properly')

    def test_defaults(self):
        defaults = 1900, 1, 1, 0, 0, 0, 0, 1, -1
        strp_output = _strptime._strptime_time('1', '%m')
        self.assertTrue(strp_output == defaults, 
            'Default values for strptime() are incorrect; %s != %s' % (
            strp_output, defaults))

    def test_escaping(self):
        need_escaping = '.^$*+?{}\\[]|)('
        self.assertTrue(_strptime._strptime_time(need_escaping, need_escaping))

    def test_feb29_on_leap_year_without_year(self):
        time.strptime('Feb 29', '%b %d')

    def test_mar1_comes_after_feb29_even_when_omitting_the_year(self):
        self.assertLess(time.strptime('Feb 29', '%b %d'), time.strptime(
            'Mar 1', '%b %d'))


class Strptime12AMPMTests(unittest.TestCase):
    """Test a _strptime regression in '%I %p' at 12 noon (12 PM)"""

    def test_twelve_noon_midnight(self):
        eq = self.assertEqual
        eq(time.strptime('12 PM', '%I %p')[3], 12)
        eq(time.strptime('12 AM', '%I %p')[3], 0)
        eq(_strptime._strptime_time('12 PM', '%I %p')[3], 12)
        eq(_strptime._strptime_time('12 AM', '%I %p')[3], 0)


class JulianTests(unittest.TestCase):
    """Test a _strptime regression that all julian (1-366) are accepted"""

    def test_all_julian_days(self):
        eq = self.assertEqual
        for i in range(1, 367):
            eq(_strptime._strptime_time('%d 2004' % i, '%j %Y')[7], i)


class CalculationTests(unittest.TestCase):
    """Test that strptime() fills in missing info correctly"""

    def setUp(self):
        self.time_tuple = time.gmtime()

    def test_julian_calculation(self):
        format_string = '%Y %m %d %H %M %S %w %Z'
        result = _strptime._strptime_time(time.strftime(format_string, self
            .time_tuple), format_string)
        self.assertTrue(result.tm_yday == self.time_tuple.tm_yday, 
            'Calculation of tm_yday failed; %s != %s' % (result.tm_yday,
            self.time_tuple.tm_yday))

    def test_gregorian_calculation(self):
        format_string = '%Y %H %M %S %w %j %Z'
        result = _strptime._strptime_time(time.strftime(format_string, self
            .time_tuple), format_string)
        self.assertTrue(result.tm_year == self.time_tuple.tm_year and 
            result.tm_mon == self.time_tuple.tm_mon and result.tm_mday ==
            self.time_tuple.tm_mday, 
            'Calculation of Gregorian date failed;%s-%s-%s != %s-%s-%s' % (
            result.tm_year, result.tm_mon, result.tm_mday, self.time_tuple.
            tm_year, self.time_tuple.tm_mon, self.time_tuple.tm_mday))

    def test_day_of_week_calculation(self):
        format_string = '%Y %m %d %H %S %j %Z'
        result = _strptime._strptime_time(time.strftime(format_string, self
            .time_tuple), format_string)
        self.assertTrue(result.tm_wday == self.time_tuple.tm_wday, 
            'Calculation of day of the week failed;%s != %s' % (result.
            tm_wday, self.time_tuple.tm_wday))
    if support.is_android:
        _ymd_excluded = (1905, 1, 1), (1906, 12, 31), (2008, 12, 29), (1917,
            12, 31)
        _formats_excluded = '%G %V',
    else:
        _ymd_excluded = ()
        _formats_excluded = ()

    def test_week_of_year_and_day_of_week_calculation(self):

        def test_helper(ymd_tuple, test_reason):
            for year_week_format in ('%Y %W', '%Y %U', '%G %V'):
                if (year_week_format in self._formats_excluded and 
                    ymd_tuple in self._ymd_excluded):
                    return
                for weekday_format in ('%w', '%u', '%a', '%A'):
                    format_string = year_week_format + ' ' + weekday_format
                    with self.subTest(test_reason, date=ymd_tuple, format=
                        format_string):
                        dt_date = datetime_date(*ymd_tuple)
                        strp_input = dt_date.strftime(format_string)
                        strp_output = _strptime._strptime_time(strp_input,
                            format_string)
                        msg = '%r: %s != %s' % (strp_input, strp_output[7],
                            dt_date.timetuple()[7])
                        self.assertEqual(strp_output[:3], ymd_tuple, msg)
        test_helper((1901, 1, 3), 'week 0')
        test_helper((1901, 1, 8), 'common case')
        test_helper((1901, 1, 13), 'day on Sunday')
        test_helper((1901, 1, 14), 'day on Monday')
        test_helper((1905, 1, 1), 'Jan 1 on Sunday')
        test_helper((1906, 1, 1), 'Jan 1 on Monday')
        test_helper((1906, 1, 7), 'first Sunday in a year starting on Monday')
        test_helper((1905, 12, 31), 'Dec 31 on Sunday')
        test_helper((1906, 12, 31), 'Dec 31 on Monday')
        test_helper((2008, 12, 29), 'Monday in the last week of the year')
        test_helper((2008, 12, 22),
            'Monday in the second-to-last week of the year')
        test_helper((1978, 10, 23), 'randomly chosen date')
        test_helper((2004, 12, 18), 'randomly chosen date')
        test_helper((1978, 10, 23),
            'year starting and ending on Monday while date not on Sunday or Monday'
            )
        test_helper((1917, 12, 17),
            'year starting and ending on Monday with a Monday not at the beginning or end of the year'
            )
        test_helper((1917, 12, 31),
            'Dec 31 on Monday with year starting and ending on Monday')
        test_helper((2007, 1, 7), 'First Sunday of 2007')
        test_helper((2007, 1, 14), 'Second Sunday of 2007')
        test_helper((2006, 12, 31), 'Last Sunday of 2006')
        test_helper((2006, 12, 24), 'Second to last Sunday of 2006')

    def test_week_0(self):

        def check(value, format, *expected):
            self.assertEqual(_strptime._strptime_time(value, format)[:-1],
                expected)
        check('2015 0 0', '%Y %U %w', 2014, 12, 28, 0, 0, 0, 6, 362)
        check('2015 0 0', '%Y %W %w', 2015, 1, 4, 0, 0, 0, 6, 4)
        check('2015 1 1', '%G %V %u', 2014, 12, 29, 0, 0, 0, 0, 363)
        check('2015 0 1', '%Y %U %w', 2014, 12, 29, 0, 0, 0, 0, 363)
        check('2015 0 1', '%Y %W %w', 2014, 12, 29, 0, 0, 0, 0, 363)
        check('2015 1 2', '%G %V %u', 2014, 12, 30, 0, 0, 0, 1, 364)
        check('2015 0 2', '%Y %U %w', 2014, 12, 30, 0, 0, 0, 1, 364)
        check('2015 0 2', '%Y %W %w', 2014, 12, 30, 0, 0, 0, 1, 364)
        check('2015 1 3', '%G %V %u', 2014, 12, 31, 0, 0, 0, 2, 365)
        check('2015 0 3', '%Y %U %w', 2014, 12, 31, 0, 0, 0, 2, 365)
        check('2015 0 3', '%Y %W %w', 2014, 12, 31, 0, 0, 0, 2, 365)
        check('2015 1 4', '%G %V %u', 2015, 1, 1, 0, 0, 0, 3, 1)
        check('2015 0 4', '%Y %U %w', 2015, 1, 1, 0, 0, 0, 3, 1)
        check('2015 0 4', '%Y %W %w', 2015, 1, 1, 0, 0, 0, 3, 1)
        check('2015 1 5', '%G %V %u', 2015, 1, 2, 0, 0, 0, 4, 2)
        check('2015 0 5', '%Y %U %w', 2015, 1, 2, 0, 0, 0, 4, 2)
        check('2015 0 5', '%Y %W %w', 2015, 1, 2, 0, 0, 0, 4, 2)
        check('2015 1 6', '%G %V %u', 2015, 1, 3, 0, 0, 0, 5, 3)
        check('2015 0 6', '%Y %U %w', 2015, 1, 3, 0, 0, 0, 5, 3)
        check('2015 0 6', '%Y %W %w', 2015, 1, 3, 0, 0, 0, 5, 3)
        check('2015 1 7', '%G %V %u', 2015, 1, 4, 0, 0, 0, 6, 4)
        check('2009 0 0', '%Y %U %w', 2008, 12, 28, 0, 0, 0, 6, 363)
        check('2009 0 0', '%Y %W %w', 2009, 1, 4, 0, 0, 0, 6, 4)
        check('2009 1 1', '%G %V %u', 2008, 12, 29, 0, 0, 0, 0, 364)
        check('2009 0 1', '%Y %U %w', 2008, 12, 29, 0, 0, 0, 0, 364)
        check('2009 0 1', '%Y %W %w', 2008, 12, 29, 0, 0, 0, 0, 364)
        check('2009 1 2', '%G %V %u', 2008, 12, 30, 0, 0, 0, 1, 365)
        check('2009 0 2', '%Y %U %w', 2008, 12, 30, 0, 0, 0, 1, 365)
        check('2009 0 2', '%Y %W %w', 2008, 12, 30, 0, 0, 0, 1, 365)
        check('2009 1 3', '%G %V %u', 2008, 12, 31, 0, 0, 0, 2, 366)
        check('2009 0 3', '%Y %U %w', 2008, 12, 31, 0, 0, 0, 2, 366)
        check('2009 0 3', '%Y %W %w', 2008, 12, 31, 0, 0, 0, 2, 366)
        check('2009 1 4', '%G %V %u', 2009, 1, 1, 0, 0, 0, 3, 1)
        check('2009 0 4', '%Y %U %w', 2009, 1, 1, 0, 0, 0, 3, 1)
        check('2009 0 4', '%Y %W %w', 2009, 1, 1, 0, 0, 0, 3, 1)
        check('2009 1 5', '%G %V %u', 2009, 1, 2, 0, 0, 0, 4, 2)
        check('2009 0 5', '%Y %U %w', 2009, 1, 2, 0, 0, 0, 4, 2)
        check('2009 0 5', '%Y %W %w', 2009, 1, 2, 0, 0, 0, 4, 2)
        check('2009 1 6', '%G %V %u', 2009, 1, 3, 0, 0, 0, 5, 3)
        check('2009 0 6', '%Y %U %w', 2009, 1, 3, 0, 0, 0, 5, 3)
        check('2009 0 6', '%Y %W %w', 2009, 1, 3, 0, 0, 0, 5, 3)
        check('2009 1 7', '%G %V %u', 2009, 1, 4, 0, 0, 0, 6, 4)


class CacheTests(unittest.TestCase):
    """Test that caching works properly."""

    def test_time_re_recreation(self):
        _strptime._strptime_time('10', '%d')
        _strptime._strptime_time('2005', '%Y')
        _strptime._TimeRE_cache.locale_time.lang = 'Ni'
        original_time_re = _strptime._TimeRE_cache
        _strptime._strptime_time('10', '%d')
        self.assertIsNot(original_time_re, _strptime._TimeRE_cache)
        self.assertEqual(len(_strptime._regex_cache), 1)

    def test_regex_cleanup(self):
        try:
            del _strptime._regex_cache['%d']
        except KeyError:
            pass
        bogus_key = 0
        while len(_strptime._regex_cache) <= _strptime._CACHE_MAX_SIZE:
            _strptime._regex_cache[bogus_key] = None
            bogus_key += 1
        _strptime._strptime_time('10', '%d')
        self.assertEqual(len(_strptime._regex_cache), 1)

    def test_new_localetime(self):
        locale_time_id = _strptime._TimeRE_cache.locale_time
        _strptime._TimeRE_cache.locale_time.lang = 'Ni'
        _strptime._strptime_time('10', '%d')
        self.assertIsNot(locale_time_id, _strptime._TimeRE_cache.locale_time)

    def test_TimeRE_recreation_locale(self):
        locale_info = locale.getlocale(locale.LC_TIME)
        try:
            locale.setlocale(locale.LC_TIME, ('en_US', 'UTF8'))
        except locale.Error:
            self.skipTest('test needs en_US.UTF8 locale')
        try:
            _strptime._strptime_time('10', '%d')
            first_time_re = _strptime._TimeRE_cache
            try:
                locale.setlocale(locale.LC_TIME, ('de_DE', 'UTF8'))
                _strptime._strptime_time('10', '%d')
                second_time_re = _strptime._TimeRE_cache
                self.assertIsNot(first_time_re, second_time_re)
            except locale.Error:
                self.skipTest('test needs de_DE.UTF8 locale')
        finally:
            locale.setlocale(locale.LC_TIME, locale_info)

    @support.run_with_tz('STD-1DST')
    def test_TimeRE_recreation_timezone(self):
        oldtzname = time.tzname
        tm = _strptime._strptime_time(time.tzname[0], '%Z')
        self.assertEqual(tm.tm_isdst, 0)
        tm = _strptime._strptime_time(time.tzname[1], '%Z')
        self.assertEqual(tm.tm_isdst, 1)
        first_time_re = _strptime._TimeRE_cache
        os.environ['TZ'] = 'EST+05EDT,M3.2.0,M11.1.0'
        time.tzset()
        tm = _strptime._strptime_time(time.tzname[0], '%Z')
        self.assertEqual(tm.tm_isdst, 0)
        tm = _strptime._strptime_time(time.tzname[1], '%Z')
        self.assertEqual(tm.tm_isdst, 1)
        second_time_re = _strptime._TimeRE_cache
        self.assertIsNot(first_time_re, second_time_re)
        with self.assertRaises(ValueError):
            _strptime._strptime_time(oldtzname[0], '%Z')
        with self.assertRaises(ValueError):
            _strptime._strptime_time(oldtzname[1], '%Z')


if __name__ == '__main__':
    unittest.main()
