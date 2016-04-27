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
"""

import operator


__all__ = ['SimpleArray']


class SimpleArray(tuple):

    def _op(self, op, other):
        if isinstance(other, tuple):
            if len(other) != len(self):
                raise TypeError("tuples must have same length for %s" % op)
            return SimpleArray(map(op, self, other))
        return NotImplemented

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
