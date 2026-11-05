# integer_overflow_detection

Check whether a fixed-width integer operation would overflow before running it, using Python's arbitrary-precision integers to compute the exact mathematical result and compare it against the requested width.

```python
from integer_overflow_detection import add, mul, fits, max_value

r = add(100, 28, 8)          # signed 8-bit
assert r.overflow is True
assert r.value == 128

r = mul(11, 11, 8)
assert r.overflow is False
assert r.value == 121

assert fits(-128, 8)
assert not fits(128, 8)
assert max_value(8) == 127
```

## Why this exists

When you emulate a fixed-width machine — a bytecode interpreter, a binary format parser, a compiler constant folder — you need to know whether `a + b` would wrap before you commit to the result. Doing the arithmetic in Python first and then checking the range is exact and cheap, and it avoids the trap of trying to detect overflow by inspecting the operands, which is easy to get wrong for signed values and for shifts. The trade-off is that every operation allocates a result object and does a range comparison; that is fine for checking, and the alternative (a separate `checked_*` function per operation) would double the API surface for no benefit.

## What you get

- `OverflowResult(overflow: bool, value: int)` — the mathematical result and whether it fits.
- `OverflowError` — an `ArithmeticError` subclass, exported for callers that want to raise it themselves.
- `add`, `sub`, `mul`, `div`, `neg`, `abs`, `shl`, `shr`, `pow` — each takes the operands plus `bits` and an optional `signed=True` keyword, and returns an `OverflowResult`.
- `fits`, `fits_signed`, `fits_unsigned` — range predicates.
- `min_value`, `max_value` — the inclusive bounds for a width.

Signed widths use two's complement, so `min_value(8) == -128` and `max_value(8) == 127`. Unsigned widths start at zero. `bits` must be a positive `int`; anything else raises `TypeError` or `ValueError`.

## The awkward edge

Division truncates toward zero, the way C and Rust do, not the way Python's `//` floors. So `div(-7, 2, 8).value == -3`, not `-4`. This matters because the only overflow case for division in two's complement is `min_value(bits) / -1`, and getting the rounding wrong would make that predicate disagree with the language you are emulating. `shl` and `shr` reject negative shift counts with `ValueError`; `pow` rejects negative exponents for the same reason.
