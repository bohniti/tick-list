"""Grade normalization module for climbing grades.

Converts between French, UIAA, YDS, Font, and V-scale grading systems.
French is the canonical system (D-02). Provides numeric scoring for ordering.
Bouldering grades use a separate numeric axis from route grades (D-03).

Pure Python, no external dependencies.
"""

from __future__ import annotations

import re

# --- Conversion mappings ---

UIAA_TO_FRENCH: dict[str, str] = {
    "4": "5a",
    "4+": "5b",
    "5-": "5c",
    "5": "6a",
    "5+": "6a+",
    "6-": "6b",
    "6": "6b+",
    "6+": "6c",
    "7-": "6c+",
    "7": "7a",
    "7+": "7a+",
    "8-": "7b",
    "8": "7b+",
    "8+": "7c",
    "9-": "7c+",
    "9": "8a",
    "9+": "8a+",
    # Slash grades (D-04)
    "7+/8-": "7a+",
    "8+/9-": "7c+",
    "6/6+": "6b+",
    "7/7+": "7a",
}

YDS_TO_FRENCH: dict[str, str] = {
    "5.6": "5b",
    "5.7": "5c",
    "5.8": "6a",
    "5.9": "6a+",
    "5.10a": "6b",
    "5.10b": "6b+",
    "5.10c": "6c",
    "5.10d": "6c+",
    "5.11a": "7a",
    "5.11b": "7a+",
    "5.11c": "7b",
    "5.11d": "7b+",
    "5.12a": "7c",
    "5.12b": "7c+",
    "5.12c": "8a",
    "5.12d": "8a+",
    "5.13a": "8b",
    "5.13b": "8b+",
    "5.13c": "8c",
    "5.13d": "8c+",
    "5.14a": "9a",
    "5.14b": "9a+",
}

FRENCH_NUMERIC: dict[str, float] = {
    "4a": 1.0,
    "4b": 1.5,
    "4c": 2.0,
    "5a": 2.5,
    "5a+": 2.7,
    "5b": 3.0,
    "5b+": 3.2,
    "5c": 3.5,
    "5c+": 3.7,
    "6a": 4.0,
    "6a+": 4.3,
    "6b": 4.5,
    "6b+": 4.7,
    "6c": 5.0,
    "6c+": 5.3,
    "7a": 5.5,
    "7a+": 5.7,
    "7b": 6.0,
    "7b+": 6.3,
    "7c": 6.5,
    "7c+": 6.7,
    "8a": 7.0,
    "8a+": 7.3,
    "8b": 7.5,
    "8b+": 7.7,
    "8c": 8.0,
    "8c+": 8.3,
    "9a": 9.0,
    "9a+": 9.5,
}

FONT_NUMERIC: dict[str, float] = {
    "4": 1.0,
    "5": 2.0,
    "5+": 2.5,
    "6A": 3.0,
    "6A+": 3.3,
    "6B": 3.5,
    "6B+": 3.7,
    "6C": 4.0,
    "6C+": 4.3,
    "7A": 4.5,
    "7A+": 4.7,
    "7B": 5.0,
    "7B+": 5.3,
    "7C": 5.5,
    "7C+": 5.7,
    "8A": 6.0,
    "8A+": 6.3,
    "8B": 6.5,
    "8B+": 6.7,
    "8C": 7.0,
    "8C+": 7.3,
}

VSCALE_TO_FONT: dict[str, str] = {
    "V0": "4",
    "V1": "5",
    "V2": "5+",
    "V3": "6A",
    "V4": "6B",
    "V5": "6C",
    "V6": "7A",
    "V7": "7A+",
    "V8": "7B+",
    "V9": "7C",
    "V10": "7C+",
    "V11": "8A",
    "V12": "8A+",
    "V13": "8B",
    "V14": "8B+",
    "V15": "8C",
    "V16": "8C+",
}

# --- UIAA pattern detection ---

# Matches: single digit optionally followed by +/- or slash notation like "7+/8-"
_UIAA_PATTERN = re.compile(r"^\d[+-]?(/\d[+-]?)?$")


