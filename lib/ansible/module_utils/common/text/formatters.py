# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import re

from ansible.module_utils.six import iteritems

SIZE_RANGES = {
    'Y': 1 << 80,
    'Z': 1 << 70,
    'E': 1 << 60,
    'P': 1 << 50,
    'T': 1 << 40,
    'G': 1 << 30,
    'M': 1 << 20,
    'K': 1 << 10,
    'B': 1,
}

_SIZE_UNIT_PREFIXES = {
    'Y': 'yotta',
    'Z': 'zetta',
    'E': 'exa',
    'P': 'peta',
    'T': 'tera',
    'G': 'giga',
    'M': 'mega',
    'K': 'kilo',
    'B': '',
}


def lenient_lowercase(lst):
    """Lowercase elements of a list.

    If an element is not a string, pass it through untouched.
    """
    lowered = []
    for value in lst:
        try:
            lowered.append(value.lower())
        except AttributeError:
            lowered.append(value)
    return lowered


def human_to_bytes(number, default_unit=None, isbits=False):
    """Convert number in string format into bytes (ex: '2K' => 2048) or using unit argument.

    example: human_to_bytes('10M') <=> human_to_bytes(10, 'M').
    The input must be an ASCII decimal number followed by an optional unit,
    with optional ASCII spaces before the unit or at the end.

    When isbits is False (default), converts bytes from a human-readable format to integer.
        example: human_to_bytes('1MB') returns 1048576 (int).
        The function expects 'B' (uppercase) as a byte identifier passed
        as a part of the number string or default_unit, e.g. 'MB'/'KB'/etc.
        (except when the identifier is single 'b', it is perceived as a byte identifier too).
        if 'Mb'/'Kb'/... is passed, ValueError will be raised.

    When isbits is True, converts bits from a human-readable format to integer.
        example: human_to_bytes('1Mb', isbits=True) returns 1048576 (int).
        The function expects 'b' (lowercase) as a bit identifier, e.g. 'Mb'/'Kb'/etc.
        if 'MB'/'KB'/... is passed, ValueError will be raised.
    """
    m = re.fullmatch(r'([0-9]+(?:\.[0-9]*)?|\.[0-9]+) *(?:([A-Za-z]+) *)?', str(number))
    if m is None:
        raise ValueError("human_to_bytes() can't interpret following string: %s" % str(number))
    num = float(m.group(1))

    unit = m.group(2)
    if unit is None:
        unit = default_unit

    if unit is None:
        # No unit given, returning raw number
        return int(round(num))
    range_key = unit[0].upper() if unit != '' else ''
    try:
        limit = SIZE_RANGES[range_key]
    except KeyError:
        raise ValueError("human_to_bytes() failed to convert %s (unit = %s). The suffix must be one of %s" % (number, unit, ", ".join(SIZE_RANGES.keys())))

    unit_class = 'b' if isbits else 'B'
    unit_class_name = 'bit' if isbits else 'byte'
    # Single-letter prefixes are valid for both bytes and bits.
    if len(unit) > 1:
        expect_message = 'expect %s%s or %s' % (range_key, unit_class, range_key)
        if range_key == 'B':
            expect_message = 'expect %s or %s' % (unit_class, unit_class_name)

        full_name = _SIZE_UNIT_PREFIXES[range_key] + unit_class_name
        is_abbreviation = range_key != 'B' and unit[1:] == unit_class
        if not is_abbreviation and unit.lower() not in (full_name, full_name + 's'):
            raise ValueError("human_to_bytes() failed to convert %s. Value is not a valid string (%s)" % (number, expect_message))

    return int(round(num * limit))


def bytes_to_human(size, isbits=False, unit=None):
    base = 'Bytes'
    if isbits:
        base = 'bits'
    suffix = ''

    for suffix, limit in sorted(iteritems(SIZE_RANGES), key=lambda item: -item[1]):
        if (unit is None and size >= limit) or unit is not None and unit.upper() == suffix[0]:
            break

    if limit != 1:
        suffix += base[0]
    else:
        suffix = base

    return '%.2f %s' % (size / limit, suffix)
