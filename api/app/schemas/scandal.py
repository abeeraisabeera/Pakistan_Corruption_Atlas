from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.entities import ConfidenceLevel, LegalStatus, ScandalCategory


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    url: str
    publisher: str
    source_type: str
    published_date: Optional[date] = None
    accessed_date: Optional[date] = None
    quote_or_claim: Optional[str] = None
    is_primary: bool = False


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_date: date
    title: str
    description: Optional[str] = None
    status_at_event: Optional[LegalStatus] = None
    source_url: Optional[str] = None
    sort_order: int = 0


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    document_type: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[date] = None


class IndividualOut(BaseModel):
    id: str
    full_name: str
    aliases: Optional[list[str]] = None
    political_party: Optional[str] = None
    position_held: Optional[str] = None
    role_description: Optional[str] = None


class InstitutionOut(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    province: Optional[str] = None
    relationship: Optional[str] = None


class FinancialLossEstimate(BaseModel):
    value: Optional[float] = None
    currency: Optional[str] = "PKR"
    confidence: Optional[str] = None


class ScandalListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_id: str
    title: str
    summary: str
    start_date: date
    end_date: Optional[date] = None
    province: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    institution: Optional[str] = None
    category: ScandalCategory
    sector: Optional[str] = None
    amount_pkr: Optional[float] = None
    amount_usd: Optional[float] = None
    amount_notes: Optional[str] = None
    current_legal_status: LegalStatus
    confidence_score: ConfidenceLevel
    case_type: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    legal_outcome: Optional[str] = None
    source_count: int = 0
    updated_at: Optional[datetime] = None


class ScandalDetail(ScandalListItem):
    government_department: Optional[str] = None
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    related_legislation: Optional[list[str]] = None
    financial_loss_estimate: Optional[FinancialLossEstimate | dict[str, Any]] = None
    last_verified: Optional[date] = None
    sources: list[SourceOut] = Field(default_factory=list)
    timeline: list[TimelineEventOut] = Field(default_factory=list)
    documents: list[DocumentOut] = Field(default_factory=list)
    individuals: list[IndividualOut] = Field(default_factory=list)
    institutions: list[InstitutionOut] = Field(default_factory=list)
    related_scandal_ids: list[str] = Field(default_factory=list)
    status_label: str = ""
    disclaimer: str = (
        "Inclusion does not imply guilt. Status labels reflect publicly documented "
        "procedural stages, not determinations of guilt by this project."
    )


class ScandalFilters(BaseModel):
    q: Optional[str] = Field(None, max_length=200)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    category: Optional[ScandalCategory] = None
    status: Optional[LegalStatus] = None
    case_type: Optional[str] = Field(None, max_length=100)
    tag: Optional[str] = Field(None, max_length=100)
    institution: Optional[str] = Field(None, max_length=300)
    individual: Optional[str] = Field(None, max_length=300)
    year_from: Optional[int] = Field(None, ge=1960, le=2026)
    year_to: Optional[int] = Field(None, ge=1960, le=2026)
    amount_min_pkr: Optional[float] = Field(None, ge=0)
    amount_max_pkr: Optional[float] = Field(None, ge=0)
    confidence: Optional[ConfidenceLevel] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedScandals(BaseModel):
    items: list[ScandalListItem]
    total: int
    page: int
    page_size: int
    pages: int


class DashboardStats(BaseModel):
    total_scandals: int
    total_estimated_pkr: float
    total_estimated_usd: float
    by_year: list[dict]
    by_province: list[dict]
    by_institution: list[dict]
    by_category: list[dict]
    by_status: list[dict]
    by_sector: list[dict]
    by_case_type: list[dict] = Field(default_factory=list)
    by_party: list[dict]
    conviction_stats: dict
    latest: list[ScandalListItem]
    disclaimer: str


class NetworkGraph(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class SourceCreate(BaseModel):
    title: str
    url: HttpUrl | str
    publisher: str
    source_type: str
    published_date: Optional[date] = None
    quote_or_claim: Optional[str] = None
    is_primary: bool = False
