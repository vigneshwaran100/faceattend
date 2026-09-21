from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EndOfDaySummary:
    attendance_date: date
    present: int
    half_day: int
    incomplete: int
    absent: int
    total_processed: int
