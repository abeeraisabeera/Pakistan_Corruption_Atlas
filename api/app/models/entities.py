"""SQLAlchemy ORM models mirroring database/schema.sql."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


class GUID(TypeDecorator):
    """UUID on Postgres, CHAR(36) on SQLite — always expose Python str."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)


class StringList(TypeDecorator):
    """TEXT[] on Postgres, JSON array on SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(Text()))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return list(value)


class LegalStatus(str, enum.Enum):
    ALLEGATION = "allegation"
    INVESTIGATION = "investigation"
    CHARGE = "charge"
    TRIAL = "trial"
    CONVICTION = "conviction"
    ACQUITTAL = "acquittal"
    CASE_DISMISSED = "case_dismissed"
    PENDING = "pending"
    OFFICIAL_INQUIRY = "official_inquiry"
    INVESTIGATIVE_JOURNALISM_REPORT = "investigative_journalism_report"
    MIXED = "mixed"
    CIVIL_SETTLEMENT = "civil_settlement"
    CLOSED = "closed"
    SETTLED_NO_CRIMINAL_REFERENCE = "settled_no_criminal_reference"
    REFERENCE_WITHDRAWAL_SOUGHT = "reference_withdrawal_sought"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScandalCategory(str, enum.Enum):
    PROCUREMENT = "procurement"
    MONEY_LAUNDERING = "money_laundering"
    BRIBERY = "bribery"
    KICKBACKS = "kickbacks"
    LAND_SCAM = "land_scam"
    TAX_FRAUD = "tax_fraud"
    STATE_ASSET_MISUSE = "state_asset_misuse"
    ELECTION_FINANCE = "election_finance"
    PUBLIC_FUND_EMBEZZLEMENT = "public_fund_embezzlement"
    GHOST_EMPLOYEES = "ghost_employees"
    ILLEGAL_CONTRACTS = "illegal_contracts"
    INFRASTRUCTURE_FRAUD = "infrastructure_fraud"
    CUSTOMS = "customs"
    POLICE_CORRUPTION = "police_corruption"
    JUDICIAL_MISCONDUCT = "judicial_misconduct"
    MILITARY_PROCUREMENT = "military_procurement"
    STATE_OWNED_ENTERPRISES = "state_owned_enterprises"
    MISUSE_OF_AUTHORITY = "misuse_of_authority"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


# Use DB enum labels (lowercase values). native_enum=True matches schema.sql on Postgres;
# SQLite falls back to VARCHAR automatically.
LegalStatusEnum = Enum(
    LegalStatus,
    name="legal_status",
    native_enum=True,
    values_callable=_enum_values,
    validate_strings=True,
)
ConfidenceEnum = Enum(
    ConfidenceLevel,
    name="confidence_level",
    native_enum=True,
    values_callable=_enum_values,
    validate_strings=True,
)
CategoryEnum = Enum(
    ScandalCategory,
    name="scandal_category",
    native_enum=True,
    values_callable=_enum_values,
    validate_strings=True,
)


class Scandal(Base):
    __tablename__ = "scandals"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    institution: Mapped[Optional[str]] = mapped_column(String(300), index=True)
    government_department: Mapped[Optional[str]] = mapped_column(String(300))
    category: Mapped[ScandalCategory] = mapped_column(CategoryEnum, nullable=False, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(200))
    amount_pkr: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    amount_usd: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    amount_notes: Mapped[Optional[str]] = mapped_column(Text)
    current_legal_status: Mapped[LegalStatus] = mapped_column(LegalStatusEnum, nullable=False, index=True)
    court_name: Mapped[Optional[str]] = mapped_column(String(300))
    case_number: Mapped[Optional[str]] = mapped_column(String(200))
    related_legislation: Mapped[Optional[list]] = mapped_column(StringList, default=list)
    confidence_score: Mapped[ConfidenceLevel] = mapped_column(
        ConfidenceEnum, nullable=False, default=ConfidenceLevel.MEDIUM
    )
    case_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    financial_loss_estimate: Mapped[Optional[dict]] = mapped_column(JSON)
    legal_outcome: Mapped[Optional[str]] = mapped_column(String(300))
    last_verified: Mapped[Optional[date]] = mapped_column(Date)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    individuals = relationship("ScandalIndividual", back_populates="scandal", cascade="all, delete-orphan")
    institutions_rel = relationship(
        "ScandalInstitution", back_populates="scandal", cascade="all, delete-orphan"
    )
    timeline = relationship(
        "TimelineEvent", back_populates="scandal", cascade="all, delete-orphan", order_by="TimelineEvent.event_date"
    )
    sources = relationship("Source", back_populates="scandal", cascade="all, delete-orphan")
    documents = relationship("SupportingDocument", back_populates="scandal", cascade="all, delete-orphan")


class Individual(Base):
    __tablename__ = "individuals"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    aliases: Mapped[Optional[list]] = mapped_column(StringList, default=list)
    political_party: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scandals = relationship("ScandalIndividual", back_populates="individual")


class ScandalIndividual(Base):
    __tablename__ = "scandal_individuals"

    scandal_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"), primary_key=True)
    individual_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("individuals.id", ondelete="CASCADE"), primary_key=True
    )
    position_held: Mapped[Optional[str]] = mapped_column(String(300))
    role_description: Mapped[Optional[str]] = mapped_column(Text)

    scandal = relationship("Scandal", back_populates="individuals")
    individual = relationship("Individual", back_populates="scandals")


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(100))
    province: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScandalInstitution(Base):
    __tablename__ = "scandal_institutions"

    scandal_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"), primary_key=True)
    institution_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("institutions.id", ondelete="CASCADE"), primary_key=True
    )
    relationship_type: Mapped[Optional[str]] = mapped_column("relationship", String(100))

    scandal = relationship("Scandal", back_populates="institutions_rel")
    institution = relationship("Institution")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    scandal_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"), index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status_at_event: Mapped[Optional[LegalStatus]] = mapped_column(LegalStatusEnum)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    scandal = relationship("Scandal", back_populates="timeline")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    scandal_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    published_date: Mapped[Optional[date]] = mapped_column(Date)
    accessed_date: Mapped[date] = mapped_column(Date, default=date.today)
    quote_or_claim: Mapped[Optional[str]] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scandal = relationship("Scandal", back_populates="sources")


class SupportingDocument(Base):
    __tablename__ = "supporting_documents"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    scandal_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(String(100))
    url: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    published_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scandal = relationship("Scandal", back_populates="documents")


class RelatedScandal(Base):
    __tablename__ = "related_scandals"
    __table_args__ = (UniqueConstraint("scandal_id", "related_id"),)

    scandal_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"), primary_key=True)
    related_id: Mapped[str] = mapped_column(GUID(), ForeignKey("scandals.id", ondelete="CASCADE"), primary_key=True)
    relationship: Mapped[Optional[str]] = mapped_column(String(100))


class EntityLink(Base):
    __tablename__ = "entity_links"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(GUID(), nullable=False)
    link_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_pkr: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="running")
    records_found: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    log_path: Mapped[Optional[str]] = mapped_column(Text)


class SourceCache(Base):
    __tablename__ = "source_cache"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
