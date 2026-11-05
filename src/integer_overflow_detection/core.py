"""Check whether fixed-width integer arithmetic would overflow before it runs.

All functions operate on Python ints and take an explicit ``bits`` argument.
By default the interpretation is signed two's complement (``signed=True``),
which matches the common case of C ``int``/``long`` and Rust ``i32``/``i64``.
Pass ``signed=False`` for unsigned widths (C ``unsigned``, Rust ``u32``).

The check is exact: it uses Python's arbitrary-precision integers to compute
the mathematical result and then asks whether that result fits, so there is
no rounding, no floating point, and no dependence on the host word size.
"""

from __future__ import annotations

import builtins
from typing import NamedTuple


class OverflowError(ArithmeticError):
    """Raised by the strict variants when a result would not fit."""


class OverflowResult(NamedTuple):
    """Outcome of an overflow check.

    ``overflow`` is True when the mathematical result does not fit in the
    requested width.  ``value`` is the mathematical result regardless of
    whether it fits; it is only meaningful when ``overflow`` is False, but
    callers that want to inspect the out-of-range value can still read it.
    """

    overflow: bool
    value: int


def _validate_bits(bits: int) -> None:
    if not isinstance(bits, int) or isinstance(bits, bool):
        raise TypeError("bits must be an int")
    if bits <= 0:
        raise ValueError("bits must be positive")


def min_value(bits: int, signed: bool = True) -> int:
    """Smallest representable value for a ``bits``-wide integer."""
    _validate_bits(bits)
    if signed:
        return -(1 << (bits - 1))
    return 0


def max_value(bits: int, signed: bool = True) -> int:
    """Largest representable value for a ``bits``-wide integer."""
    _validate_bits(bits)
    if signed:
        return (1 << (bits - 1)) - 1
    return (1 << bits) - 1


def fits(value: int, bits: int, signed: bool = True) -> bool:
    """True when ``value`` is representable in ``bits`` bits."""
    _validate_bits(bits)
    return min_value(bits, signed) <= value <= max_value(bits, signed)


def fits_signed(value: int, bits: int) -> bool:
    """Convenience wrapper for the common signed case."""
    return fits(value, bits, signed=True)


def fits_unsigned(value: int, bits: int) -> bool:
    """Convenience wrapper for the common unsigned case."""
    return fits(value, bits, signed=False)


def add(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a + b`` for overflow in ``bits`` bits."""
    _validate_bits(bits)
    result = a + b
    return OverflowResult(not fits(result, bits, signed), result)


def sub(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a - b`` for overflow in ``bits`` bits."""
    _validate_bits(bits)
    result = a - b
    return OverflowResult(not fits(result, bits, signed), result)


def mul(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a * b`` for overflow in ``bits`` bits."""
    _validate_bits(bits)
    result = a * b
    return OverflowResult(not fits(result, bits, signed), result)


def div(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a / b`` (truncating toward zero) for overflow in ``bits`` bits.

    The only overflow case for division in two's complement is the most
    negative value divided by -1, which does not fit back into the same
    width.  Division by zero raises ``ZeroDivisionError`` before any
    overflow check is attempted.
    """
    _validate_bits(bits)
    if b == 0:
        raise ZeroDivisionError("integer division by zero")
    # Python's // floors, but C/Rust truncate toward zero.  Match the
    # truncating behaviour so the overflow predicate agrees with those
    # languages for negative operands.
    q = builtins.abs(a) // builtins.abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return OverflowResult(not fits(q, bits, signed), q)


def neg(a: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check unary ``-a`` for overflow in ``bits`` bits."""
    _validate_bits(bits)
    result = -a
    return OverflowResult(not fits(result, bits, signed), result)


def abs(a: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``abs(a)`` for overflow in ``bits`` bits.

    For signed widths this can overflow when ``a`` is the most negative
    value, whose magnitude is one larger than the most positive value.
    """
    _validate_bits(bits)
    result = -a if a < 0 else a
    return OverflowResult(not fits(result, bits, signed), result)


def shl(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a << b`` for overflow in ``bits`` bits.

    ``b`` is the shift count; a negative count raises ``ValueError``.
    """
    _validate_bits(bits)
    if b < 0:
        raise ValueError("shift count must be non-negative")
    result = a << b
    return OverflowResult(not fits(result, bits, signed), result)


def shr(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a >> b`` for overflow in ``bits`` bits.

    Right shift never overflows for a fixed width, but the function is
    provided for symmetry with :func:`shl`.  ``b`` must be non-negative.
    """
    _validate_bits(bits)
    if b < 0:
        raise ValueError("shift count must be non-negative")
    result = a >> b
    return OverflowResult(not fits(result, bits, signed), result)


def pow(a: int, b: int, bits: int, signed: bool = True) -> OverflowResult:
    """Check ``a ** b`` for overflow in ``bits`` bits.

    ``b`` must be non-negative; negative exponents are not integers and
    raise ``ValueError``.
    """
    _validate_bits(bits)
    if b < 0:
        raise ValueError("exponent must be non-negative")
    result = a ** b
    return OverflowResult(not fits(result, bits, signed), result)
