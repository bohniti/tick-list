"""Tests for grade normalization module.

Covers: UIAA->French, YDS->French, auto-detection, numeric scoring,
bouldering grades, slash grades, edge cases, round-trips, monotonicity.
"""

from __future__ import annotations

import pytest

from tick_list.grades import (
    FONT_NUMERIC,
    FRENCH_NUMERIC,
    UIAA_TO_FRENCH,
    VSCALE_TO_FONT,
    YDS_TO_FRENCH,
    boulder_grade_to_numeric,
    grade_to_numeric,
    normalize_to_french,
)


# --- UIAA to French conversion (D-01, D-02) ---


class TestUIAAToFrench:
    def test_5_plus(self):
        assert normalize_to_french("5+", "uiaa") == "6a+"

    def test_6_minus(self):
        assert normalize_to_french("6-", "uiaa") == "6b"

    def test_7(self):
        assert normalize_to_french("7", "uiaa") == "7a"

    def test_8_minus(self):
        assert normalize_to_french("8-", "uiaa") == "7b"

    def test_8_plus(self):
        assert normalize_to_french("8+", "uiaa") == "7c"

    def test_9_minus(self):
        assert normalize_to_french("9-", "uiaa") == "7c+"


# --- UIAA slash grades (D-04) ---


class TestUIAASlashGrades:
    def test_7_plus_8_minus(self):
        assert normalize_to_french("7+/8-", "uiaa") == "7a+"

    def test_8_plus_9_minus(self):
        assert normalize_to_french("8+/9-", "uiaa") == "7c+"

    def test_6_6_plus(self):
        assert normalize_to_french("6/6+", "uiaa") == "6b+"


# --- YDS to French conversion ---


class TestYDSToFrench:
    def test_5_10a(self):
        assert normalize_to_french("5.10a", "yds") == "6b"

    def test_5_11a(self):
        assert normalize_to_french("5.11a", "yds") == "7a"

    def test_5_12a(self):
        assert normalize_to_french("5.12a", "yds") == "7c"

    def test_5_9(self):
        assert normalize_to_french("5.9", "yds") == "6a+"


# --- Auto-detection ---


class TestAutoDetection:
    def test_yds_auto(self):
        """YDS detected by '5.' prefix."""
        assert normalize_to_french("5.10a") == "6b"

    def test_uiaa_auto(self):
        """UIAA detected by pattern match."""
        assert normalize_to_french("7+") == "6c+"

    def test_french_passthrough(self):
        """Already French returns unchanged."""
        assert normalize_to_french("6b+") == "6b+"


# --- Numeric scoring (D-01, monotonically increasing) ---


class TestNumericScoring:
    def test_6a_equals_4(self):
        assert grade_to_numeric("6a") == 4.0

    def test_7a_equals_5_5(self):
        assert grade_to_numeric("7a") == 5.5

    def test_8a_equals_7(self):
        assert grade_to_numeric("8a") == 7.0

    def test_ordering(self):
        assert grade_to_numeric("5a") < grade_to_numeric("5b") < grade_to_numeric("6a")

    def test_monotonic_across_all_grades(self):
        """All consecutive French grades have strictly increasing numeric values."""
        sorted_grades = sorted(FRENCH_NUMERIC.keys(), key=lambda g: FRENCH_NUMERIC[g])
        scores = [FRENCH_NUMERIC[g] for g in sorted_grades]
        for i in range(1, len(scores)):
            assert scores[i] > scores[i - 1], (
                f"Not monotonic: {sorted_grades[i-1]}={scores[i-1]} >= {sorted_grades[i]}={scores[i]}"
            )


# --- French slash grade scoring ---


class TestFrenchSlashGrades:
    def test_6a_b_midpoint(self):
        expected = (grade_to_numeric("6a") + grade_to_numeric("6b")) / 2
        assert grade_to_numeric("6a/b") == expected


# --- Bouldering grades (D-03 - separate axis) ---


class TestBoulderingGrades:
    def test_font_6a_has_score(self):
        assert boulder_grade_to_numeric("6A") > 0

    def test_v_scale_conversion(self):
        """V-scale converts to Font then scores."""
        assert boulder_grade_to_numeric("V3") == FONT_NUMERIC["6A"]

    def test_v0_through_v16(self):
        """All V-scale grades produce nonzero scores."""
        for v_grade in VSCALE_TO_FONT:
            assert boulder_grade_to_numeric(v_grade) > 0, f"{v_grade} should have a score"


# --- Edge cases ---


class TestEdgeCases:
    def test_unknown_grade_numeric(self):
        assert grade_to_numeric("unknown") == 0.0

    def test_unknown_grade_normalize(self):
        assert normalize_to_french("unknown_grade") == "unknown_grade"

    def test_whitespace_stripped(self):
        assert normalize_to_french("  7+  ") == "6c+"

    def test_7_slash_a_aid_notation(self):
        """The '7/A' aid notation returns the free climbing grade '7a' for the '7' component."""
        result = normalize_to_french("7/A")
        assert result == "7a"


# --- Round-trip guarantees ---


class TestRoundTrips:
    def test_uiaa_roundtrip(self):
        """Every grade in UIAA_TO_FRENCH normalizes to a grade with nonzero numeric score."""
        for uiaa_grade, french_grade in UIAA_TO_FRENCH.items():
            score = grade_to_numeric(french_grade)
            assert score > 0, f"UIAA {uiaa_grade} -> French {french_grade} -> score {score}"

    def test_yds_roundtrip(self):
        """Every grade in YDS_TO_FRENCH normalizes to a grade with nonzero numeric score."""
        for yds_grade, french_grade in YDS_TO_FRENCH.items():
            score = grade_to_numeric(french_grade)
            assert score > 0, f"YDS {yds_grade} -> French {french_grade} -> score {score}"
