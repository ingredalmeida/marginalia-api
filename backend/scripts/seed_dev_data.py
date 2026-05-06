"""Populate Postgres with demo admin, patron, authors and books (Docker / local dev).

Idempotent: if the admin e-mail already exists, exits without changes.
Enable with SEED_DEV_DATA=1 (set in docker-compose for the api service).
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models import Author, Book, User

ADMIN_EMAIL = "admin@demo.marginalia.org"
_LEGACY_ADMIN_EMAIL = "admin@marginalia.local"
ADMIN_PASSWORD = "AdminSenha1"
ADMIN_NAME = "Administrador Demo"

PATRON_EMAIL = "patron@demo.marginalia.org"
PATRON_PASSWORD = "PatronoSenha1"
PATRON_NAME = "Patrono Demo"


def _enabled() -> bool:
    v = os.environ.get("SEED_DEV_DATA", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _url() -> str:
    return os.environ.get("DATABASE_URL", settings.database_url)


def seed(session: Session) -> None:
    if session.scalar(
        select(User.id).where(User.email.in_((ADMIN_EMAIL, _LEGACY_ADMIN_EMAIL)))
    ):
        return

    admin = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        hashed_password=hash_password(ADMIN_PASSWORD),
        is_admin=True,
    )
    patron = User(
        name=PATRON_NAME,
        email=PATRON_EMAIL,
        hashed_password=hash_password(PATRON_PASSWORD),
        is_admin=False,
    )
    session.add_all([admin, patron])
    session.flush()

    authors_spec = [
        ("Clarice Lispector", "Escritora brasileira."),
        ("Machado de Assis", "Romancista e cronista."),
        ("Jorge Amado", "Romancista baiano."),
    ]
    authors: dict[str, Author] = {}
    for name, bio in authors_spec:
        a = Author(name=name, bio=bio)
        session.add(a)
        session.flush()
        authors[name] = a

    books_spec: list[tuple[str, str, int | None, str | None, str | None]] = [
        # (title, author_name, year, isbn, description)
        (
            "Dom Casmurro",
            "Machado de Assis",
            1899,
            "9788535909249",
            "Romance em primeira pessoa; narrador Bentinho.",
        ),
        (
            "Dom Casmurro",
            "Machado de Assis",
            1899,
            "9788535909256",
            "Segundo exemplar do acervo de demonstração.",
        ),
        (
            "A hora da estrela",
            "Clarice Lispector",
            1977,
            "9788535902776",
            "Último romance publicado em vida.",
        ),
        (
            "Laços de família",
            "Clarice Lispector",
            1960,
            "9788535901234",
            "Contos.",
        ),
        (
            "Capitães da Areia",
            "Jorge Amado",
            1937,
            "9788535908888",
            "Meninos do trapiche em Salvador.",
        ),
        (
            "Dona Flor e seus dois maridos",
            "Jorge Amado",
            1966,
            "9788535907777",
            "Romance; culinária e humor.",
        ),
    ]

    for title, author_name, year, isbn, desc in books_spec:
        author = authors[author_name]
        session.add(
            Book(
                title=title,
                author_id=author.id,
                publication_year=year,
                isbn=isbn,
                description=desc,
            )
        )

    session.commit()


def main() -> None:
    if not _enabled():
        sys.exit(0)

    engine = create_engine(_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        try:
            seed(session)
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
