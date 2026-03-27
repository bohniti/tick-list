"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-27 11:48:47.236187

"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables, PostGIS extension, enums, and updated_at triggers."""
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # Create updated_at trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)

    # Create enum types
    locationlevel = postgresql.ENUM(
        "country", "area", "crag", "sector", name="locationlevel", create_type=False
    )
    discipline = postgresql.ENUM(
        "sport", "trad", "boulder", "multipitch", "ice", "mixed",
        name="discipline", create_type=False,
    )
    ascentstyle = postgresql.ENUM(
        "onsight", "flash", "redpoint", "repeat", "attempt", "toprope", "hangdog",
        name="ascentstyle", create_type=False,
    )
    gradesystem = postgresql.ENUM(
        "french", "uiaa", "yds", "font", "vscale", name="gradesystem", create_type=False
    )
    phototype = postgresql.ENUM(
        "topo", "send", "crag", "action", "beta", "selfie", name="phototype", create_type=False
    )

    locationlevel.create(op.get_bind(), checkfirst=True)
    discipline.create(op.get_bind(), checkfirst=True)
    ascentstyle.create(op.get_bind(), checkfirst=True)
    gradesystem.create(op.get_bind(), checkfirst=True)
    phototype.create(op.get_bind(), checkfirst=True)

    # --- locations ---
    op.create_table(
        "locations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", locationlevel, nullable=False),
        sa.Column("parent_id", sa.UUID(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column(
            "coordinates",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- routes ---
    op.create_table(
        "routes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("grade_french", sa.String(20), nullable=True),
        sa.Column("grade_original", sa.String(20), nullable=True),
        sa.Column("grade_system", gradesystem, nullable=True),
        sa.Column("grade_numeric", sa.Float(), nullable=True),
        sa.Column("discipline", discipline, nullable=False),
        sa.Column("pitches", sa.Integer(), default=1),
        sa.Column("location_id", sa.UUID(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- sessions ---
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_id", sa.UUID(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("partners", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- ascents ---
    op.create_table(
        "ascents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("session_id", sa.UUID(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id"), nullable=False),
        sa.Column("style", ascentstyle, nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- photos ---
    op.create_table(
        "photos",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=True),
        sa.Column("photo_type", phototype, nullable=True),
        sa.Column("session_id", sa.UUID(), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("ascent_id", sa.UUID(), sa.ForeignKey("ascents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create updated_at triggers for all tables
    for table in ["locations", "routes", "sessions", "ascents", "photos"]:
        op.execute(f"""
        CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables, triggers, enums, and PostGIS extension."""
    # Drop triggers first
    for table in ["photos", "ascents", "sessions", "routes", "locations"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop tables in reverse dependency order
    op.drop_table("photos")
    op.drop_table("ascents")
    op.drop_table("sessions")
    op.drop_table("routes")
    op.drop_table("locations")

    # Drop enum types
    for enum_name in ["phototype", "ascentstyle", "gradesystem", "discipline", "locationlevel"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")

    # Drop PostGIS extension
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE;")
