import logging
from datetime import date, datetime, time
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.models.attendance import Attendance
from app.models.attendance_summary import AttendanceSummary
from app.models.daily_attendance_report import (
    DailyAttendanceItem,
    DailyAttendanceReport,
)
from app.models.employee import Employee
from app.models.end_of_day_summary import EndOfDaySummary
from app.repositories.attendance_repository import (
    AttendanceRepository,
)

logger = logging.getLogger(__name__)


class AttendanceService:
    FULL_DAY_HOURS = 9.0
    HALF_DAY_HOURS = 5.0
    REQUIRED_WORKING_HOURS = 9.0
    TIMEZONE = ZoneInfo("Asia/Kolkata")

    def __init__(
        self,
        repository: AttendanceRepository,
    ) -> None:
        self._repository = repository

    def check_in(
        self,
        employee_id: str,
        *,
        now: datetime | None = None,
    ) -> Attendance:
        current_time = now or datetime.now(
            self.TIMEZONE
        )

        attendance_date = current_time.date()

        existing = (
            self._repository.get_by_employee_and_date(
                employee_id,
                attendance_date,
            )
        )

        # First check-in is permanent for the day.
        if existing is not None:
            logger.debug(
                "Existing check-in found for employee_id=%s on date=%s",
                employee_id,
                attendance_date,
            )
            return existing

        attendance = Attendance(
            attendance_id=str(uuid4()),
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in=current_time.time(),
            check_out=None,
            status="in_progress",
            created_at=current_time,
            updated_at=current_time,
        )

        created = self._repository.create(attendance)

        logger.info(
            "New check-in created | employee_id=%s | date=%s | time=%s",
            employee_id,
            attendance_date,
            attendance.check_in,
        )

        return created

    def check_out(
        self,
        employee_id: str,
        *,
        now: datetime | None = None,
    ) -> Attendance:
        current_time = now or datetime.now(
            self.TIMEZONE
        )

        existing = (
            self._repository.get_by_employee_and_date(
                employee_id,
                current_time.date(),
            )
        )

        if existing is None:
            raise ValueError(
                f"No attendance record found for {employee_id}"
            )

        if existing.check_in is None:
            raise ValueError(
                f"Check-in time missing for {employee_id}"
            )

        # Latest inside scanner scan always wins.
        updated = Attendance(
            attendance_id=existing.attendance_id,
            employee_id=existing.employee_id,
            attendance_date=existing.attendance_date,
            check_in=existing.check_in,
            check_out=current_time.time(),
            status="in_progress",
            created_at=existing.created_at,
            updated_at=current_time,
        )

        result = self._repository.update(updated)

        logger.info(
            "Check-out updated | employee_id=%s | date=%s | check_out=%s",
            employee_id,
            current_time.date(),
            updated.check_out,
        )

        return result

    def finalize_attendance(
        self,
        employee_id: str,
        attendance_date: date,
    ) -> Attendance:
        existing = (
            self._repository.get_by_employee_and_date(
                employee_id,
                attendance_date,
            )
        )

        if existing is None:
            raise ValueError(
                f"No attendance found for {employee_id}"
            )

        if existing.check_in is None:
            raise ValueError(
                f"Check-in missing for {employee_id}"
            )

        if existing.check_out is None:
            status = "incomplete"
        else:
            worked_hours = self.calculate_working_hours(
                existing.check_in,
                existing.check_out,
            )

            if worked_hours >= self.FULL_DAY_HOURS:
                status = "present"
            elif worked_hours >= self.HALF_DAY_HOURS:
                status = "half_day"
            else:
                status = "incomplete"

        finalized = Attendance(
            attendance_id=existing.attendance_id,
            employee_id=existing.employee_id,
            attendance_date=existing.attendance_date,
            check_in=existing.check_in,
            check_out=existing.check_out,
            status=status,
            created_at=existing.created_at,
            updated_at=datetime.now(self.TIMEZONE),
        )

        result = self._repository.update(finalized)

        logger.info(
            "Attendance finalized | employee_id=%s | date=%s | status=%s",
            employee_id,
            attendance_date,
            status,
        )

        return result

    def finalize_day(
        self,
        attendance_date: date,
    ) -> list[Attendance]:
        records = self._repository.get_all_by_date(
            attendance_date
        )

        finalized_records = [
            self.finalize_attendance(
                record.employee_id,
                attendance_date,
            )
            for record in records
            if record.status == "in_progress"
        ]

        logger.info(
            "Day attendance finalization completed | date=%s | count=%d",
            attendance_date,
            len(finalized_records),
        )

        return finalized_records

    def get_attendance_history(
        self,
        employee_id: str,
    ) -> list[Attendance]:
        return self._repository.get_all_by_employee(
            employee_id
        )

    def get_attendance_history_by_date_range(
        self,
        employee_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Attendance]:
        return self._repository.get_by_employee_and_date_range(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def calculate_working_hours(
        check_in: time,
        check_out: time,
    ) -> float:
        check_in_seconds = (
            check_in.hour * 3600
            + check_in.minute * 60
            + check_in.second
        )

        check_out_seconds = (
            check_out.hour * 3600
            + check_out.minute * 60
            + check_out.second
        )

        worked_seconds = (
            check_out_seconds - check_in_seconds
        )

        if worked_seconds < 0:
            raise ValueError(
                "Check-out cannot be before check-in"
            )

        return worked_seconds / 3600

    def mark_absent(
        self,
        employee_id: str,
        attendance_date: date,
        *,
        now: datetime | None = None,
    ) -> Attendance:
        current_time = now or datetime.now(self.TIMEZONE)

        existing = self._repository.get_by_employee_and_date(
            employee_id,
            attendance_date,
        )

        if existing is not None:
            logger.debug(
                "Attendance record already exists for employee_id=%s on date=%s | status=%s",
                employee_id,
                attendance_date,
                existing.status,
            )
            return existing

        attendance = Attendance(
            attendance_id=str(uuid4()),
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in=None,
            check_out=None,
            status="absent",
            created_at=current_time,
            updated_at=current_time,
        )

        created = self._repository.create(attendance)

        logger.info(
            "Absent record created | employee_id=%s | date=%s",
            employee_id,
            attendance_date,
        )

        return created

    def mark_absent_employees(
        self,
        active_employees: list[Employee],
        attendance_date: date,
        *,
        now: datetime | None = None,
    ) -> list[Attendance]:
        current_time = now or datetime.now(self.TIMEZONE)
        absent_records: list[Attendance] = []

        for employee in active_employees:
            existing = self._repository.get_by_employee_and_date(
                employee.employee_id,
                attendance_date,
            )

            if existing is None:
                absent_record = self.mark_absent(
                    employee_id=employee.employee_id,
                    attendance_date=attendance_date,
                    now=current_time,
                )
                absent_records.append(absent_record)

        logger.info(
            "Absent marking completed | date=%s | marked_count=%d | total_active=%d",
            attendance_date,
            len(absent_records),
            len(active_employees),
        )

        return absent_records

    def process_end_of_day(
        self,
        active_employees: list[Employee],
        attendance_date: date,
        *,
        now: datetime | None = None,
    ) -> EndOfDaySummary:
        current_time = now or datetime.now(self.TIMEZONE)

        # 1. Finalize all in-progress attendance records for the date
        self.finalize_day(attendance_date)

        # 2. Mark active employees with no record as ABSENT
        self.mark_absent_employees(
            active_employees=active_employees,
            attendance_date=attendance_date,
            now=current_time,
        )

        # 3. Retrieve all records for this date to compute exact final counts
        all_records = self._repository.get_all_by_date(attendance_date)

        present_count = sum(
            1 for r in all_records if r.status in ("present", "PRESENT")
        )
        half_day_count = sum(
            1 for r in all_records if r.status in ("half_day", "HALF_DAY")
        )
        incomplete_count = sum(
            1 for r in all_records if r.status in ("incomplete", "INCOMPLETE")
        )
        absent_count = sum(
            1 for r in all_records if r.status in ("absent", "ABSENT")
        )

        logger.info(
            "End-of-day processing completed | date=%s | total=%d | "
            "present=%d | half_day=%d | incomplete=%d | absent=%d",
            attendance_date,
            len(all_records),
            present_count,
            half_day_count,
            incomplete_count,
            absent_count,
        )

        return EndOfDaySummary(
            attendance_date=attendance_date,
            present=present_count,
            half_day=half_day_count,
            incomplete=incomplete_count,
            absent=absent_count,
            total_processed=len(all_records),
        )

    def get_attendance_summary(
        self,
        employee_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AttendanceSummary:
        records = self._repository.get_by_employee_and_date_range(
            employee_id,
            start_date,
            end_date,
        )

        present_days = sum(
            1
            for record in records
            if record.status == "present"
        )

        half_days = sum(
            1
            for record in records
            if record.status == "half_day"
        )

        in_progress_days = sum(
            1
            for record in records
            if record.status == "in_progress"
        )

        absent_days = sum(
            1
            for record in records
            if record.status in ("absent", "ABSENT")
        )

        incomplete_days = sum(
            1
            for record in records
            if record.status in ("incomplete", "INCOMPLETE")
        )

        total_working_hours = sum(
            self.calculate_working_hours(
                record.check_in,
                record.check_out,
            )
            for record in records
            if (
                record.check_in is not None
                and record.check_out is not None
            )
        )

        total_records = len(records)
        total_working_days = total_records

        attendance_percentage = (
            round(
                ((present_days + 0.5 * half_days) / total_working_days) * 100.0,
                2,
            )
            if total_working_days > 0
            else 0.0
        )

        return AttendanceSummary(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            total_records=total_records,
            total_working_days=total_working_days,
            present_days=present_days,
            half_days=half_days,
            in_progress_days=in_progress_days,
            total_working_hours=total_working_hours,
            absent_days=absent_days,
            incomplete_days=incomplete_days,
            attendance_percentage=attendance_percentage,
        )

    def get_daily_attendance_report(
        self,
        active_employees: list[Employee],
        attendance_date: date,
    ) -> DailyAttendanceReport:
        records = self._repository.get_all_by_date(attendance_date)
        attendance_by_employee = {
            record.employee_id: record for record in records
        }

        report_items: list[DailyAttendanceItem] = []

        for employee in active_employees:
            record = attendance_by_employee.get(employee.employee_id)

            if record is None:
                report_items.append(
                    DailyAttendanceItem(
                        employee_id=employee.employee_id,
                        name=employee.name,
                        check_in=None,
                        check_out=None,
                        working_hours=None,
                        status="absent",
                    )
                )
            else:
                working_hours = None
                if record.check_in is not None and record.check_out is not None:
                    try:
                        working_hours = round(
                            self.calculate_working_hours(
                                record.check_in,
                                record.check_out,
                            ),
                            2,
                        )
                    except ValueError:
                        working_hours = None

                report_items.append(
                    DailyAttendanceItem(
                        employee_id=employee.employee_id,
                        name=employee.name,
                        check_in=record.check_in,
                        check_out=record.check_out,
                        working_hours=working_hours,
                        status=record.status,
                    )
                )

        return DailyAttendanceReport(
            attendance_date=attendance_date,
            total_employees=len(report_items),
            records=report_items,
        )