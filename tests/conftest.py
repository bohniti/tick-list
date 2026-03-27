import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from tick_list.models import Base

POSTGIS_IMAGE = "postgis/postgis:17-3.6"


@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostGIS container for the test session. Requires Docker running."""
    with PostgresContainer(POSTGIS_IMAGE) as container:
        yield container


@pytest.fixture
async def db_engine(postgres_container):
    """Create async engine connected to the test container."""
    url = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    # Remove psycopg2 driver if present in URL
    url = url.replace("postgresql+asyncpg+psycopg2://", "postgresql+asyncpg://")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS postgis;")
        )
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Provide an async session for database tests."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
