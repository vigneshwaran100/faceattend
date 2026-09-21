import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.attendance import AttendanceORM
from app.infrastructure.database_error import DatabaseError
from app.models.attendance import Attendance

logger = logging.getLogger(__name__)


class AttendanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_employee_and_date(
        self,
        employee_id: str,
        attendance_date: date,
    ) -> Attendance | None:
    
        statement = select(AttendanceORM).where(
            AttendanceORM.employee_id == employee_id,
            AttendanceORM.attendance_date == attendance_date,
        )

        record = self._session.scalar(statement)

        if record is None:
            return None

        return self._to_domain(record)

    def get_all_by_date(
        self,
        attendance_date: date,
    ) -> list[Attendance]:
        statement = select(AttendanceORM).where(
            AttendanceORM.attendance_date == attendance_date,
        )

        records = self._session.scalars(statement).all()

        return [
            self._to_domain(record)
            for record in records
        ]

    def get_all_by_employee(
        self,
        employee_id: str,
    ) -> list[Attendance]:
        statement = (
            select(AttendanceORM)
            .where(AttendanceORM.employee_id == employee_id)
            .order_by(AttendanceORM.attendance_date.desc())
        )

        records = self._session.scalars(statement).all()

        return [
            self._to_domain(record)
            for record in records
        ]

    def create(
        self,
        attendance: Attendance,
    ) -> Attendance:
        try:
            record = AttendanceORM(
                attendance_id=attendance.attendance_id,
                employee_id=attendance.employee_id,
                attendance_date=attendance.attendance_date,
                check_in=attendance.check_in,
                check_out=attendance.check_out,
                status=attendance.status,
                created_at=attendance.created_at,
                updated_at=attendance.updated_at,
            )

            self._session.add(record)
            self._session.commit()
            self._session.refresh(record)

            return self._to_domain(record)

        except IntegrityError as error:
            self._session.rollback()

            is_attendance_date_uq = False
            if hasattr(error, "orig") and error.orig is not None:
                constraint_name = getattr(
                    getattr(error.orig, "diag", None),
                    "constraint_name",
                    None,
                )
                if constraint_name == "uq_attendance_employee_date":
                    is_attendance_date_uq = True

            if not is_attendance_date_uq:
                error_str = str(error).lower()
                if "uq_attendance_employee_date" in error_str or (
                    "employee_id" in error_str
                    and "attendance_date" in error_str
                ):
                    is_attendance_date_uq = True

            if is_attendance_date_uq:
                existing = self.get_by_employee_and_date(
                    attendance.employee_id,
                    attendance.attendance_date,
                )
                if existing is not None:
                    logger.info(
                        "Resolved concurrent attendance insert via unique constraint | employee_id=%s | date=%s",
                        attendance.employee_id,
                        attendance.attendance_date,
                    )
                    return existing

            logger.error(
                "Integrity error creating attendance | employee_id=%s | error=%s",
                attendance.employee_id,
                error,
            )
            raise DatabaseError(
                "Failed to create attendance record due to integrity violation"
            ) from error

        except SQLAlchemyError as error:
            self._session.rollback()

            logger.error(
                "Database error creating attendance | employee_id=%s | error=%s",
                attendance.employee_id,
                error,
            )

            raise DatabaseError(
                "Failed to create attendance record"
            ) from error

    def update(
        self,
        attendance: Attendance,
    ) -> Attendance:
        try:
            statement = select(AttendanceORM).where(
                AttendanceORM.attendance_id
                == attendance.attendance_id
            )

            record = self._session.scalar(statement)

            if record is None:
                raise ValueError(
                    f"Attendance not found: "
                    f"{attendance.attendance_id}"
                )

            record.check_in = attendance.check_in
            record.check_out = attendance.check_out
            record.status = attendance.status
            record.updated_at = attendance.updated_at

            self._session.commit()
            self._session.refresh(record)

            return self._to_domain(record)

        except SQLAlchemyError as error:
            self._session.rollback()

            logger.error(
                "Database error updating attendance | attendance_id=%s | error=%s",
                attendance.attendance_id,
                error,
            )

            raise DatabaseError(
                "Failed to update attendance record"
            ) from error

    @staticmethod
    def _to_domain(
        record: AttendanceORM,
    ) -> Attendance:
        return Attendance(
            attendance_id=record.attendance_id,
            employee_id=record.employee_id,
            attendance_date=record.attendance_date,
            check_in=record.check_in,
            check_out=record.check_out,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


    def get_by_employee_and_date_range(
        self,
        employee_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Attendance]:
        try:
            query = (
                self._session.query(AttendanceORM)
                .filter(AttendanceORM.employee_id == employee_id)
            )

            if start_date is not None:
                query = query.filter(
                    AttendanceORM.attendance_date >= start_date
                )

            if end_date is not None:
                query = query.filter(
                    AttendanceORM.attendance_date <= end_date
                )

            attendance_records = (
                query.order_by(
                    AttendanceORM.attendance_date.desc()
                )
                .all()
            )

            return [
                self._to_domain(record)
                for record in attendance_records
            ]

        except Exception as error:
            logger.error(
                "Failed to retrieve attendance history | "
                "employee_id=%s | error=%s",
                employee_id,
                error,
            )
            raise DatabaseError(
                "Failed to retrieve attendance history"
            ) from error