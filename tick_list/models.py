import enum
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from tick_list.config import settings


class Base(DeclarativeBase):
    pass


# --- Enums ---


class LocationLevel(str, enum.Enum):
    country = "country"
    area = "area"
    crag = "crag"
    sector = "sector"


class Discipline(str, enum.Enum):
    sport = "sport"
    trad = "trad"
    boulder = "boulder"
    multipitch = "multipitch"
    ice = "ice"
    mixed = "mixed"


class AscentStyle(str, enum.Enum):
    onsight = "onsight"
    flash = "flash"
    redpoint = "redpoint"
    repeat = "repeat"
    attempt = "attempt"
    toprope = "toprope"
    hangdog = "hangdog"


class GradeSystem(str, enum.Enum):
    french = "french"
    uiaa = "uiaa"
    yds = "yds"
    font = "font"
    vscale = "vscale"


class PhotoType(str, enum.Enum):
    topo = "topo"
    send = "send"
    crag = "crag"
    action = "action"
    beta = "beta"
    selfie = "selfie"


# --- Models ---


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[LocationLevel] = mapped_column(Enum(LocationLevel), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    coordinates: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parent: Mapped["Location | None"] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Location"]] = relationship(back_populates="parent")
    routes: Mapped[list["Route"]] = relationship(back_populates="location")
    sessions: Mapped[list["Session"]] = relationship(back_populates="location")


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    grade_french: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade_original: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade_system: Mapped[GradeSystem | None] = mapped_column(Enum(GradeSystem), nullable=True)
    grade_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    discipline: Mapped[Discipline] = mapped_column(Enum(Discipline), nullable=False)
    pitches: Mapped[int] = mapped_column(Integer, default=1)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    location: Mapped["Location | None"] = relationship(back_populates="routes")
    ascents: Mapped[list["Ascent"]] = relationship(back_populates="route")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    partners: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    location: Mapped["Location | None"] = relationship(back_populates="sessions")
    ascents: Mapped[list["Ascent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="session", foreign_keys="Photo.session_id"
    )


class Ascent(Base):
    __tablename__ = "ascents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False
    )
    style: Mapped[AscentStyle] = mapped_column(Enum(AscentStyle), nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="ascents")
    route: Mapped["Route"] = relationship(back_populates="ascents")
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="ascent", foreign_keys="Photo.ascent_id"
    )


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_type: Mapped[PhotoType | None] = mapped_column(Enum(PhotoType), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True
    )
    ascent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ascents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session | None"] = relationship(back_populates="photos", foreign_keys=[session_id])
    ascent: Mapped["Ascent | None"] = relationship(back_populates="photos", foreign_keys=[ascent_id])


# --- Async Engine ---

engine = create_async_engine(settings.database_url, echo=False, pool_size=5, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
