from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScannerProcessingResult:
    success: bool
    message: str
    employee_id: Optional[str] = None