from .settings import db
from sqlalchemy.exc import IntegrityError


def save_and_commit(obj):
    """
    Добавляет obj в сессию и пытается закоммитить.
    При коллизии откатывает транзакцию и возвращает False,
    иначе возвращает True.
    """
    db.session.add(obj)
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
