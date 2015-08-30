# -*- encoding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


def _sum(l):
    """ Same as stdlib sum but returns None instead of 0
    in case of empty sequence.

    >>> sum([1])
    1
    >>> _sum([1])
    1
    >>> sum([1, 2])
    3
    >>> _sum([1, 2])
    3
    >>> sum([])
    0
    >>> _sum([])
    """
    if not l:
        return None
    return sum(l)


def _avg(l):
    """ Arithmetic mean of a sequence. Returns None in case of empty sequence.

    >>> _avg([1])
    1.0
    >>> _avg([1, 2])
    1.5
    >>> _avg([])
    """
    if not l:
        return None
    return sum(l) / float(len(l))


def _min(*args):
    """ Same as stdlib min but returns None instead of exception
    in case of empty sequence.

    >>> min(1, 2)
    1
    >>> _min(1, 2)
    1
    >>> min([1, 2])
    1
    >>> _min([1, 2])
    1
    >>> min(1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: 'int' object is not iterable
    >>> _min(1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: 'int' object is not iterable
    >>> min([1])
    1
    >>> _min([1])
    1
    >>> min()
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: min expected 1 arguments, got 0
    >>> _min()
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: min expected 1 arguments, got 0
    >>> min([])
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    ValueError: min() arg is an empty sequence
    >>> _min([])
    """
    if len(args) == 1 and not args[0]:
        return None
    return min(*args)


def _max(*args):
    """ Same as stdlib max but returns None instead of exception
    in case of empty sequence.

    >>> max(1, 2)
    2
    >>> _max(1, 2)
    2
    >>> max([1, 2])
    2
    >>> _max([1, 2])
    2
    >>> max(1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: 'int' object is not iterable
    >>> _max(1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: 'int' object is not iterable
    >>> max([1])
    1
    >>> _max([1])
    1
    >>> max()
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: max expected 1 arguments, got 0
    >>> _max()
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: max expected 1 arguments, got 0
    >>> max([])
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    ValueError: max() arg is an empty sequence
    >>> _max([])
    """
    if len(args) == 1 and not args[0]:
        return None
    return max(*args)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
