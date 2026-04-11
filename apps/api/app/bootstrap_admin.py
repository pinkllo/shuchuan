import argparse

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.user import User, UserRole, UserStatus
from app.db.session import SessionLocal

ADMIN_DISPLAY_NAME = "管理员"


def bootstrap_admin(
    session: Session,
    username: str,
    password: str,
    email: str,
) -> User:
    bind = session.get_bind()
    User.__table__.create(bind=bind, checkfirst=True)
    existing_user = session.query(User).filter(User.username == username).one_or_none()
    if existing_user is not None:
        if existing_user.role != UserRole.ADMIN:
            raise SystemExit("同名用户已存在且不是管理员")
        existing_user.display_name = ADMIN_DISPLAY_NAME
        existing_user.password_hash = hash_password(password)
        existing_user.email = email
        existing_user.status = UserStatus.ACTIVE
        session.commit()
        session.refresh(existing_user)
        return existing_user
    admin = User(
        username=username,
        display_name=ADMIN_DISPLAY_NAME,
        password_hash=hash_password(password),
        email=email,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    with SessionLocal() as session:
        admin = bootstrap_admin(session, args.username, args.password, args.email)
    print(f"admin:{admin.username}")


if __name__ == "__main__":
    main()
