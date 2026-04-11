from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.db.models import asset, catalog, demand, log, task, user  # noqa: E402,F401
