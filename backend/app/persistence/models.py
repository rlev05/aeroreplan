from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.persistence.database import Base

class AnalysisCaseORM(Base):
    __tablename__ = "analysis_cases"

    case_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    operating_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    seed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    disruption_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    aircraft_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    recommended_strategy: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    disruption_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    comparison_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    decision_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )


