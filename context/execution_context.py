from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4


@dataclass(slots=True)
class ExecutionContext:
    """
    Contexto compartido de una ejecución completa del ETL.
    """

    execution_id: UUID = field(default_factory=uuid4)
    started_at: datetime = field(default_factory=datetime.now)
    log_file: Path | None = None
    records_read: int = 0