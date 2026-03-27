"""Test model structure and enum definitions. No database required."""

from tick_list.models import (
    Ascent,
    AscentStyle,
    Base,
    Discipline,
    GradeSystem,
    Location,
    LocationLevel,
    Photo,
    PhotoType,
    Route,
    Session,
)


def test_all_tables_registered():
    tables = set(Base.metadata.tables.keys())
    assert tables == {"locations", "routes", "sessions", "ascents", "photos"}


def test_discipline_enum_values():
    values = {d.value for d in Discipline}
    assert values == {"sport", "trad", "boulder", "multipitch", "ice", "mixed"}


def test_ascent_style_enum_values():
    values = {s.value for s in AscentStyle}
    assert values == {"onsight", "flash", "redpoint", "repeat", "attempt", "toprope", "hangdog"}


def test_location_level_enum_values():
    values = {level.value for level in LocationLevel}
    assert values == {"country", "area", "crag", "sector"}


def test_grade_system_enum_values():
    values = {g.value for g in GradeSystem}
    assert values == {"french", "uiaa", "yds", "font", "vscale"}


def test_photo_type_enum_values():
    values = {p.value for p in PhotoType}
    assert values == {"topo", "send", "crag", "action", "beta", "selfie"}


def test_route_has_required_columns():
    cols = {c.name for c in Route.__table__.columns}
    assert "name" in cols
    assert "grade_french" in cols
    assert "grade_original" in cols
    assert "grade_system" in cols
    assert "grade_numeric" in cols
    assert "discipline" in cols
    assert "pitches" in cols
    assert "location_id" in cols


def test_location_has_self_referential_fk():
    cols = {c.name for c in Location.__table__.columns}
    assert "parent_id" in cols
    assert "coordinates" in cols
    assert "level" in cols


def test_session_has_partners_array():
    cols = {c.name for c in Session.__table__.columns}
    assert "partners" in cols
    assert "conditions" in cols
    assert "date" in cols


def test_ascent_has_style_and_rating():
    cols = {c.name for c in Ascent.__table__.columns}
    assert "style" in cols
    assert "rating" in cols
    assert "session_id" in cols
    assert "route_id" in cols


def test_all_tables_have_uuid_pk():
    for table in Base.metadata.tables.values():
        pk_cols = [c for c in table.columns if c.primary_key]
        assert len(pk_cols) == 1, f"Table {table.name} should have exactly 1 PK column"
        assert "uuid" in str(pk_cols[0].type).lower(), f"Table {table.name} PK should be UUID"


def test_all_tables_have_timestamps():
    for table in Base.metadata.tables.values():
        col_names = {c.name for c in table.columns}
        assert "created_at" in col_names, f"Table {table.name} missing created_at"
        assert "updated_at" in col_names, f"Table {table.name} missing updated_at"


def test_photo_has_session_and_ascent_fks():
    cols = {c.name for c in Photo.__table__.columns}
    assert "session_id" in cols
    assert "ascent_id" in cols
    assert "filename" in cols
    assert "photo_type" in cols
