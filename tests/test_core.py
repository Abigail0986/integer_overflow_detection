import unittest

from integer_overflow_detection import (
    OverflowError,
    OverflowResult,
    add,
    sub,
    mul,
    div,
    neg,
    abs,
    shl,
    shr,
    pow,
    fits,
    fits_signed,
    fits_unsigned,
    min_value,
    max_value,
)


class TestBounds(unittest.TestCase):
    def test_signed_bounds(self):
        self.assertEqual(min_value(8), -128)
        self.assertEqual(max_value(8), 127)
        self.assertEqual(min_value(32), -(2 ** 31))
        self.assertEqual(max_value(32), 2 ** 31 - 1)

    def test_unsigned_bounds(self):
        self.assertEqual(min_value(8, signed=False), 0)
        self.assertEqual(max_value(8, signed=False), 255)

    def test_bits_must_be_positive(self):
        with self.assertRaises(ValueError):
            min_value(0)
        with self.assertRaises(ValueError):
            max_value(-1)

    def test_bits_must_be_int(self):
        with self.assertRaises(TypeError):
            min_value(8.0)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            max_value(True)  # bool is not accepted as a width


class TestFits(unittest.TestCase):
    def test_signed_edges(self):
        self.assertTrue(fits(127, 8))
        self.assertTrue(fits(-128, 8))
        self.assertFalse(fits(128, 8))
        self.assertFalse(fits(-129, 8))

    def test_unsigned_edges(self):
        self.assertTrue(fits(255, 8, signed=False))
        self.assertTrue(fits(0, 8, signed=False))
        self.assertFalse(fits(-1, 8, signed=False))
        self.assertFalse(fits(256, 8, signed=False))

    def test_convenience_wrappers(self):
        self.assertTrue(fits_signed(127, 8))
        self.assertFalse(fits_signed(128, 8))
        self.assertTrue(fits_unsigned(255, 8))
        self.assertFalse(fits_unsigned(256, 8))


class TestArithmetic(unittest.TestCase):
    def test_add_no_overflow(self):
        r = add(100, 27, 8)
        self.assertIsInstance(r, OverflowResult)
        self.assertFalse(r.overflow)
        self.assertEqual(r.value, 127)

    def test_add_overflow(self):
        r = add(100, 28, 8)
        self.assertTrue(r.overflow)
        self.assertEqual(r.value, 128)

    def test_add_unsigned(self):
        self.assertFalse(add(200, 55, 8, signed=False).overflow)
        self.assertTrue(add(200, 56, 8, signed=False).overflow)

    def test_sub_overflow(self):
        r = sub(-128, 1, 8)
        self.assertTrue(r.overflow)
        self.assertEqual(r.value, -129)

    def test_mul_overflow(self):
        self.assertFalse(mul(11, 11, 8).overflow)
        self.assertTrue(mul(12, 11, 8).overflow)

    def test_mul_negative(self):
        self.assertFalse(mul(-11, 11, 8).overflow)
        self.assertTrue(mul(-12, 11, 8).overflow)

    def test_div_truncates_toward_zero(self):
        # -7 / 2 is -3 in C, not -4 as Python's // would give.
        r = div(-7, 2, 8)
        self.assertFalse(r.overflow)
        self.assertEqual(r.value, -3)

    def test_div_min_by_minus_one_overflows(self):
        r = div(-128, -1, 8)
        self.assertTrue(r.overflow)
        self.assertEqual(r.value, 128)

    def test_div_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            div(1, 0, 8)

    def test_neg_overflow(self):
        self.assertFalse(neg(127, 8).overflow)
        self.assertTrue(neg(-128, 8).overflow)

    def test_abs_overflow(self):
        self.assertFalse(abs(-127, 8).overflow)
        self.assertTrue(abs(-128, 8).overflow)

    def test_shl(self):
        self.assertFalse(shl(1, 6, 8).overflow)
        self.assertTrue(shl(1, 7, 8).overflow)
        with self.assertRaises(ValueError):
            shl(1, -1, 8)

    def test_shr_never_overflows(self):
        self.assertFalse(shr(-128, 1, 8).overflow)
        self.assertEqual(shr(-128, 1, 8).value, -64)
        with self.assertRaises(ValueError):
            shr(1, -1, 8)

    def test_pow(self):
        self.assertFalse(pow(2, 6, 8).overflow)
        self.assertTrue(pow(2, 7, 8).overflow)
        with self.assertRaises(ValueError):
            pow(2, -1, 8)

    def test_overflow_error_is_arithmetic_error(self):
        self.assertTrue(issubclass(OverflowError, ArithmeticError))


if __name__ == "__main__":
    unittest.main()
