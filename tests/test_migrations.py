"""Test Alembic migrations against real PostGIS. Requires Docker running."""

import uuid

import pytest
from alembic import command
from alembic.config import Config
from geoalchemy2 import WKTElement
from sqlalchemy import text

from tick_list.models import Location, LocationLevel

pytestmark = pytest.mark.requires_docker


@pytest.fixture
def alembic_config(postgres_container):
    url = postgres_container.get_connection_url()
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_upgrade(alembic_config):
    command.upgrade(alembic_config, "head")


def test_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")


async def test_location_spatial_insert(db_session):
    loc = Location(
        id=uuid.uuid4(),
        name="Frankenjura",
        level=LocationLevel.area,
        coordinates=WKTElement("POINT(11.4 49.7)", srid=4326),
    )
    db_session.add(loc)
    await db_session.commit()

    result = await db_session.execute(
        text("SELECT ST_AsText(coordinates) FROM locations WHERE name = 'Frankenjura'")
    )
    row = result.scalar_one()
    assert "11.4" in row
    assert "49.7" in row
