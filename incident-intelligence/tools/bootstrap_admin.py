#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass

from sqlalchemy import select

from packages.common.security import hash_password
from packages.domain_models.database import SessionLocal, create_schema
from packages.domain_models.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first local incident-intelligence administrator.")
    parser.add_argument("email")
    args = parser.parse_args()
    password = getpass.getpass("Password (12+ characters): ")
    create_schema()
    with SessionLocal() as session:
        if session.scalar(select(User).where(User.email == args.email.lower())):
            raise SystemExit("A user with that email already exists.")
        user = User(email=args.email.lower(), password_hash=hash_password(password), role_name="admin")
        session.add(user); session.commit()
        print(f"Created admin {user.email} ({user.id})")


if __name__ == "__main__":
    main()

