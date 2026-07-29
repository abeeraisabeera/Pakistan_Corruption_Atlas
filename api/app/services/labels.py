"""Status display labels — never present allegations as established fact."""
from app.models.entities import LegalStatus

STATUS_LABELS: dict[LegalStatus, str] = {
    LegalStatus.ALLEGATION: "Alleged",
    LegalStatus.INVESTIGATION: "Under Investigation",
    LegalStatus.CHARGE: "Charged",
    LegalStatus.TRIAL: "On Trial",
    LegalStatus.CONVICTION: "Convicted",
    LegalStatus.ACQUITTAL: "Acquitted",
    LegalStatus.CASE_DISMISSED: "Case Dismissed",
    LegalStatus.PENDING: "Pending",
    LegalStatus.OFFICIAL_INQUIRY: "Official Inquiry",
    LegalStatus.INVESTIGATIVE_JOURNALISM_REPORT: "Investigative Journalism Report",
    LegalStatus.MIXED: "Mixed Outcomes",
    LegalStatus.CIVIL_SETTLEMENT: "Civil Settlement",
    LegalStatus.CLOSED: "Closed",
    LegalStatus.SETTLED_NO_CRIMINAL_REFERENCE: "Settled (No Criminal Reference)",
    LegalStatus.REFERENCE_WITHDRAWAL_SOUGHT: "Reference Withdrawal Sought",
}

DISCLAIMER = (
    "This project aggregates publicly available information from reputable and official "
    "sources for research, transparency, and educational purposes. Inclusion in the "
    "database does not imply guilt. Users should consult the cited primary sources and "
    "court records for authoritative information."
)


def status_label(status: LegalStatus | str, override: str | None = None) -> str:
    if override:
        return override
    if isinstance(status, str):
        try:
            status = LegalStatus(status)
        except ValueError:
            return status.replace("_", " ").title()
    return STATUS_LABELS.get(status, str(status))