def _is_uiaa(grade: str) -> bool:
    """Return True if grade matches UIAA pattern.

    UIAA grades are a single digit optionally followed by +/- modifier,
    or slash grades like "7+/8-", "6/6+".
    """
    return bool(_UIAA_PATTERN.match(grade))


def _is_aid_slash(grade: str) -> bool:
    """Detect aid climbing notation like '7/A' (free grade / aid grade)."""
    if "/" not in grade:
        return False
    parts = grade.split("/")
    if len(parts) != 2:
        return False
    # Aid grades start with 'A' followed by a digit (A0, A1, A2, etc.)
    return bool(re.match(r"^A\d?$", parts[1]))


# --- Public functions ---


def normalize_to_french(grade: str, system: str = "auto") -> str:
    """Convert a climbing grade to French notation.

    Args:
        grade: The grade string to convert (e.g., "7+", "5.10a", "6b+").
        system: Grading system - "uiaa", "yds", or "auto" (default).
            Auto-detection: "5." prefix -> YDS, UIAA pattern match -> UIAA,
            otherwise returns grade unchanged (assumed already French).

    Returns:
        French grade string, or the original grade if unknown.
    """
    grade = grade.strip()

    # Handle aid notation like "7/A" -> extract free climbing component "7"
    if _is_aid_slash(grade):
        free_part = grade.split("/")[0].strip()
        return UIAA_TO_FRENCH.get(free_part, free_part.lower())

    if system == "uiaa":
        return UIAA_TO_FRENCH.get(grade, grade)

    if system == "yds":
        return YDS_TO_FRENCH.get(grade, grade)

    if system == "auto":
        # YDS starts with "5."
        if grade.startswith("5."):
            return YDS_TO_FRENCH.get(grade, grade)
        # Check UIAA pattern (must check lookup table too for slash grades)
        if grade in UIAA_TO_FRENCH:
            return UIAA_TO_FRENCH[grade]
        if _is_uiaa(grade):
            return UIAA_TO_FRENCH.get(grade, grade)
        # Assume already French
        return grade

    return grade


def grade_to_numeric(french_grade: str, discipline: str = "route") -> float:
    """Return numeric score for a French grade.

    Args:
        french_grade: French grade string (e.g., "6a", "7b+", "6a/b").
        discipline: "route" (default) uses FRENCH_NUMERIC,
            "boulder" uses FONT_NUMERIC.

    Returns:
        Numeric score (float). 0.0 for unknown grades.
        For slash grades like "6a/b", returns the midpoint of both grades.
    """
    french_grade = french_grade.strip()
    lookup = FONT_NUMERIC if discipline == "boulder" else FRENCH_NUMERIC

    # Handle French slash grades like "6a/b" -> midpoint of "6a" and "6b"
    if "/" in french_grade:
        parts = french_grade.split("/")
        if len(parts) == 2:
            left = parts[0].strip()
            right = parts[1].strip()
            # Expand shorthand: "6a/b" -> "6a" and "6b"
            if len(right) == 1:
                # Take the prefix from the left grade (everything except the last char)
                right = left[:-1] + right
            scores = [lookup.get(left, 0.0), lookup.get(right, 0.0)]
            if all(s > 0 for s in scores):
                return sum(scores) / len(scores)
            # If one side is unknown, return whatever we have
            return max(scores)

    return lookup.get(french_grade, 0.0)


def boulder_grade_to_numeric(font_grade: str) -> float:
    """Return numeric score for a bouldering grade.

    Accepts Font grades (6A, 7B+, etc.) or V-scale (V0-V16).
    V-scale is converted to Font first via VSCALE_TO_FONT.

    Args:
        font_grade: Font or V-scale grade string.

    Returns:
        Numeric score on the bouldering axis. 0.0 for unknown grades.
    """
    font_grade = font_grade.strip()

    # Convert V-scale to Font first
    if font_grade in VSCALE_TO_FONT:
        font_grade = VSCALE_TO_FONT[font_grade]

    return FONT_NUMERIC.get(font_grade, 0.0)
