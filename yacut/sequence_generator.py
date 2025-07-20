import string
import random
from .settings import db


def get_unique_short_id(k=6):
    """
    Генератор последовательности для короткой ссылки.

    Генерирует случайный идентификатор длины k из [A–Z, a–z, 0–9]
    и гарантирует его уникальность в таблице URLMap.
    """
    from .models import URLMap
    alphabet = string.ascii_letters + string.digits
    while True:
        short_id = ''.join(random.choices(alphabet, k=k))
        exists = db.session.query(
            db.exists().where(URLMap.short == short_id)
        ).scalar()
        if not exists:
            return short_id
