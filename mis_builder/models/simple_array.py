# -*- coding: utf-8 -*-
# © 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
""" A trivial immutable array that supports basic arithmetic operations.

>>> a = SimpleArray((1.0, 2.0, 3.0))
>>> b = SimpleArray((4.0, 5.0, 6.0))
>>> t  = (4.0, 5.0, 6.0)
>>> +a
SimpleArray((1.0, 2.0, 3.0))
>>> -a
SimpleArray((-1.0, -2.0, -3.0))
>>> a + b
SimpleArray((5.0, 7.0, 9.0))
>>> b + a
SimpleArray((5.0, 7.0, 9.0))
>>> a + t
SimpleArray((5.0, 7.0, 9.0))
>>> t + a
SimpleArray((5.0, 7.0, 9.0))
>>> a - b
SimpleArray((-3.0, -3.0, -3.0))
>>> a - t
SimpleArray((-3.0, -3.0, -3.0))
>>> t - a
SimpleArray((3.0, 3.0, 3.0))
>>> a * b
SimpleArray((4.0, 10.0, 18.0))
>>> b * a
SimpleArray((4.0, 10.0, 18.0))
>>> a * t
SimpleArray((4.0, 10.0, 18.0))
>>> t * a
SimpleArray((4.0, 10.0, 18.0))
>>> a / b
SimpleArray((0.25, 0.4, 0.5))
>>> b / a
SimpleArray((4.0, 2.5, 2.0))
>>> a / t
SimpleArray((0.25, 0.4, 0.5))
>>> t / a
SimpleArray((4.0, 2.5, 2.0))
>>> b / 2
SimpleArray((2.0, 2.5, 3.0))
>>> 2 * b
SimpleArray((8.0, 10.0, 12.0))
>>> b += 2 ; b
SimpleArray((6.0, 7.0, 8.0))
>>> a / ((1.0, 0.0, 1.0))
SimpleArray((1.0, DataError(), 3.0))
>>> a / 0.0
SimpleArray((DataError(), DataError(), DataError()))
"""

import operator
import traceback

from .data_error import DataError


__all__ = ['SimpleArray']


# TODO named tuple-like behaviour, so expressions can work on subkpis


class SimpleArray(tuple):

    def _op(self, op, other):
        def _o2(x, y):
            try:
                return op(x, y)
            except ZeroDivisionError:
                return DataError('#DIV/0', traceback.format_exc())
            except:
                return DataError('#ERR', traceback.format_exc())

        if isinstance(other, tuple):
            if len(other) != len(self):
                raise TypeError("tuples must have same length for %s" % op)
            return SimpleArray(map(_o2, self, other))
        else:
            return SimpleArray(map(lambda z: _o2(z, other), self))

    def __add__(self, other):
        return self._op(operator.add, other)

    __radd__ = __add__

    def __pos__(self):
        return SimpleArray(map(operator.pos, self))

    def __neg__(self):
        return SimpleArray(map(operator.neg, self))

    def __sub__(self, other):
        return self._op(operator.sub, other)

    def __rsub__(self, other):
        return SimpleArray(other)._op(operator.sub, self)

    def __mul__(self, other):
        return self._op(operator.mul, other)

    __rmul__ = __mul__

    def __div__(self, other):
        return self._op(operator.div, other)

    def __floordiv__(self, other):
        return self._op(operator.floordiv, other)

    def __truediv__(self, other):
        return self._op(operator.truediv, other)

    def __rdiv__(self, other):
        return SimpleArray(other)._op(operator.div, self)

    def __rfloordiv__(self, other):
        return SimpleArray(other)._op(operator.floordiv, self)

    def __rtruediv__(self, other):
        return SimpleArray(other)._op(operator.truediv, self)

    def __repr__(self):
        return "SimpleArray(%s)" % tuple.__repr__(self)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
