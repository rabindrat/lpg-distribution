import unicodedata
from difflib import SequenceMatcher


def _context_key(value):
    suffixes = {
        "city",
        "mahanagarpalika",
        "metropolitan",
        "municipality",
        "nagarpalika",
    }
    return " ".join(
        token
        for token in normalize_location_text(value).split()
        if token not in suffixes
    )


def normalize_location_text(value):
    """Normalize user/dealer text without discarding the original value."""

    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = "".join(
        char
        if (char.isalnum() or char.isspace() or unicodedata.category(char).startswith("M"))
        else " "
        for char in value
    )
    return " ".join(value.split())


def _similarity(left, right):
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


def _coverage_tole_names(coverage):
    names = [coverage.tole]
    location_unit = getattr(coverage, "location_unit", None)
    if location_unit:
        names.extend(
            [location_unit.name_en, location_unit.name_ne]
            + list(location_unit.aliases or [])
            + list(
                location_unit.alias_records.filter(is_active=True).values_list(
                    "alias", flat=True
                )
            )
        )
    return [normalize_location_text(name) for name in names if name]


def _matches_context(household, coverage):
    household_municipality = _context_key(household.municipality)
    coverage_municipality = _context_key(coverage.municipality)
    household_ward = normalize_location_text(household.ward)
    coverage_ward = normalize_location_text(coverage.ward)
    if household_municipality and coverage_municipality:
        if household_municipality != coverage_municipality:
            return False
    if household_ward and coverage_ward:
        if household_ward != coverage_ward:
            return False
    return True


def coverage_match(household, coverage):
    """Return (score, level) for a household/coverage pair, or (0, None)."""

    if not coverage.is_active or not _matches_context(household, coverage):
        return 0.0, None

    household_municipality = _context_key(household.municipality)
    household_ward = normalize_location_text(household.ward)
    coverage_municipality = _context_key(coverage.municipality)

    if coverage.location_unit_id and household.location_unit_id:
        if coverage.location_unit_id == household.location_unit_id:
            return 1.0, coverage.coverage_level
        if coverage.coverage_level == coverage.CoverageLevel.WARD:
            current = household.location_unit
            while current and current.parent_id:
                if current.parent_id == coverage.location_unit_id:
                    return 0.85, coverage.CoverageLevel.WARD
                current = current.parent

    if coverage.coverage_level == coverage.CoverageLevel.WARD:
        coverage_ward = normalize_location_text(coverage.ward)
        if (
            household_municipality
            and coverage_municipality
            and household_ward
            and household_ward == coverage_ward
        ):
            return 0.85, coverage.CoverageLevel.WARD
        return 0.0, None

    household_tole = normalize_location_text(household.tole)
    coverage_toles = _coverage_tole_names(coverage)
    if not household_tole or not coverage_toles:
        return 0.0, None
    score = max(_similarity(household_tole, coverage_tole) for coverage_tole in coverage_toles)
    required_score = 0.95 if not household_municipality or not household_ward else 0.88
    if score >= required_score:
        return score, coverage.CoverageLevel.TOLE
    return 0.0, None


def best_coverage_match(household, coverages):
    matches = [coverage_match(household, coverage) for coverage in coverages]
    matches = [match for match in matches if match[0] > 0]
    return max(matches, default=(0.0, None))
