import argparse
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.logging_config import configure_logging
from app.database.models.user import UserORM
from app.database.session import SessionFactory
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update an operator user in FaceAttend."
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Username (defaults to 'admin')",
    )
    parser.add_argument(
        "--password",
        default="admin123",
        help="Password (must be at least 6 characters, defaults to 'admin123')",
    )
    parser.add_argument(
        "--role",
        choices=["admin", "security"],
        default="admin",
        help="User role (admin or security, defaults to admin)",
    )
    parser.add_argument(
        "--status",
        choices=["active", "inactive"],
        default="active",
        help="User status (active or inactive, defaults to active)",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()
    username = args.username.strip().lower()
    password = args.password

    if len(password) < 6:
        print("\n[ERROR] Password must be at least 6 characters long.\n")
        return

    password_hash = AuthService.hash_password(password)

    with SessionFactory() as session:
        user = session.query(UserORM).filter_by(username=username).first()
        now = datetime.now(timezone.utc)

        if user is not None:
            user.password_hash = password_hash
            user.role = args.role
            user.status = args.status
            user.updated_at = now
            session.commit()
            print("\n======================================")
            print("     USER UPDATED SUCCESSFULLY        ")
            print("======================================")
        else:
            user = UserORM(
                id=str(uuid4()),
                username=username,
                password_hash=password_hash,
                role=args.role,
                status=args.status,
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            session.commit()
            print("\n======================================")
            print("     USER CREATED SUCCESSFULLY        ")
            print("======================================")

        print(f"Username : {user.username}")
        print(f"Role     : {user.role}")
        print(f"Status   : {user.status}")
        print(f"Password : {password}")
        print("======================================\n")


if __name__ == "__main__":
    main()
