# coding=utf-8
""" Tools for Earth Engine ee.List objects """

import ee


def eq(string, to_compare):
    """ Compare two ee.String and return 1 if equal else 0 """
    string = ee.String(string)
    to_compare = ee.String(to_compare)
    return string.compareTo(to_compare).Not()


def format(string, replacement):
    """ Format a string using variables (as str.format) """

    s = ee.String(string)
    repl = ee.Dictionary(replacement)
    keys = repl.keys()
    values = repl.values()
    z = keys.zip(values)

    def wrap(kv, ini):
        keyval = ee.List(kv)
        ini = ee.String(ini)

        key = ee.String(keyval.get(0))
        value = ee.String(keyval.get(1))

        pattern = ee.String('{').cat(key).cat(ee.String('}'))

        return ini.replace(pattern, value)

    newstr = z.iterate(wrap, s)
    return ee.String(newstr)